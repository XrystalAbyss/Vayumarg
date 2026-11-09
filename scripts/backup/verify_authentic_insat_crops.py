"""Authentic INSAT Satellite Crops Scientific Verification Suite.

Performs deep audit of the 4 authentic ISRO MOSDAC INSAT crops:
- AMPHAN (2020-05-19 23:58 UTC, INSAT-3DR)
- BIPARJOY (2023-06-12 23:58 UTC, INSAT-3DR)
- REMAL (2024-05-26 18:02 UTC, INSAT-3DR)
- DANA (2024-10-25 23:30 UTC, INSAT-3DS)
"""

import h5py
import json
from pathlib import Path

from vayumarg.satellite.preview import compute_physical_crop_metrics, render_crop_png

CROPS_DIR = Path("data/processed/satellite/crops")
LEDGER_PATH = Path("reports/F2_4_GATE_C1R_SCIENTIFIC_LEDGER.json")


def test_insat_crops():
    print("=" * 75)
    print("VAYUMARG 3.0 AUTHENTIC INSAT SATELLITE CROPS AUDIT")
    print("=" * 75)

    crops = [
        ("AMPHAN", "AMPHAN_20200519_2358_MULTICHANNEL.h5", "INSAT-3DR", "2020136N10088"),
        ("BIPARJOY", "BIPARJOY_20230612_2358_MULTICHANNEL.h5", "INSAT-3DR", "2023156N10067"),
        ("REMAL", "REMAL_20240526_1802_MULTICHANNEL.h5", "INSAT-3DR", "2024145N14087"),
        ("DANA", "DANA_20241025_2330_MULTICHANNEL.h5", "INSAT-3DS", "2024295N15092"),
    ]

    results = {}

    for name, fname, sat, sid in crops:
        cpath = CROPS_DIR / fname
        assert cpath.is_file(), f"Missing crop: {cpath}"
        print(f"\n--- Storm: {name} ({fname}) ---")
        print(f"    Satellite: {sat} | Canonical SID: {sid}")
        print(f"    File Size: {cpath.stat().st_size:,} bytes")

        with h5py.File(cpath, "r") as f:
            keys = list(f.keys())
            attrs = {k: str(v) for k, v in f.attrs.items()}
            print(f"    Available Datasets/Channels: {keys}")
            print(f"    Top-level Attributes Count: {len(attrs)}")
            for ch in ["TIR-1", "TIR-2", "WV", "MIR"]:
                if ch in f:
                    ds = f[ch]
                    print(f"      Channel {ch}: shape={ds.shape}, dtype={ds.dtype}")

        # Compute physical metrics
        metrics = compute_physical_crop_metrics(cpath, channel="TIR-1")
        min_bt = metrics["temperature_quantiles_kelvin"]["min_kelvin"]
        med_bt = metrics["temperature_quantiles_kelvin"]["median_kelvin"]
        max_bt = metrics["temperature_quantiles_kelvin"]["max_kelvin"]
        cold_frac = metrics["cold_cloud_analytics"]["fraction_under_200k"]
        valid_frac = metrics["valid_pixels"] / metrics["total_pixels"]

        print(f"    Valid Pixels: {metrics['valid_pixels']}/{metrics['total_pixels']} ({valid_frac * 100:.2f}%)")
        print(f"    Brightness Temp (TIR-1): min={min_bt:.2f} K, median={med_bt:.2f} K, max={max_bt:.2f} K")
        print(f"    Cold Cloud Fraction (<200K): {cold_frac:.4f}")

        # Verification Invariant: ISRO calibration LUT floor >= 179.80 K
        assert min_bt >= 179.80, f"Radiometric floor violation: {min_bt} < 179.80 K"
        assert valid_frac >= 0.9999, f"Invalid pixel ratio: {valid_frac}"

        # Render PNG
        png_bytes = render_crop_png(cpath, channel="TIR-1")
        print(f"    Rendered PNG Preview Size: {len(png_bytes):,} bytes")
        assert len(png_bytes) > 10000

        results[name] = {
            "satellite": sat,
            "filename": fname,
            "size_bytes": cpath.stat().st_size,
            "channels": keys,
            "valid_fraction": valid_frac,
            "min_kelvin": min_bt,
            "median_kelvin": med_bt,
            "max_kelvin": max_bt,
            "cold_cloud_fraction": cold_frac,
            "png_render_bytes": len(png_bytes),
        }

    # Verify DANA governance flags in scientific ledger
    if LEDGER_PATH.is_file():
        with open(LEDGER_PATH, encoding="utf-8") as f:
            ledger = json.load(f)
        dana_entry = next((c for c in ledger["crops"] if c.get("storm_name") == "DANA"), None)
        assert dana_entry is not None, "DANA entry missing in scientific ledger"
        elig = dana_entry["model_eligibility_by_task"]
        print(f"\n[DANA Governance Verification]:")
        print(f"    primary_imd_category_classification: {elig['primary_imd_category_classification']} (Must be False)")
        print(f"    primary_imd_wind_intensity_regression: {elig['primary_imd_wind_intensity_regression']} (Must be False)")
        print(f"    post_landfall_weakening_analysis: {elig['post_landfall_weakening_analysis']} (Must be True)")
        print(f"    general_atmospheric_research: {elig['general_atmospheric_research']} (Must be True)")
        print(f"    Exclusion reason: {dana_entry.get('exclusion_reason')}")
        assert elig["primary_imd_category_classification"] is False
        assert elig["primary_imd_wind_intensity_regression"] is False
        assert elig["post_landfall_weakening_analysis"] is True
        assert elig["general_atmospheric_research"] is True

    print("\n" + "=" * 75)
    print("ALL 4 AUTHENTIC INSAT CROPS COMPLY FULLY WITH SCIENTIFIC STANDARDS!")
    print("=" * 75)
    return results


if __name__ == "__main__":
    test_insat_crops()
