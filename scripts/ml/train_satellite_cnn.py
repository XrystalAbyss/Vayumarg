"""Training Pipeline for Satellite Infrared CNN Intensity Regressor.

Trains a ResNet-18 single-channel infrared model on the authentic NASA Tropical Cyclone
Wind benchmark dataset with storm-disjoint splits, evaluating real MAE and RMSE metrics
and producing the production checkpoint in models/vayumarg/vision/.
"""

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.amp import GradScaler, autocast
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from vayumarg.ml.vision.dataset import CycloneImageDataset  # noqa: E402
from vayumarg.ml.vision.models import CycloneCNNRegressor  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_cnn")

# Paths
DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_PATH = DATA_DIR / "processed" / "satellite" / "nasa_cyclone" / "dataset_manifest.json"
MODELS_DIR = PROJECT_ROOT / "models" / "vayumarg" / "vision"
REPORTS_DIR = PROJECT_ROOT / "reports" / "ml"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_split(model: nn.Module, loader: DataLoader, device: torch.device) -> dict:
    """Evaluate model on a dataset split, returning MAE, RMSE, and correlation."""
    model.eval()
    all_preds = []
    all_targets = []
    all_cats_pred = []
    all_cats_true = []

    with torch.no_grad():
        for batch in loader:
            imgs = batch["image"].to(device, non_blocking=True)
            targets = batch["wind_speed"].to(device, non_blocking=True)
            cats = batch["category"].to(device, non_blocking=True)

            with autocast(device_type=device.type):
                preds, cat_logits = model(imgs)

            preds = preds.squeeze(-1)
            all_preds.extend(preds.cpu().numpy().tolist())
            all_targets.extend(targets.cpu().numpy().tolist())
            all_cats_pred.extend(cat_logits.argmax(dim=-1).cpu().numpy().tolist())
            all_cats_true.extend(cats.cpu().numpy().tolist())

    preds_arr = np.array(all_preds)
    targets_arr = np.array(all_targets)

    mae = float(np.mean(np.abs(preds_arr - targets_arr)))
    rmse = float(np.sqrt(np.mean((preds_arr - targets_arr) ** 2)))
    mape = float(np.mean(np.abs(preds_arr - targets_arr) / np.maximum(targets_arr, 1.0)) * 100.0)

    # Pearson correlation
    if np.std(preds_arr) > 1e-6 and np.std(targets_arr) > 1e-6:
        r = float(np.corrcoef(preds_arr, targets_arr)[0, 1])
    else:
        r = 0.0

    # Category Accuracy
    cats_pred_arr = np.array(all_cats_pred)
    cats_true_arr = np.array(all_cats_true)
    cat_acc = float(np.mean(cats_pred_arr == cats_true_arr) * 100.0)

    return {
        "mae_knots": round(mae, 2),
        "rmse_knots": round(rmse, 2),
        "mape_percent": round(mape, 2),
        "pearson_r": round(r, 4),
        "category_accuracy_percent": round(cat_acc, 2),
        "sample_count": len(preds_arr),
    }


def main():
    logger.info("================================================================================")
    logger.info("VAYUMARG SATELLITE CNN INTENSITY REGRESSION TRAINING")
    logger.info("================================================================================")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(
        "Target execution device: %s (%s)",
        device,
        torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Host CPU",
    )

    if not MANIFEST_PATH.is_file():
        logger.error(
            "Dataset manifest not found at %s. Please run acquire_nasa_cyclone_data.py first.",
            MANIFEST_PATH,
        )
        sys.exit(1)

    # 1. Datasets & DataLoaders
    batch_size = 32
    num_workers = 2 if sys.platform != "win32" else 0
    image_size = 128

    logger.info("Loading storm-disjoint splits from %s...", MANIFEST_PATH)
    train_dataset = CycloneImageDataset(
        MANIFEST_PATH, split="train", image_size=image_size, augment=True
    )
    val_dataset = CycloneImageDataset(
        MANIFEST_PATH, split="val", image_size=image_size, augment=False
    )
    test_dataset = CycloneImageDataset(
        MANIFEST_PATH, split="test", image_size=image_size, augment=False
    )

    logger.info(
        "Splits loaded: Train = %d frames, Val = %d frames, Test = %d frames",
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

    # 2. Model, Loss, Optimizer
    model = CycloneCNNRegressor(pretrained_backbone=True, dropout=0.25).to(device)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("Model instantiated: ResNet-18 IR (Trainable parameters: %s)", f"{total_params:,}")

    regression_criterion = nn.SmoothL1Loss(beta=2.0)  # Huber Loss for robust intensity regression
    classification_criterion = nn.CrossEntropyLoss()

    epochs = 15
    lr = 5e-4
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    scaler = GradScaler(device=device.type)

    best_val_mae = float("inf")
    best_checkpoint_path = MODELS_DIR / "satellite_cnn_best.pt"
    history = []

    logger.info("Starting training loop across %d epochs...", epochs)
    t_start = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        running_reg_loss = 0.0
        running_cls_loss = 0.0

        for batch in train_loader:
            imgs = batch["image"].to(device, non_blocking=True)
            targets = batch["wind_speed"].to(device, non_blocking=True)
            cats = batch["category"].to(device, non_blocking=True)

            optimizer.zero_grad()

            with autocast(device_type=device.type):
                preds, cat_logits = model(imgs)
                preds = preds.squeeze(-1)

                loss_reg = regression_criterion(preds, targets)
                loss_cls = classification_criterion(cat_logits, cats)
                total_loss = loss_reg + 0.1 * loss_cls

            scaler.scale(total_loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += total_loss.item() * len(targets)
            running_reg_loss += loss_reg.item() * len(targets)
            running_cls_loss += loss_cls.item() * len(targets)

        scheduler.step()

        epoch_loss = running_loss / len(train_dataset)
        epoch_reg_loss = running_reg_loss / len(train_dataset)
        cur_lr = scheduler.get_last_lr()[0]

        # Validation evaluation
        val_metrics = evaluate_split(model, val_loader, device)

        logger.info(
            "Epoch [%02d/%02d] | Train Loss: %.3f (Reg: %.3f) | Val MAE: %.2f kt | Val RMSE: %.2f kt | r: %.4f | LR: %.2e",
            epoch,
            epochs,
            epoch_loss,
            epoch_reg_loss,
            val_metrics["mae_knots"],
            val_metrics["rmse_knots"],
            val_metrics["pearson_r"],
            cur_lr,
        )

        history.append(
            {
                "epoch": epoch,
                "train_loss": round(epoch_loss, 4),
                "train_reg_loss": round(epoch_reg_loss, 4),
                "val_mae": val_metrics["mae_knots"],
                "val_rmse": val_metrics["rmse_knots"],
                "val_r": val_metrics["pearson_r"],
                "val_cat_acc": val_metrics["category_accuracy_percent"],
                "learning_rate": cur_lr,
            }
        )

        # Checkpoint if best validation MAE
        if val_metrics["mae_knots"] < best_val_mae:
            best_val_mae = val_metrics["mae_knots"]
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_metrics": val_metrics,
                    "model_architecture": "ResNet18-IR-SingleChannel",
                    "training_timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
                },
                best_checkpoint_path,
            )
            logger.info(
                "  --> Saved new best checkpoint (Val MAE: %.2f kt) to %s",
                best_val_mae,
                best_checkpoint_path.name,
            )

    total_training_time = time.time() - t_start
    logger.info(
        "Training complete in %.2f seconds (%.2f min).",
        total_training_time,
        total_training_time / 60.0,
    )

    # 3. Final Evaluation on Held-Out Test Set (Disjoint Storms)
    logger.info("Loading best checkpoint for final held-out test evaluation...")
    checkpoint = torch.load(best_checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])

    test_metrics = evaluate_split(model, test_loader, device)
    train_eval_metrics = evaluate_split(model, train_loader, device)

    logger.info("================================================================================")
    logger.info("FINAL DISJOINT EVALUATION RESULTS")
    logger.info("================================================================================")
    logger.info(
        "Train Set (%d frames): MAE = %.2f kt, RMSE = %.2f kt, r = %.4f",
        train_eval_metrics["sample_count"],
        train_eval_metrics["mae_knots"],
        train_eval_metrics["rmse_knots"],
        train_eval_metrics["pearson_r"],
    )
    logger.info(
        "Val Set   (%d frames): MAE = %.2f kt, RMSE = %.2f kt, r = %.4f",
        checkpoint["val_metrics"]["sample_count"],
        checkpoint["val_metrics"]["mae_knots"],
        checkpoint["val_metrics"]["rmse_knots"],
        checkpoint["val_metrics"]["pearson_r"],
    )
    logger.info(
        "Test Set  (%d frames): MAE = %.2f kt, RMSE = %.2f kt, r = %.4f",
        test_metrics["sample_count"],
        test_metrics["mae_knots"],
        test_metrics["rmse_knots"],
        test_metrics["pearson_r"],
    )
    logger.info(
        "Test Category Classification Accuracy: %.2f%%", test_metrics["category_accuracy_percent"]
    )

    # 4. Save Final Evaluation Ledger
    eval_summary = {
        "model_name": "Vayumarg-CNN-ResNet18-IR",
        "training_dataset": "NASA Tropical Cyclone Wind Estimation Benchmark Subset",
        "source_agency": "NASA IMPACT / NOAA GOES IR (11 µm)",
        "unique_training_storms": 15,
        "unique_validation_storms": 5,
        "unique_test_storms": 5,
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
        "test_samples": len(test_dataset),
        "epochs_trained": epochs,
        "training_time_seconds": round(total_training_time, 2),
        "hardware_device": str(device),
        "metrics": {
            "train": train_eval_metrics,
            "val": checkpoint["val_metrics"],
            "test": test_metrics,
        },
        "history": history,
    }

    eval_json_path = MODELS_DIR / "cnn_evaluation_metrics.json"
    eval_json_path.write_text(json.dumps(eval_summary, indent=2))
    logger.info("Evaluation metrics ledger written to %s", eval_json_path)


if __name__ == "__main__":
    main()
