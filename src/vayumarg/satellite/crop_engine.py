"""Multi-channel physical satellite cropping and radiometric calibration engine.

Extracts physically aligned, calibrated multi-spectral crops (TIR-1, WV, TIR-2, MIR)
from authentic ISRO INSAT L1B standard HDF5 granules with:
- Shared physical extent (km) across differing sensor spatial resolutions.
- Radiometric calibration lookup table (LUT) inversion to physical Kelvin.
- Calibration saturation / lower boundary clamping detection.
- Accurate pixel-level quality and space-fill masks.
- Transparent spatial co-registration via pure NumPy bilinear interpolation.
- Full preservation of native arrays, effective resolution, and provenance.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np

from vayumarg.core.logging import get_logger

logger = get_logger("vayumarg.satellite.crop_engine")

# Channel specifications in INSAT L1B HDF5
CHANNEL_CONFIG = {
    "TIR-1": {
        "dataset": "IMG_TIR1",
        "lut_temp": "IMG_TIR1_TEMP",
        "lut_rad": "IMG_TIR1_RADIANCE",
        "lat_ds": "Latitude",
        "lon_ds": "Longitude",
        "native_res_km": 4.0,
        "fill_value": 1023,
        "clamped_count_min": 921,  # Lower LUT table boundary (179.86 K)
    },
    "TIR-2": {
        "dataset": "IMG_TIR2",
        "lut_temp": "IMG_TIR2_TEMP",
        "lut_rad": "IMG_TIR2_RADIANCE",
        "lat_ds": "Latitude",
        "lon_ds": "Longitude",
        "native_res_km": 4.0,
        "fill_value": 1023,
        "clamped_count_min": 921,
    },
    "WV": {
        "dataset": "IMG_WV",
        "lut_temp": "IMG_WV_TEMP",
        "lut_rad": "IMG_WV_RADIANCE",
        "lat_ds": "Latitude_WV",
        "lon_ds": "Longitude_WV",
        "native_res_km": 8.0,
        "fill_value": 1023,
        "clamped_count_min": 995,  # Lower LUT table boundary (179.69 K)
    },
    "MIR": {
        "dataset": "IMG_MIR",
        "lut_temp": "IMG_MIR_TEMP",
        "lut_rad": "IMG_MIR_RADIANCE",
        "lat_ds": "Latitude",
        "lon_ds": "Longitude",
        "native_res_km": 4.0,
        "fill_value": 1023,
        "clamped_count_min": 921,
    },
}


def bilinear_resample_2d(
    arr: np.ndarray,
    target_shape: tuple[int, int],
    valid_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Perform physically sound 2D bilinear interpolation using pure NumPy.

    If valid_mask is provided (or if arr contains NaNs), normalized bilinear
    interpolation is applied: valid neighbor weights are re-normalized so that
    invalid/fill/missing values cannot contaminate valid pixels.
    Where a target pixel is surrounded entirely by invalid pixels, the output
    is set to np.nan rather than an arbitrary 0.0 temperature.
    """
    src_h, src_w = arr.shape
    dst_h, dst_w = target_shape
    if (src_h, src_w) == (dst_h, dst_w):
        if valid_mask is not None:
            out = arr.copy().astype(float)
            out[~valid_mask] = np.nan
            return out
        return arr.copy()

    if src_h == 1 or src_w == 1:
        # Edge case: single pixel dimension
        val = arr[0, 0]
        if valid_mask is not None and not valid_mask[0, 0]:
            val = np.nan
        return np.full(target_shape, val, dtype=float)

    y = np.linspace(0.0, float(src_h - 1), dst_h)
    x = np.linspace(0.0, float(src_w - 1), dst_w)

    x0 = np.clip(np.floor(x).astype(int), 0, src_w - 2)
    x1 = x0 + 1
    dx = (x - x0)[None, :]  # shape (1, dst_w)

    y0 = np.clip(np.floor(y).astype(int), 0, src_h - 2)
    y1 = y0 + 1
    dy = (y - y0)[:, None]  # shape (dst_h, 1)

    wa = (1.0 - dx) * (1.0 - dy)
    wb = (1.0 - dx) * dy
    wc = dx * (1.0 - dy)
    wd = dx * dy

    # Determine if mask handling or NaN handling is required
    has_nans = np.isnan(arr).any()
    if valid_mask is None and not has_nans:
        # Fast path: pure unmasked bilinear interpolation
        return (
            wa * arr[y0[:, None], x0[None, :]]
            + wb * arr[y1[:, None], x0[None, :]]
            + wc * arr[y0[:, None], x1[None, :]]
            + wd * arr[y1[:, None], x1[None, :]]
        )

    # Normalized bilinear interpolation path:
    if valid_mask is None:
        m = (~np.isnan(arr)).astype(float)
        clean_arr = np.nan_to_num(arr, nan=0.0).astype(float)
    else:
        m = valid_mask.astype(float)
        clean_arr = np.where(valid_mask, np.nan_to_num(arr, nan=0.0), 0.0).astype(float)

    # Sample weights and values at 4 bounding corners
    m_a = m[y0[:, None], x0[None, :]]
    m_b = m[y1[:, None], x0[None, :]]
    m_c = m[y0[:, None], x1[None, :]]
    m_d = m[y1[:, None], x1[None, :]]

    val_a = clean_arr[y0[:, None], x0[None, :]]
    val_b = clean_arr[y1[:, None], x0[None, :]]
    val_c = clean_arr[y0[:, None], x1[None, :]]
    val_d = clean_arr[y1[:, None], x1[None, :]]

    w_valid_total = wa * m_a + wb * m_b + wc * m_c + wd * m_d
    weighted_sum = wa * m_a * val_a + wb * m_b * val_b + wc * m_c * val_c + wd * m_d * val_d

    result = np.full(target_shape, np.nan, dtype=float)
    has_valid_neighbors = w_valid_total > 1e-6
    result[has_valid_neighbors] = (
        weighted_sum[has_valid_neighbors] / w_valid_total[has_valid_neighbors]
    )
    return result


@dataclass
class ChannelCropData:
    """Cropped channel data containing native, calibrated, and quality arrays."""

    channel_name: str
    native_counts: np.ndarray
    native_temps_k: np.ndarray
    coregistered_temps_k: np.ndarray
    valid_mask: np.ndarray
    clamped_mask: np.ndarray
    native_shape: tuple[int, int]
    coregistered_shape: tuple[int, int]
    native_resolution_km: float
    effective_resolution_km: float
    resampling_method: str
    center_pixel_row_col: tuple[int, int]
    center_pixel_lat_lon: tuple[float, float]
    center_pixel_tb_k: float
    min_tb_k: float
    max_tb_k: float
    mean_tb_k: float
    fill_pixel_ratio: float
    clamped_pixel_ratio: float


@dataclass
class MultiChannelCropResult:
    """Scientific multi-channel crop package for a storm-centered observation."""

    granule_filename: str
    center_target_lat: float
    center_target_lon: float
    extent_km: float
    target_resolution_km: float
    target_shape: tuple[int, int]
    channels: dict[str, ChannelCropData]
    combined_valid_mask: np.ndarray
    is_fully_on_disk: bool
    qc_flags: dict[str, Any]


class MultiChannelCropEngine:
    """Engine for extracting physically co-registered multi-channel satellite crops."""

    def __init__(self, extent_km: float = 800.0, target_resolution_km: float = 4.0):
        self.extent_km = extent_km
        self.target_resolution_km = target_resolution_km
        # Calculate target array dimensions (e.g. 800 km / 4.0 km = 200 -> 201x201 with center)
        half_pixels = int(round((extent_km / 2.0) / target_resolution_km))
        self.target_pixels = 2 * half_pixels + 1
        self.target_shape = (self.target_pixels, self.target_pixels)

    def extract_crop(
        self,
        hdf5_path: Path | str,
        center_lat: float,
        center_lon: float,
        channels: list[str] | None = None,
    ) -> MultiChannelCropResult:
        """Extract and calibrate multi-channel crop centered at specified coordinates."""
        hdf5_path = Path(hdf5_path)
        if not hdf5_path.is_file():
            raise FileNotFoundError(f"HDF5 file not found: {hdf5_path}")

        if channels is None:
            channels = ["TIR-1", "WV"]

        channel_results: dict[str, ChannelCropData] = {}

        with h5py.File(hdf5_path, "r") as h5:
            for ch in channels:
                if ch not in CHANNEL_CONFIG:
                    raise ValueError(
                        f"Unsupported channel: {ch}. Supported: {list(CHANNEL_CONFIG.keys())}"
                    )
                cfg = CHANNEL_CONFIG[ch]
                if cfg["dataset"] not in h5:
                    logger.warning(
                        "Dataset %s for channel %s not in file, skipping", cfg["dataset"], ch
                    )
                    continue

                crop_data = self._process_single_channel(h5, ch, cfg, center_lat, center_lon)
                channel_results[ch] = crop_data

        if not channel_results:
            raise RuntimeError(f"No channels could be processed from {hdf5_path}")

        # Combined valid mask on the target grid (pixel valid in ALL requested channels)
        coreg_masks = []
        for c in channel_results.values():
            if c.native_shape == self.target_shape:
                coreg_masks.append(c.valid_mask)
            else:
                coreg_mask = (
                    bilinear_resample_2d(c.valid_mask.astype(float), self.target_shape) > 0.5
                )
                coreg_masks.append(coreg_mask)
        combined_valid = np.all(coreg_masks, axis=0)
        is_fully_on_disk = bool(np.all(combined_valid))

        qc_flags = {
            "extent_km": self.extent_km,
            "target_resolution_km": self.target_resolution_km,
            "target_shape": list(self.target_shape),
            "channels_processed": list(channel_results.keys()),
            "is_fully_on_disk": is_fully_on_disk,
            "combined_valid_ratio": float(np.mean(combined_valid)),
        }

        return MultiChannelCropResult(
            granule_filename=hdf5_path.name,
            center_target_lat=center_lat,
            center_target_lon=center_lon,
            extent_km=self.extent_km,
            target_resolution_km=self.target_resolution_km,
            target_shape=self.target_shape,
            channels=channel_results,
            combined_valid_mask=combined_valid,
            is_fully_on_disk=is_fully_on_disk,
            qc_flags=qc_flags,
        )

    def _process_single_channel(
        self,
        h5: h5py.File,
        ch_name: str,
        cfg: dict[str, Any],
        center_lat: float,
        center_lon: float,
    ) -> ChannelCropData:
        """Process native slice, LUT mapping, quality masking, and resampling for one channel."""
        # 1. Geolocation lookup
        lat_ds_name = cfg["lat_ds"]
        lon_ds_name = cfg["lon_ds"]
        native_res = cfg["native_res_km"]

        # Support INSAT-3DS where Latitude_WV does not exist (shares 4km Latitude/Longitude grid)
        if lat_ds_name not in h5 and "Latitude" in h5:
            lat_ds_name = "Latitude"
            lon_ds_name = "Longitude"
            if ch_name == "WV":
                native_res = 4.0

        lat_ds = h5[lat_ds_name]
        lon_ds = h5[lon_ds_name]
        lat_raw = lat_ds[:]
        lon_raw = lon_ds[:]

        lat_scale = float(lat_ds.attrs.get("scale_factor", [0.01])[0])
        lon_scale = float(lon_ds.attrs.get("scale_factor", [0.01])[0])
        lat_fill = int(lat_ds.attrs.get("_FillValue", [32767])[0])
        lon_fill = int(lon_ds.attrs.get("_FillValue", [32767])[0])

        valid_geo = (lat_raw != lat_fill) & (lon_raw != lon_fill)
        lats = np.full_like(lat_raw, np.nan, dtype=np.float32)
        lons = np.full_like(lon_raw, np.nan, dtype=np.float32)
        lats[valid_geo] = lat_raw[valid_geo] * lat_scale
        lons[valid_geo] = lon_raw[valid_geo] * lon_scale

        dist = np.full_like(lat_raw, 1e9, dtype=np.float64)
        dist[valid_geo] = (lats[valid_geo] - center_lat) ** 2 + (lons[valid_geo] - center_lon) ** 2
        r_center, c_center = np.unravel_index(np.argmin(dist), dist.shape)

        actual_center_lat = float(lats[r_center, c_center])
        actual_center_lon = float(lons[r_center, c_center])

        # 2. Compute native slice boundaries for physical extent
        half_native_pixels = int(round((self.extent_km / 2.0) / native_res))
        r_start = r_center - half_native_pixels
        r_end = r_center + half_native_pixels + 1
        c_start = c_center - half_native_pixels
        c_end = c_center + half_native_pixels + 1

        # Check bounds
        pad_top = max(0, -r_start)
        pad_bottom = max(0, r_end - lat_raw.shape[0])
        pad_left = max(0, -c_start)
        pad_right = max(0, c_end - lat_raw.shape[1])

        r_slice_start = max(0, r_start)
        r_slice_end = min(lat_raw.shape[0], r_end)
        c_slice_start = max(0, c_start)
        c_slice_end = min(lat_raw.shape[1], c_end)

        raw_array = h5[cfg["dataset"]][0, r_slice_start:r_slice_end, c_slice_start:c_slice_end]

        if pad_top > 0 or pad_bottom > 0 or pad_left > 0 or pad_right > 0:
            raw_array = np.pad(
                raw_array,
                ((pad_top, pad_bottom), (pad_left, pad_right)),
                mode="constant",
                constant_values=cfg["fill_value"],
            )

        native_counts = raw_array.astype(int)
        native_shape = native_counts.shape

        # 3. Radiometric LUT Mapping
        lut_temp = h5[cfg["lut_temp"]][:]
        # Clamped indexing (0..1023)
        valid_indices = np.clip(native_counts, 0, len(lut_temp) - 1)
        native_temps_k = lut_temp[valid_indices]

        # 4. Quality Masks
        fill_val = cfg["fill_value"]
        valid_mask = native_counts != fill_val
        min_temp = np.min(lut_temp)
        min_indices = np.where(lut_temp == min_temp)[0]
        clamped_min = int(min_indices[0]) if len(min_indices) > 0 else cfg["clamped_count_min"]
        clamped_mask = native_counts >= clamped_min

        center_raw = int(h5[cfg["dataset"]][0, r_center, c_center])
        center_tb = float(lut_temp[min(center_raw, len(lut_temp) - 1)])

        # 5. Co-registration / Resampling
        if native_shape == self.target_shape:
            coregistered_temps_k = native_temps_k.copy()
            resampling_method = "native/none"
            effective_res = native_res
        else:
            coregistered_temps_k = bilinear_resample_2d(
                native_temps_k, self.target_shape, valid_mask=valid_mask
            )
            resampling_method = "bilinear"
            effective_res = native_res  # Resampling does NOT add new high-frequency resolution

        # Temperature stats on valid pixels
        if np.any(valid_mask):
            valid_temps = native_temps_k[valid_mask]
            min_tb = float(np.min(valid_temps))
            max_tb = float(np.max(valid_temps))
            mean_tb = float(np.mean(valid_temps))
        else:
            min_tb = max_tb = mean_tb = float("nan")

        fill_ratio = float(np.mean(~valid_mask))
        clamped_ratio = float(np.mean(clamped_mask[valid_mask])) if np.any(valid_mask) else 0.0

        return ChannelCropData(
            channel_name=ch_name,
            native_counts=native_counts,
            native_temps_k=native_temps_k,
            coregistered_temps_k=coregistered_temps_k,
            valid_mask=valid_mask,
            clamped_mask=clamped_mask,
            native_shape=native_shape,
            coregistered_shape=self.target_shape,
            native_resolution_km=native_res,
            effective_resolution_km=effective_res,
            resampling_method=resampling_method,
            center_pixel_row_col=(r_center, c_center),
            center_pixel_lat_lon=(actual_center_lat, actual_center_lon),
            center_pixel_tb_k=center_tb,
            min_tb_k=min_tb,
            max_tb_k=max_tb,
            mean_tb_k=mean_tb,
            fill_pixel_ratio=fill_ratio,
            clamped_pixel_ratio=clamped_ratio,
        )

    @staticmethod
    def save_to_hdf5(crop_result: MultiChannelCropResult, output_path: Path | str) -> str:
        """Save multi-channel crop to versioned, documented HDF5 container."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with h5py.File(output_path, "w") as out:
            # Global Attributes
            out.attrs["granule_filename"] = crop_result.granule_filename
            out.attrs["center_target_lat"] = crop_result.center_target_lat
            out.attrs["center_target_lon"] = crop_result.center_target_lon
            out.attrs["extent_km"] = crop_result.extent_km
            out.attrs["target_resolution_km"] = crop_result.target_resolution_km
            out.attrs["is_fully_on_disk"] = crop_result.is_fully_on_disk
            out.attrs["channels"] = list(crop_result.channels.keys())

            # Groups
            coreg_grp = out.create_group("coregistered")
            native_grp = out.create_group("native")
            masks_grp = out.create_group("masks")

            masks_grp.create_dataset(
                "combined_valid_mask",
                data=crop_result.combined_valid_mask,
                compression="gzip",
            )

            for ch_name, data in crop_result.channels.items():
                # Coregistered dataset
                ds_coreg = coreg_grp.create_dataset(
                    ch_name,
                    data=data.coregistered_temps_k,
                    compression="gzip",
                )
                ds_coreg.attrs["units"] = "K"
                ds_coreg.attrs["native_resolution_km"] = data.native_resolution_km
                ds_coreg.attrs["effective_resolution_km"] = data.effective_resolution_km
                ds_coreg.attrs["resampling_method"] = data.resampling_method

                # Native group
                ch_native_grp = native_grp.create_group(ch_name)
                ch_native_grp.create_dataset("counts", data=data.native_counts, compression="gzip")
                ch_native_grp.create_dataset(
                    "brightness_temperature_k", data=data.native_temps_k, compression="gzip"
                )
                ch_native_grp.create_dataset("valid_mask", data=data.valid_mask, compression="gzip")
                ch_native_grp.create_dataset(
                    "clamped_mask", data=data.clamped_mask, compression="gzip"
                )
                ch_native_grp.attrs["native_resolution_km"] = data.native_resolution_km
                ch_native_grp.attrs["center_tb_k"] = data.center_pixel_tb_k
                ch_native_grp.attrs["center_lat"] = data.center_pixel_lat_lon[0]
                ch_native_grp.attrs["center_lon"] = data.center_pixel_lat_lon[1]

        # Calculate SHA-256
        import hashlib

        hasher = hashlib.sha256()
        with open(output_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
