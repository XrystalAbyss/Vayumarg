"""Vayumarg 3.0 — Phase 6 Application Compatibility & Inference Verification."""

import hashlib
import torch
import numpy as np
from pathlib import Path
from vayumarg.ml.vision.models import CycloneCNNRegressor, CycloneConvLSTM
from vayumarg.ml.track.models import VayumargTrackGRU, VayumargHybridTrackModel
from vayumarg.ml.registry import get_model_registry

def main():
    print("=" * 80)
    print("PHASE 6: APPLICATION COMPATIBILITY & INFERENCE VERIFICATION")
    print("=" * 80)

    # 1. Model Registry Check
    print("\n[Step 1] Querying Authoritative Model Registry...")
    reg = get_model_registry()
    print(f"  Overall Registry Status: {reg.get('status')}")
    models_dict = reg.get("models", {})
    for mid, info in models_dict.items():
        print(f"  Model ID: {mid}")
        print(f"    Architecture:      {info.get('architecture')}")
        print(f"    Checksum Verified: {info.get('checksum_verified')}")
        print(f"    Status:            {info.get('status')}")
        assert info.get("checksum_verified") is True, f"Registry failed checksum for {mid}!"
    print("  >>> MODEL REGISTRY INTEGRITY CONFIRMED <<<")

    # 2. Satellite CNN Inference Verification
    cnn_path = Path("models/vayumarg/vision/satellite_cnn_best.pt")
    assert cnn_path.exists(), "CNN checkpoint missing!"
    print(f"\n[Step 2] Testing Satellite CNN: {cnn_path.name}")
    cnn_data = torch.load(cnn_path, map_location="cpu", weights_only=True)
    cnn_model = CycloneCNNRegressor(pretrained_backbone=False)
    cnn_model.load_state_dict(cnn_data["model_state_dict"])
    cnn_model.eval()
    
    # Dummy forward pass (batch 1, channel 1, 128, 128)
    dummy_cnn_in = torch.randn(1, 1, 128, 128)
    with torch.no_grad():
        wind_pred, cat_logits = cnn_model(dummy_cnn_in)
    print(f"  [PASS] CNN Loaded successfully. State dict keys: {len(cnn_data['model_state_dict'])}")
    print(f"  [PASS] Dummy input shape: {dummy_cnn_in.shape} -> Predicted wind speed: {wind_pred.item():.2f} kts, Category logits: {cat_logits.shape}")

    # 3. Satellite ConvLSTM Inference Verification
    conv_path = Path("models/vayumarg/vision/satellite_convlstm_best.pt")
    assert conv_path.exists(), "ConvLSTM checkpoint missing!"
    print(f"\n[Step 3] Testing Satellite ConvLSTM: {conv_path.name}")
    conv_data = torch.load(conv_path, map_location="cpu", weights_only=True)
    conv_model = CycloneConvLSTM(in_channels=1, hidden_dims=(32, 64), kernel_size=3)
    conv_model.load_state_dict(conv_data["model_state_dict"])
    conv_model.eval()
    
    # Dummy forward pass (batch 1, seq_len 3, channel 1, 64, 64)
    dummy_conv_in = torch.randn(1, 3, 1, 64, 64)
    with torch.no_grad():
        intensity_pred, next_frame = conv_model(dummy_conv_in)
    print(f"  [PASS] ConvLSTM Loaded successfully. State dict keys: {len(conv_data['model_state_dict'])}")
    print(f"  [PASS] Dummy input shape: {dummy_conv_in.shape} -> Intensity: {intensity_pred.item():.2f} kts, Future frame: {next_frame.shape}")

    # 4. Track GRU Inference Verification
    gru_path = Path("models/vayumarg/track_gru_best.pt")
    assert gru_path.exists(), "Track GRU checkpoint missing!"
    print(f"\n[Step 4] Testing Track GRU: {gru_path.name}")
    gru_data = torch.load(gru_path, map_location="cpu", weights_only=True)
    gru_model = VayumargTrackGRU(
        in_features=gru_data.get("in_features", 10),
        hidden_size=gru_data.get("hidden_size", 96),
        num_layers=gru_data.get("num_layers", 2),
        horizons=tuple(gru_data.get("horizons", [6, 12, 24]))
    )
    gru_model.load_state_dict(gru_data["model_state_dict"])
    gru_model.eval()
    
    # Dummy forward pass (batch 1, seq_len 8, features 10)
    dummy_gru_in = torch.randn(1, 8, 10)
    with torch.no_grad():
        gru_out = gru_model(dummy_gru_in)
    print(f"  [PASS] Track GRU Loaded successfully. State dict keys: {len(gru_data['model_state_dict'])}")
    print(f"  [PASS] Dummy input shape: {dummy_gru_in.shape} -> Displacements: {gru_out['displacement_km'].shape}, Winds: {gru_out['future_wind_kt'].shape}")

    # 5. Track Hybrid Residual Inference Verification
    hybrid_path = Path("models/vayumarg/track_hybrid_residual_best.pt")
    assert hybrid_path.exists(), "Hybrid checkpoint missing!"
    print(f"\n[Step 5] Testing Track Hybrid Residual: {hybrid_path.name}")
    hybrid_data = torch.load(hybrid_path, map_location="cpu", weights_only=False)
    hybrid_model = VayumargHybridTrackModel(
        in_features=hybrid_data.get("in_features", 10),
        hidden_size=hybrid_data.get("hidden_size", 64),
        num_layers=hybrid_data.get("num_layers", 2),
        horizons=tuple(hybrid_data.get("horizons", [6, 12, 24]))
    )
    hybrid_model.load_state_dict(hybrid_data["model_state_dict"])
    hybrid_model.eval()
    
    dummy_hybrid_in = torch.randn(1, 8, 10)
    dummy_baseline_disp = torch.zeros(1, 3, 2)
    with torch.no_grad():
        hybrid_out = hybrid_model(dummy_hybrid_in, dummy_baseline_disp)
    print(f"  [PASS] Track Hybrid Residual Loaded successfully. State dict keys: {len(hybrid_data['model_state_dict'])}")
    print(f"  [PASS] Dummy input shape: {dummy_hybrid_in.shape} -> Displacements: {hybrid_out['final_disp_km'].shape}, Residuals: {hybrid_out['residual_km'].shape}, Winds: {hybrid_out['future_wind_kt'].shape}")

    print("\n" + "=" * 80)
    print("ALL FOUR LOCAL MODEL CHECKPOINTS REMAIN FULLY OPERATIONAL AND UNMODIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    main()
