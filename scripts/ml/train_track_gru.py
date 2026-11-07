"""Training script for VayumargTrackGRU on historical North Indian Ocean cyclones.

Trains a recurrent deep learning track and intensity model with multi-horizon
heads (+6h, +12h, +24h), evaluated against Geodesic, Stationary, and Wind Persistence baselines.
"""

import hashlib
import json
import sys
import time
from pathlib import Path

# Ensure project root is in python path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from torch.utils.data import DataLoader  # noqa: E402

from vayumarg.ml.track.dataset import (  # noqa: E402
    CycloneTrackDataset,
    dxdy_to_latlon,
    extract_sliding_windows,
    haversine_km,
    load_ibtracs_storms,
    split_storm_disjoint,
)
from vayumarg.ml.track.models import VayumargTrackGRU  # noqa: E402


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def evaluate_model(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> dict:
    """Run full evaluation computing track errors in km and wind errors in kt."""
    model.eval()

    horizons = [6, 12, 24]
    errors_gru = {h: [] for h in horizons}
    errors_geodesic = {h: [] for h in horizons}
    errors_stationary = {h: [] for h in horizons}

    wind_err_gru = {h: [] for h in horizons}
    wind_err_pers = {h: [] for h in horizons}

    with torch.no_grad():
        for batch in loader:
            features = batch["features"].to(device)
            target_wind = batch["target_wind"].cpu().numpy()
            origin_lat = batch["origin_lat"].cpu().numpy()
            origin_lon = batch["origin_lon"].cpu().numpy()
            target_latlon = batch["target_latlon"].cpu().numpy()
            base_geo_disp = batch["baseline_geodesic_disp"].cpu().numpy()
            base_pers_wind = batch["baseline_persistence_wind"].cpu().numpy()

            outputs = model(features)
            pred_disp = outputs["displacement_km"].cpu().numpy()
            pred_wind = outputs["future_wind_kt"].cpu().numpy()

            b_size = features.size(0)
            for b in range(b_size):
                o_lat = float(origin_lat[b])
                o_lon = float(origin_lon[b])

                for h_idx, h in enumerate(horizons):
                    t_lat = float(target_latlon[b, h_idx, 0])
                    t_lon = float(target_latlon[b, h_idx, 1])

                    # 1. GRU predicted position
                    p_dx = float(pred_disp[b, h_idx, 0])
                    p_dy = float(pred_disp[b, h_idx, 1])
                    p_lat, p_lon = dxdy_to_latlon(o_lat, o_lon, p_dx, p_dy)
                    err_gru = haversine_km(p_lat, p_lon, t_lat, t_lon)
                    errors_gru[h].append(err_gru)

                    # 2. Geodesic baseline position
                    g_dx = float(base_geo_disp[b, h_idx, 0])
                    g_dy = float(base_geo_disp[b, h_idx, 1])
                    g_lat, g_lon = dxdy_to_latlon(o_lat, o_lon, g_dx, g_dy)
                    err_geo = haversine_km(g_lat, g_lon, t_lat, t_lon)
                    errors_geodesic[h].append(err_geo)

                    # 3. Stationary baseline position (origin)
                    err_stat = haversine_km(o_lat, o_lon, t_lat, t_lon)
                    errors_stationary[h].append(err_stat)

                    # 4. Wind errors
                    t_w = float(target_wind[b, h_idx])
                    p_w = float(pred_wind[b, h_idx])
                    b_w = float(base_pers_wind[b, h_idx])
                    wind_err_gru[h].append(abs(p_w - t_w))
                    wind_err_pers[h].append(abs(b_w - t_w))

    summary = {
        "horizons": horizons,
        "mean_track_error_km_gru": {f"+{h}h": float(np.mean(errors_gru[h])) for h in horizons},
        "median_track_error_km_gru": {f"+{h}h": float(np.median(errors_gru[h])) for h in horizons},
        "mean_track_error_km_geodesic": {
            f"+{h}h": float(np.mean(errors_geodesic[h])) for h in horizons
        },
        "mean_track_error_km_stationary": {
            f"+{h}h": float(np.mean(errors_stationary[h])) for h in horizons
        },
        "wind_mae_kt_gru": {f"+{h}h": float(np.mean(wind_err_gru[h])) for h in horizons},
        "wind_mae_kt_persistence": {f"+{h}h": float(np.mean(wind_err_pers[h])) for h in horizons},
        "track_skill_score_vs_geodesic": {
            f"+{h}h": float(1.0 - (np.mean(errors_gru[h]) / np.mean(errors_geodesic[h])))
            for h in horizons
        },
        "track_skill_score_vs_stationary": {
            f"+{h}h": float(1.0 - (np.mean(errors_gru[h]) / np.mean(errors_stationary[h])))
            for h in horizons
        },
        "wind_skill_score_vs_persistence": {
            f"+{h}h": float(1.0 - (np.mean(wind_err_gru[h]) / np.mean(wind_err_pers[h])))
            for h in horizons
        },
    }
    return summary


def train():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"[PREFLIGHT] Training on device: {device}")
    if torch.cuda.is_available():
        print(f"[PREFLIGHT] GPU: {torch.cuda.get_device_name(0)}")

    csv_path = Path("data/raw/ibtracs_ni_v04r01.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing IBTrACS dataset at {csv_path}")

    print("[DATA] Loading historical storms from IBTrACS North Indian Ocean archive...")
    storms = load_ibtracs_storms(csv_path, min_year=1980)
    print(f"[DATA] Loaded {len(storms)} historical storms (1980-2024).")

    train_storms, val_storms, test_storms = split_storm_disjoint(storms, seed=42)
    print(
        f"[DATA] Storm-disjoint split: Train={len(train_storms)}, "
        f"Val={len(val_storms)}, Test={len(test_storms)}"
    )

    print("[DATA] Generating 3-hourly sliding sequence windows (T=8 in, +6h/+12h/+24h out)...")
    train_samples = extract_sliding_windows(train_storms)
    val_samples = extract_sliding_windows(val_storms)
    test_samples = extract_sliding_windows(test_storms)
    print(
        f"[DATA] Sample counts: Train={len(train_samples)}, "
        f"Val={len(val_samples)}, Test={len(test_samples)}"
    )

    train_loader = DataLoader(
        CycloneTrackDataset(train_samples),
        batch_size=64,
        shuffle=True,
        drop_last=True,
    )
    val_loader = DataLoader(
        CycloneTrackDataset(val_samples),
        batch_size=64,
        shuffle=False,
    )
    test_loader = DataLoader(
        CycloneTrackDataset(test_samples),
        batch_size=64,
        shuffle=False,
    )

    model = VayumargTrackGRU(
        in_features=10,
        hidden_size=96,
        num_layers=2,
        dropout=0.15,
        horizons=(6, 12, 24),
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[MODEL] VayumargTrackGRU instantiated with {total_params:,} trainable parameters.")

    criterion_disp = nn.SmoothL1Loss(beta=5.0)
    criterion_wind = nn.SmoothL1Loss(beta=2.0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=25, eta_min=1e-5)

    num_epochs = 25
    best_val_loss = float("inf")
    output_dir = Path("models/vayumarg")
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "track_gru_best.pt"

    history = []
    start_time = time.time()

    print("\n--- BEGIN TRACK GRU TRAINING ---")
    for epoch in range(1, num_epochs + 1):
        model.train()
        train_loss = 0.0
        train_batches = 0

        for batch in train_loader:
            features = batch["features"].to(device)
            target_disp = batch["target_disp"].to(device)
            target_wind = batch["target_wind"].to(device)

            optimizer.zero_grad()
            outputs = model(features)

            loss_disp = criterion_disp(outputs["displacement_km"], target_disp)
            loss_wind = criterion_wind(outputs["future_wind_kt"], target_wind)
            total_loss = loss_disp + 0.1 * loss_wind

            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            train_loss += total_loss.item()
            train_batches += 1

        avg_train_loss = train_loss / max(1, train_batches)
        scheduler.step()

        # Validation pass
        model.eval()
        val_loss = 0.0
        val_batches = 0
        with torch.no_grad():
            for batch in val_loader:
                features = batch["features"].to(device)
                target_disp = batch["target_disp"].to(device)
                target_wind = batch["target_wind"].to(device)

                outputs = model(features)
                loss_disp = criterion_disp(outputs["displacement_km"], target_disp)
                loss_wind = criterion_wind(outputs["future_wind_kt"], target_wind)
                v_loss = loss_disp + 0.1 * loss_wind

                val_loss += v_loss.item()
                val_batches += 1

        avg_val_loss = val_loss / max(1, val_batches)
        history.append(
            {
                "epoch": epoch,
                "train_loss": round(avg_train_loss, 4),
                "val_loss": round(avg_val_loss, 4),
                "lr": round(scheduler.get_last_lr()[0], 6),
            }
        )

        is_best = avg_val_loss < best_val_loss
        if is_best:
            best_val_loss = avg_val_loss
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_loss": avg_val_loss,
                    "architecture": "VayumargTrackGRU",
                    "in_features": 10,
                    "hidden_size": 96,
                    "num_layers": 2,
                    "horizons": [6, 12, 24],
                },
                checkpoint_path,
            )

        print(
            f"Epoch [{epoch:02d}/{num_epochs:02d}] "
            f"Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} "
            f"{'(* BEST SAVED)' if is_best else ''}"
        )

    elapsed = time.time() - start_time
    print(
        f"\n[COMPLETE] Training completed in {elapsed:.1f}s. Evaluating best model on held-out test storms..."
    )

    # Load best checkpoint for test evaluation
    best_ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(best_ckpt["model_state_dict"])

    test_eval = evaluate_model(model, test_loader, device)
    sha256_hash = compute_sha256(checkpoint_path)

    final_results = {
        "model_id": "vayumarg-track-gru-v1",
        "checkpoint_path": str(checkpoint_path),
        "sha256": sha256_hash,
        "parameters": total_params,
        "epochs_trained": num_epochs,
        "best_epoch": best_ckpt["epoch"],
        "best_val_loss": round(best_ckpt["val_loss"], 4),
        "training_time_seconds": round(elapsed, 1),
        "dataset": {
            "source": "IBTrACS v04r01 North Indian Ocean (1980-2024)",
            "train_samples": len(train_samples),
            "val_samples": len(val_samples),
            "test_samples": len(test_samples),
            "train_storms": len(train_storms),
            "val_storms": len(val_storms),
            "test_storms": len(test_storms),
        },
        "test_evaluation": test_eval,
        "history": history,
    }

    metrics_path = output_dir / "track_gru_evaluation_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2)

    print("\n================ TEST BENCHMARK RESULTS ================")
    print(f"Checkpoint SHA-256: {sha256_hash}")
    for h in [6, 12, 24]:
        k = f"+{h}h"
        print(
            f"Horizon {k}: GRU Track Error = {test_eval['mean_track_error_km_gru'][k]:.1f} km "
            f"| Geodesic = {test_eval['mean_track_error_km_geodesic'][k]:.1f} km "
            f"| Stationary = {test_eval['mean_track_error_km_stationary'][k]:.1f} km "
            f"| Skill vs Geodesic = {test_eval['track_skill_score_vs_geodesic'][k] * 100:.1f}%"
        )
        print(
            f"            GRU Wind MAE = {test_eval['wind_mae_kt_gru'][k]:.2f} kt "
            f"| Persistence = {test_eval['wind_mae_kt_persistence'][k]:.2f} kt "
            f"| Skill vs Persistence = {test_eval['wind_skill_score_vs_persistence'][k] * 100:.1f}%"
        )
    print("========================================================\n")


if __name__ == "__main__":
    train()
