"""Audit INSAT-3DS Water-Vapour resolution, grid spacing, and metadata."""

from pathlib import Path

import h5py
import numpy as np


def main():
    path = Path("data/raw/satellite/insat_real/3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5")
    with h5py.File(path, "r") as f:
        print(f"File: {path.name}")
        print("\n--- DATASETS & ATTRIBUTES ---")
        for ds_name in [
            "IMG_WV",
            "IMG_TIR1",
            "IMG_TIR2",
            "IMG_MIR",
            "IMG_VIS",
            "Latitude",
            "Longitude",
        ]:
            if ds_name in f:
                ds = f[ds_name]
                print(f"\nDataset: {ds_name}")
                print(f"  Shape: {ds.shape}, Dtype: {ds.dtype}")
                print("  Attrs:")
                for k, v in ds.attrs.items():
                    print(f"    {k}: {v}")

        # Check grid spacing around storm center
        lat_raw = f["Latitude"][:]
        lon_raw = f["Longitude"][:]
        scale = float(f["Latitude"].attrs.get("scale_factor", [0.01])[0])
        fill = int(f["Latitude"].attrs.get("_FillValue", [32767])[0])

        valid = (lat_raw != fill) & (lon_raw != fill)
        lats = lat_raw * scale
        lons = lon_raw * scale

        # Find pixel near 21.2 N, 86.4 E
        dist = np.full_like(lat_raw, 1e9, dtype=float)
        dist[valid] = (lats[valid] - 21.2) ** 2 + (lons[valid] - 86.4) ** 2
        r, c = np.unravel_index(np.argmin(dist), dist.shape)

        print(f"\nCenter Pixel near DANA: row={r}, col={c}")
        print(f"  Center Lat={lats[r, c]:.4f}, Lon={lons[r, c]:.4f}")

        # Grid spacing along rows (N-S) and cols (E-W)
        d_lat_row = abs(lats[r + 1, c] - lats[r - 1, c]) / 2.0
        d_lon_col = abs(lons[r, c + 1] - lons[r, c - 1]) / 2.0
        print(f"  Delta Lat per pixel (N-S): {d_lat_row:.4f} deg (~{d_lat_row * 111.1:.2f} km)")
        print(
            f"  Delta Lon per pixel (E-W): {d_lon_col:.4f} deg (~{d_lon_col * 111.1 * np.cos(np.radians(21.2)):.2f} km)"
        )

        # Compare with INSAT-3DR if available
        r_path = Path("data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5")
        if r_path.is_file():
            with h5py.File(r_path, "r") as rf:
                print(f"\n--- COMPARISON WITH INSAT-3DR ({r_path.name}) ---")
                print(f"  3DR IMG_WV shape: {rf['IMG_WV'].shape}")
                print(f"  3DR IMG_TIR1 shape: {rf['IMG_TIR1'].shape}")
                print(f"  3DR Latitude_WV in file: {'Latitude_WV' in rf}")
                if "Latitude_WV" in rf:
                    print(f"  3DR Latitude_WV shape: {rf['Latitude_WV'].shape}")


if __name__ == "__main__":
    main()
