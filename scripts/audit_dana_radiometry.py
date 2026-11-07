"""Audit radiometric counts, LUT mapping, valid masks, and clamping for DANA crop."""

from pathlib import Path

import h5py
import numpy as np


def main():
    crop_path = Path("data/processed/satellite/crops/DANA_20241025_2330_MULTICHANNEL.h5")
    with h5py.File(crop_path, "r") as f:
        print(f"Crop File: {crop_path.name}")
        print(f"Attrs: {dict(f.attrs)}")

        # Combined mask
        comb_mask = f["masks/combined_valid_mask"][:]
        total_px = comb_mask.size
        valid_px = int(np.sum(comb_mask))
        print("\nMask Analysis:")
        print(f"  Total pixels: {total_px}")
        print(f"  Valid pixels: {valid_px} ({valid_px / total_px:.6f})")
        print(f"  Invalid pixels: {total_px - valid_px}")

        # Find location of invalid pixel(s)
        invalids = np.argwhere(~comb_mask)
        print(f"  Invalid pixel coordinates (row, col): {invalids.tolist()}")

        for ch in ["TIR-1", "WV", "TIR-2", "MIR"]:
            counts = f[f"native/{ch}/counts"][:]
            tb = f[f"native/{ch}/brightness_temperature_k"][:]
            vmask = f[f"native/{ch}/valid_mask"][:]
            cmask = f[f"native/{ch}/clamped_mask"][:]

            print(f"\nChannel: {ch}")
            print(f"  Counts: min={counts.min()}, max={counts.max()}, mean={counts.mean():.1f}")
            print(
                f"  Valid Tb: min={tb[vmask].min():.2f} K, max={tb[vmask].max():.2f} K, mean={tb[vmask].mean():.2f} K"
            )
            print(
                f"  Clamped pixels count: {int(np.sum(cmask))}, ratio: {float(np.mean(cmask)):.6f}"
            )
            print(
                f"  Fill pixels count: {int(np.sum(~vmask))}, ratio: {float(np.mean(~vmask)):.6f}"
            )


if __name__ == "__main__":
    main()
