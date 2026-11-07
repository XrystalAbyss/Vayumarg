"""Find Cyclone REMAL eye location and extract scientific crop from authentic INSAT-3DR HDF5."""

import h5py
import numpy as np

HDF5_PATH = "data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5"


def analyze_remal_location():
    with h5py.File(HDF5_PATH, "r") as f:
        lat_raw = f["Latitude"][:]
        lon_raw = f["Longitude"][:]

        lat_scale = float(f["Latitude"].attrs.get("scale_factor", [0.01])[0])
        lon_scale = float(f["Longitude"].attrs.get("scale_factor", [0.01])[0])
        lat_fill = int(f["Latitude"].attrs.get("_FillValue", [32767])[0])
        lon_fill = int(f["Longitude"].attrs.get("_FillValue", [32767])[0])

        valid = (lat_raw != lat_fill) & (lon_raw != lon_fill)

        lats = np.full_like(lat_raw, np.nan, dtype=np.float32)
        lons = np.full_like(lon_raw, np.nan, dtype=np.float32)
        lats[valid] = lat_raw[valid] * lat_scale
        lons[valid] = lon_raw[valid] * lon_scale

        target_lat, target_lon = 21.7, 89.2

        dist = np.full_like(lat_raw, 1e9, dtype=np.float64)
        dist[valid] = (lats[valid] - target_lat) ** 2 + (lons[valid] - target_lon) ** 2

        r, c = np.unravel_index(np.argmin(dist), dist.shape)

        actual_lat = float(lats[r, c])
        actual_lon = float(lons[r, c])

        tir1_count = int(f["IMG_TIR1"][0, r, c])
        tir1_temp = float(f["IMG_TIR1_TEMP"][tir1_count])

        print(f"Target: Lat {target_lat}°N, Lon {target_lon}°E")
        print(f"Closest Grid Pixel: row={r}, col={c}")
        print(f"Pixel Center: Lat {actual_lat:.4f}°N, Lon {actual_lon:.4f}°E")
        print(f"Delta: Lat {actual_lat - target_lat:+.4f}°, Lon {actual_lon - target_lon:+.4f}°")
        print(f"TIR-1 Raw Count: {tir1_count}")
        print(f"TIR-1 Calibrated Brightness Temp: {tir1_temp:.2f} K ({tir1_temp - 273.15:.2f} °C)")

        # Crop 201x201 around the center
        half_box = 100
        r_start = max(0, r - half_box)
        r_end = min(lats.shape[0], r + half_box + 1)
        c_start = max(0, c - half_box)
        c_end = min(lats.shape[1], c + half_box + 1)

        crop_tir1 = f["IMG_TIR1"][0, r_start:r_end, c_start:c_end]
        crop_counts = crop_tir1.astype(int)
        crop_temps = f["IMG_TIR1_TEMP"][:][crop_counts]

        print(f"Crop Shape: {crop_tir1.shape}")
        print(f"Crop Temp Range: {crop_temps.min():.2f} K to {crop_temps.max():.2f} K")
        print(
            f"Deep Convection Minimum (Cold Cloud Top): {crop_temps.min():.2f} K ({crop_temps.min() - 273.15:.2f} °C)"
        )
        print(
            f"Warm Surface Maximum: {crop_temps.max():.2f} K ({crop_temps.max() - 273.15:.2f} °C)"
        )
        print(
            f"Mean Convective Cloud Top Temp: {crop_temps.mean():.2f} K ({crop_temps.mean() - 273.15:.2f} °C)"
        )

        return {
            "row": r,
            "col": c,
            "actual_lat": actual_lat,
            "actual_lon": actual_lon,
            "tir1_count": tir1_count,
            "tir1_temp_k": tir1_temp,
            "crop_shape": crop_tir1.shape,
            "min_temp_k": float(crop_temps.min()),
            "max_temp_k": float(crop_temps.max()),
            "mean_temp_k": float(crop_temps.mean()),
        }


if __name__ == "__main__":
    analyze_remal_location()
