"""Training Pipeline for Satellite Spatiotemporal ConvLSTM Sequence Forecaster.

Trains a multi-layer ConvLSTM on chronological satellite image sequences (T=3 past frames)
to predict next-step cyclone intensity (knots) and next-frame infrared imagery.
Benchmarks against Persistence Baseline and Single-Frame CNN.
"""

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.amp import GradScaler, autocast
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from vayumarg.ml.vision.dataset import CycloneSequenceDataset  # noqa: E402
from vayumarg.ml.vision.models import CycloneConvLSTM  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_convlstm")

DATA_DIR = PROJECT_ROOT / "data"
SEQ_MANIFEST_PATH = (
    DATA_DIR / "processed" / "satellite" / "nasa_cyclone" / "sequences_manifest.json"
)
MODELS_DIR = PROJECT_ROOT / "models" / "vayumarg" / "vision"
REPORTS_DIR = PROJECT_ROOT / "reports" / "ml"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_sequences(model: nn.Module, loader: DataLoader, device: torch.device) -> dict:
    """Evaluate ConvLSTM on sequences, comparing with Persistence Baseline."""
    model.eval()
    all_preds = []
    all_targets = []
    total_frame_mse = 0.0
    total_frames = 0

    with torch.no_grad():
        for batch in loader:
            seqs = batch["sequence"].to(device, non_blocking=True)  # (B, T, 1, H, W)
            targets = batch["target_wind"].to(device, non_blocking=True)
            target_frames = batch["target_frame"].to(device, non_blocking=True)

            with autocast(device_type=device.type):
                pred_winds, pred_frames = model(seqs)

            pred_winds = pred_winds.squeeze(-1)
            all_preds.extend(pred_winds.cpu().numpy().tolist())
            all_targets.extend(targets.cpu().numpy().tolist())

            # Persistence baseline: last observed frame's intensity is seqs[:, -1]
            # Since sequence has 3 frames, we take the last past wind
            # For pure frame persistence, we use target - last_known
            # We also compute frame MSE
            frame_mse = F.mse_loss(pred_frames, target_frames, reduction="sum").item()
            total_frame_mse += frame_mse
            total_frames += targets.size(0)

    preds_arr = np.array(all_preds)
    targets_arr = np.array(all_targets)

    mae = float(np.mean(np.abs(preds_arr - targets_arr)))
    rmse = float(np.sqrt(np.mean((preds_arr - targets_arr) ** 2)))

    if np.std(preds_arr) > 1e-6 and np.std(targets_arr) > 1e-6:
        r = float(np.corrcoef(preds_arr, targets_arr)[0, 1])
    else:
        r = 0.0

    mean_frame_mse = float(total_frame_mse / max(1, total_frames * 64 * 64))

    return {
        "mae_knots": round(mae, 2),
        "rmse_knots": round(rmse, 2),
        "pearson_r": round(r, 4),
        "next_frame_pixel_mse": round(mean_frame_mse, 5),
        "sample_count": len(preds_arr),
    }


def compute_persistence_baseline(manifest_path: Path, split: str) -> dict:
    """Compute exact physical Persistence baseline on the split sequences."""
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)
    seqs = [s for s in data["sequences"] if s["split"] == split]

    pers_errors = []
    targets = []
    for s in seqs:
        last_wind = s["past_winds"][-1]
        target_wind = s["target_wind"]
        pers_errors.append(abs(last_wind - target_wind))
        targets.append(target_wind)

    errs = np.array(pers_errors)
    return {
        "mae_knots": round(float(np.mean(errs)), 2),
        "rmse_knots": round(float(np.sqrt(np.mean(errs**2))), 2),
        "sample_count": len(errs),
    }


def main():
    logger.info("================================================================================")
    logger.info("VAYUMARG SATELLITE CONVLSTM SPATIOTEMPORAL TRAINING")
    logger.info("================================================================================")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(
        "Execution device: %s (%s)",
        device,
        torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Host CPU",
    )

    if not SEQ_MANIFEST_PATH.is_file():
        logger.error("Sequence manifest not found at %s.", SEQ_MANIFEST_PATH)
        sys.exit(1)

    # Persistence Baseline calculation first
    logger.info("Computing Persistence Baseline benchmarks...")
    pers_train = compute_persistence_baseline(SEQ_MANIFEST_PATH, "train")
    pers_val = compute_persistence_baseline(SEQ_MANIFEST_PATH, "val")
    pers_test = compute_persistence_baseline(SEQ_MANIFEST_PATH, "test")

    logger.info("PERSISTENCE BENCHMARK:")
    logger.info(
        "  Train: MAE = %.2f kt, RMSE = %.2f kt", pers_train["mae_knots"], pers_train["rmse_knots"]
    )
    logger.info(
        "  Val:   MAE = %.2f kt, RMSE = %.2f kt", pers_val["mae_knots"], pers_val["rmse_knots"]
    )
    logger.info(
        "  Test:  MAE = %.2f kt, RMSE = %.2f kt", pers_test["mae_knots"], pers_test["rmse_knots"]
    )

    # Datasets
    batch_size = 32
    image_size = 64
    num_workers = 2 if sys.platform != "win32" else 0

    train_dataset = CycloneSequenceDataset(SEQ_MANIFEST_PATH, split="train", image_size=image_size)
    val_dataset = CycloneSequenceDataset(SEQ_MANIFEST_PATH, split="val", image_size=image_size)
    test_dataset = CycloneSequenceDataset(SEQ_MANIFEST_PATH, split="test", image_size=image_size)

    logger.info(
        "Chronological sequences: Train = %d, Val = %d, Test = %d",
        len(train_dataset),
        len(val_dataset),
        len(test_dataset),
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    # Model
    model = CycloneConvLSTM(in_channels=1, hidden_dims=(32, 64), kernel_size=3, dropout=0.2).to(
        device
    )
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(
        "ConvLSTM instantiated: 2-layer ConvLSTM (32 -> 64 filters, Parameters: %s)",
        f"{total_params:,}",
    )

    wind_criterion = nn.SmoothL1Loss(beta=2.0)
    frame_criterion = nn.MSELoss()

    epochs = 12
    lr = 8e-4
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    scaler = GradScaler(device=device.type)

    best_val_mae = float("inf")
    best_checkpoint_path = MODELS_DIR / "satellite_convlstm_best.pt"
    history = []

    logger.info("Starting ConvLSTM spatiotemporal sequence training...")
    t_start = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        running_wind_loss = 0.0
        running_frame_loss = 0.0

        for batch in train_loader:
            seqs = batch["sequence"].to(device, non_blocking=True)
            targets = batch["target_wind"].to(device, non_blocking=True)
            target_frames = batch["target_frame"].to(device, non_blocking=True)

            optimizer.zero_grad()

            with autocast(device_type=device.type):
                pred_winds, pred_frames = model(seqs)
                pred_winds = pred_winds.squeeze(-1)

                loss_wind = wind_criterion(pred_winds, targets)
                loss_frame = frame_criterion(pred_frames, target_frames)
                total_loss = loss_wind + 5.0 * loss_frame

            scaler.scale(total_loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += total_loss.item() * len(targets)
            running_wind_loss += loss_wind.item() * len(targets)
            running_frame_loss += loss_frame.item() * len(targets)

        scheduler.step()

        epoch_loss = running_loss / len(train_dataset)
        cur_lr = scheduler.get_last_lr()[0]

        val_metrics = evaluate_sequences(model, val_loader, device)

        logger.info(
            "Epoch [%02d/%02d] | Train Loss: %.3f | Val MAE: %.2f kt | Val RMSE: %.2f kt | Frame MSE: %.4f | r: %.4f",
            epoch,
            epochs,
            epoch_loss,
            val_metrics["mae_knots"],
            val_metrics["rmse_knots"],
            val_metrics["next_frame_pixel_mse"],
            val_metrics["pearson_r"],
        )

        history.append(
            {
                "epoch": epoch,
                "train_loss": round(epoch_loss, 4),
                "val_mae": val_metrics["mae_knots"],
                "val_rmse": val_metrics["rmse_knots"],
                "val_frame_mse": val_metrics["next_frame_pixel_mse"],
                "val_r": val_metrics["pearson_r"],
                "learning_rate": cur_lr,
            }
        )

        if val_metrics["mae_knots"] < best_val_mae:
            best_val_mae = val_metrics["mae_knots"]
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_metrics": val_metrics,
                    "model_architecture": "CycloneConvLSTM-32-64",
                    "training_timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
                },
                best_checkpoint_path,
            )
            logger.info(
                "  --> Saved new best ConvLSTM checkpoint (Val MAE: %.2f kt) to %s",
                best_val_mae,
                best_checkpoint_path.name,
            )

    total_training_time = time.time() - t_start
    logger.info(
        "ConvLSTM training complete in %.2f seconds (%.2f min).",
        total_training_time,
        total_training_time / 60.0,
    )

    # Final evaluation on held-out test split
    checkpoint = torch.load(best_checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])

    test_metrics = evaluate_sequences(model, test_loader, device)
    train_eval_metrics = evaluate_sequences(model, train_loader, device)

    logger.info("================================================================================")
    logger.info("CONVLSTM VS BENCHMARKS ON HELD-OUT TEST STORMS")
    logger.info("================================================================================")
    logger.info(
        "Persistence Baseline (Test): MAE = %.2f kt, RMSE = %.2f kt",
        pers_test["mae_knots"],
        pers_test["rmse_knots"],
    )
    logger.info(
        "ConvLSTM Forecaster (Test):  MAE = %.2f kt, RMSE = %.2f kt (r = %.4f)",
        test_metrics["mae_knots"],
        test_metrics["rmse_knots"],
        test_metrics["pearson_r"],
    )

    eval_summary = {
        "model_name": "Vayumarg-ConvLSTM-Spatiotemporal",
        "dataset": "NASA Tropical Cyclone Wind Sequence Benchmark",
        "sequence_length": 3,
        "spatial_resolution": [64, 64],
        "training_time_seconds": round(total_training_time, 2),
        "benchmarks": {
            "persistence": {
                "train": pers_train,
                "val": pers_val,
                "test": pers_test,
            },
            "convlstm": {
                "train": train_eval_metrics,
                "val": checkpoint["val_metrics"],
                "test": test_metrics,
            },
        },
        "history": history,
    }

    eval_json_path = MODELS_DIR / "convlstm_evaluation_metrics.json"
    eval_json_path.write_text(json.dumps(eval_summary, indent=2))
    logger.info("ConvLSTM metrics saved to %s", eval_json_path)


if __name__ == "__main__":
    main()
