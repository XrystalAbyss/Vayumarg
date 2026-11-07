"""Inspection and scientific validation of authentic INSAT-3DR HDF5 granule."""

import hashlib
from pathlib import Path

import h5py
import numpy as np

from vayumarg.satellite.mosdac_adapter import MOSDACAdapter

HDF5_PATH = Path("data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5")


def inspect_hdf5(file_path: Path):
    if not file_path.is_file():
        raise FileNotFoundError(f"Target file not found: {file_path}")

    file_size_bytes = file_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)

    # Compute SHA-256
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    sha256 = hasher.hexdigest()

    print(f"File: {file_path.name}")
    print(f"Size: {file_size_bytes} bytes ({file_size_mb:.2f} MB)")
    print(f"SHA-256: {sha256}")

    results = {
        "filename": file_path.name,
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_mb, 2),
        "sha256": sha256,
        "groups": [],
        "datasets": {},
        "attributes": {},
        "channels": {},
        "planck_test": {},
    }

    with h5py.File(file_path, "r") as h5:
        # Global attributes
        for k, v in h5.attrs.items():
            val = str(v)
            if isinstance(v, bytes):
                val = v.decode("utf-8", errors="replace")
            elif isinstance(v, np.ndarray):
                val = v.tolist()
            results["attributes"][k] = val

        # Traverse groups and datasets
        def visitor(name, node):
            if isinstance(node, h5py.Group):
                results["groups"].append(name)
            elif isinstance(node, h5py.Dataset):
                ds_info = {
                    "shape": list(node.shape),
                    "dtype": str(node.dtype),
                    "attrs": {k: str(v) for k, v in node.attrs.items()},
                }
                results["datasets"][name] = ds_info

        h5.visititems(visitor)

        # Inspect channels
        for ch_key in ["IMG_TIR1", "IMG_TIR2", "IMG_WV", "IMG_MIR", "IMG_VIS", "IMG_SWIR"]:
            # Find dataset matching ch_key
            matching = [name for name in results["datasets"] if ch_key in name]
            if matching:
                ds_name = matching[0]
                ds = h5[ds_name]
                data = ds[:]
                valid_mask = data > 0
                results["channels"][ch_key] = {
                    "dataset_name": ds_name,
                    "shape": list(ds.shape),
                    "dtype": str(ds.dtype),
                    "min_val": float(np.min(data)),
                    "max_val": float(np.max(data)),
                    "mean_valid_val": float(np.mean(data[valid_mask]))
                    if np.any(valid_mask)
                    else None,
                }

        # Test Planck inversion if TIR-1 is present
        tir1_matches = [
            name for name in results["datasets"] if "IMG_TIR1" in name or "TIR1" in name
        ]
        if tir1_matches:
            tir1_ds = h5[tir1_matches[0]]
            tir1_data = tir1_ds[:]
            valid_pixels = tir1_data[tir1_data > 0]
            if len(valid_pixels) > 0:
                sample_rad = float(np.median(valid_pixels))
                # If values are raw counts or radiances
                tb = MOSDACAdapter.calculate_brightness_temperature(sample_rad, "TIR-1")
                results["planck_test"] = {
                    "sample_value": sample_rad,
                    "calculated_brightness_temp_k": tb,
                }

    return results


if __name__ == "__main__":
    res = inspect_hdf5(HDF5_PATH)
    print("\n--- SUMMARY ---")
    print(f"Total Datasets: {len(res['datasets'])}")
    print(f"Channels found: {list(res['channels'].keys())}")
    for ch, info in res["channels"].items():
        print(f"  {ch}: shape={info['shape']}, min={info['min_val']}, max={info['max_val']}")
    print(f"Planck Test: {res['planck_test']}")
