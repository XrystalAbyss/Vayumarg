"""Inspect and validate WV channel geolocation, calibration, and spatial alignment."""

import h5py
import numpy as np

HDF5_FILE = "data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5"


def inspect_wv():
    with h5py.File(HDF5_FILE, "r") as f:
        print("Latitude_WV shape:", f["Latitude_WV"].shape, "attrs:", dict(f["Latitude_WV"].attrs))
        print(
            "Longitude_WV shape:", f["Longitude_WV"].shape, "attrs:", dict(f["Longitude_WV"].attrs)
        )

        lat_scale = float(f["Latitude_WV"].attrs.get("scale_factor", [0.01])[0])
        lon_scale = float(f["Longitude_WV"].attrs.get("scale_factor", [0.01])[0])
        lat_fill = int(f["Latitude_WV"].attrs.get("_FillValue", [32767])[0])
        lon_fill = int(f["Longitude_WV"].attrs.get("_FillValue", [32767])[0])

        wv_lat_raw = f["Latitude_WV"][:]
        wv_lon_raw = f["Longitude_WV"][:]
        valid_wv = (wv_lat_raw != lat_fill) & (wv_lon_raw != lon_fill)

        lats_wv = np.full_like(wv_lat_raw, np.nan, dtype=np.float32)
        lons_wv = np.full_like(wv_lon_raw, np.nan, dtype=np.float32)
        lats_wv[valid_wv] = wv_lat_raw[valid_wv] * lat_scale
        lons_wv[valid_wv] = wv_lon_raw[valid_wv] * lon_scale

        target_lat, target_lon = 21.70, 89.20
        dist_wv = np.full_like(wv_lat_raw, 1e9, dtype=np.float64)
        dist_wv[valid_wv] = (lats_wv[valid_wv] - target_lat) ** 2 + (
            lons_wv[valid_wv] - target_lon
        ) ** 2
        r_wv, c_wv = np.unravel_index(np.argmin(dist_wv), dist_wv.shape)

        actual_lat = float(lats_wv[r_wv, c_wv])
        actual_lon = float(lons_wv[r_wv, c_wv])
        raw_count = int(f["IMG_WV"][0, r_wv, c_wv])
        cal_temp = float(f["IMG_WV_TEMP"][raw_count])

        print(f"Target: Lat {target_lat}°N, Lon {target_lon}°E")
        print(f"Closest WV pixel: row={r_wv}, col={c_wv}")
        print(f"WV Pixel Center: Lat={actual_lat:.4f}°N, Lon={actual_lon:.4f}°E")
        print(f"Delta: Lat={actual_lat - target_lat:+.4f}°, Lon={actual_lon - target_lon:+.4f}°")
        print(f"WV Raw Count: {raw_count}")
        print(
            f"WV Calibrated Temp at best-track center: {cal_temp:.2f} K ({cal_temp - 273.15:.2f} °C)"
        )

        # Compare with TIR-1 grid center
        # In TIR-1: row=835, col=1783
        # Since WV resolution is 8 km (half the grid dimension of 4 km):
        # 835 / 2 = 417.5 -> row 418
        # 1783 / 2 = 891.5 -> col 892
        print(f"Ratio of TIR1 center (835, 1783) / 2: ({835 / 2:.1f}, {1783 / 2:.1f})")
        print(f"Actual WV grid center: ({r_wv}, {c_wv})")


if __name__ == "__main__":
    inspect_wv()
