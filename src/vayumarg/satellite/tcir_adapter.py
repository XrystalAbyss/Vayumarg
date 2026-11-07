"""Official TCIR (Tropical Cyclone for Image-to-intensity Regression) Adapter.

Provides lazy, chunked access, inspection, metadata profiling, and scientific
validation for multi-channel satellite HDF5 archives published by NTU CSIE:
- Channels: IR1 (Index 0), WV (Index 1), VIS (Index 2), PMW (Index 3)
- Spatial Dimensions: 201 x 201 pixels centered on cyclone vortex (~4 km/pixel)
- HDF5 Structure: Datasets 'matrix' (N, 201, 201, 4) and 'info' (DataFrame)
- Strict NaN and missing value handling
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from vayumarg.core.hashing import calculate_sha256
from vayumarg.core.logging import get_logger

logger = get_logger("vayumarg.satellite.tcir")

EXPECTED_CHANNELS = ["IR1", "WV", "VIS", "PMW"]
EXPECTED_FRAME_SHAPE = (201, 201, 4)


@dataclass
class TCIRFrameMetadata:
    """Metadata for an individual TCIR satellite frame."""

    frame_index: int
    storm_id: str
    storm_name: str
    season_year: int
    basin: str
    subbasin: str | None
    timestamp_utc: datetime
    latitude: float
    longitude: float
    vmax_knots: float | None
    mslp_hpa: float | None
    is_north_indian_ocean: bool


@dataclass
class TCIRDatasetProfile:
    """Scientific profile of an inspected TCIR HDF5 file."""

    file_path: str
    file_size_bytes: int
    sha256_checksum: str
    total_frames: int
    matrix_shape: tuple[int, ...]
    matrix_dtype: str
    channels: list[str]
    unique_storms_count: int
    unique_seasons: list[int]
    basin_counts: dict[str, int]
    north_indian_ocean_frames: int
    channel_missing_percentages: dict[str, float]
    vmax_range_knots: tuple[float | None, float | None]
    mslp_range_hpa: tuple[float | None, float | None]


class TCIRAdapter:
    """High-performance, memory-safe reader for TCIR HDF5 archives."""

    def __init__(self, file_path: Path | str):
        self.file_path = Path(file_path)
        if not self.file_path.is_file():
            raise FileNotFoundError(f"TCIR file does not exist: {self.file_path}")

        self._sha256: str | None = None
        self._info_df: pd.DataFrame | None = None

    @property
    def sha256(self) -> str:
        """Calculate or retrieve cached file SHA-256."""
        if self._sha256 is None:
            self._sha256 = calculate_sha256(self.file_path)
        return self._sha256

    def load_metadata_table(self) -> pd.DataFrame:
        """Load and normalize the 'info' metadata table."""
        if self._info_df is not None:
            return self._info_df

        with h5py.File(self.file_path, "r") as f:
            if "info" not in f:
                raise KeyError(
                    f"Corrupt TCIR file: missing 'info' dataset/group in {self.file_path}"
                )

            info_node = f["info"]
            if isinstance(info_node, h5py.Dataset):
                data = info_node[:]
                # If structured numpy array
                if data.dtype.names:
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame(data)
            else:
                # Fallback to pandas read_hdf if stored as PyTables group
                try:
                    df = pd.read_hdf(self.file_path, key="info", mode="r")
                except Exception as exc:
                    logger.warning("Falling back to raw HDF5 group extraction for 'info': %s", exc)
                    # Extract datasets in group
                    cols = {}
                    for k in info_node.keys():
                        val = info_node[k][:]
                        cols[k] = [v.decode("utf-8") if isinstance(v, bytes) else v for v in val]
                    df = pd.DataFrame(cols)

        # Standardize column naming
        df.columns = [str(c).strip().lower() for c in df.columns]
        self._info_df = df
        return df

    def get_frame_metadata(self, frame_idx: int) -> TCIRFrameMetadata:
        """Retrieve structured metadata for a specific frame index."""
        df = self.load_metadata_table()
        if frame_idx < 0 or frame_idx >= len(df):
            raise IndexError(f"Frame index {frame_idx} out of range [0, {len(df) - 1}]")

        row = df.iloc[frame_idx]

        # Resolve storm identity
        sid = str(row.get("sid", row.get("id", f"STORM_{frame_idx}"))).strip()
        name = str(row.get("name", "UNNAMED")).strip().upper()

        # Parse season year
        season_val = row.get("season", row.get("year", 0))
        try:
            season = int(season_val)
        except (ValueError, TypeError):
            season = 0

        # Parse basin and subbasin
        basin = str(row.get("basin", "IO")).strip().upper()
        subbasin = str(row.get("subbasin", "")).strip().upper() or None

        # Parse timestamp
        time_raw = row.get("time", row.get("iso_time", row.get("datetime")))
        if isinstance(time_raw, pd.Timestamp):
            ts = time_raw.to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
        elif isinstance(time_raw, (int, float, np.integer, np.floating)):
            # Formats like YYYYMMDDHH or epoch
            time_str = str(int(time_raw))
            if len(time_str) == 10:
                ts = datetime.strptime(time_str, "%Y%m%d%H").replace(tzinfo=UTC)
            else:
                ts = datetime.fromtimestamp(float(time_raw), tz=UTC)
        else:
            time_str = str(time_raw).strip()
            if len(time_str) == 10 and time_str.isdigit():
                ts = datetime.strptime(time_str, "%Y%m%d%H").replace(tzinfo=UTC)
            else:
                try:
                    ts = datetime.fromisoformat(time_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=UTC)
                except ValueError:
                    ts = datetime(season or 1970, 1, 1, tzinfo=UTC)

        # Coordinates
        lat = float(row.get("lat", row.get("latitude", 0.0)))
        lon = float(row.get("lon", row.get("longitude", 0.0)))

        # Intensity labels
        vmax_raw = row.get("vmax", row.get("wind", None))
        vmax = float(vmax_raw) if pd.notna(vmax_raw) and float(vmax_raw) >= 0 else None

        mslp_raw = row.get("mslp", row.get("pres", None))
        mslp = float(mslp_raw) if pd.notna(mslp_raw) and float(mslp_raw) > 500 else None

        # Determine North Indian Ocean membership
        # In TCIR, IO includes both NI (North Indian: Bay of Bengal/Arabian Sea, Lat > 0)
        # and SH (South Indian Ocean, Lat < 0)
        is_nio = (basin in ("NI", "BB", "AS")) or (basin == "IO" and lat >= 0.0)

        return TCIRFrameMetadata(
            frame_index=frame_idx,
            storm_id=sid,
            storm_name=name,
            season_year=season,
            basin=basin,
            subbasin=subbasin,
            timestamp_utc=ts,
            latitude=lat,
            longitude=lon,
            vmax_knots=vmax,
            mslp_hpa=mslp,
            is_north_indian_ocean=is_nio,
        )

    def read_frame_channels(
        self,
        frame_idx: int,
        channels: list[str] | None = None,
    ) -> dict[str, np.ndarray]:
        """Read a single frame lazily from HDF5 matrix without loading full dataset."""
        req_channels = channels or EXPECTED_CHANNELS
        channel_indices = [
            EXPECTED_CHANNELS.index(c) for c in req_channels if c in EXPECTED_CHANNELS
        ]

        with h5py.File(self.file_path, "r") as f:
            if "matrix" not in f:
                raise KeyError(f"Corrupt TCIR file: missing 'matrix' dataset in {self.file_path}")

            matrix = f["matrix"]
            if frame_idx < 0 or frame_idx >= matrix.shape[0]:
                raise IndexError(f"Frame index {frame_idx} out of range [0, {matrix.shape[0] - 1}]")

            # Lazy slice: shape is (201, 201, num_channels)
            frame_slice = matrix[frame_idx, :, :, channel_indices]

        result = {}
        for idx, ch_name in enumerate(req_channels):
            result[ch_name] = frame_slice[:, :, idx].astype(np.float32)

        return result

    def generate_profile(self, sample_limit: int = 500) -> TCIRDatasetProfile:
        """Inspect the dataset and generate a scientific profile."""
        file_stat = self.file_path.stat()
        df = self.load_metadata_table()
        total_frames = len(df)

        with h5py.File(self.file_path, "r") as f:
            matrix = f["matrix"]
            matrix_shape = tuple(matrix.shape)
            matrix_dtype = str(matrix.dtype)

            # Sample subset of frames for channel missingness to conserve memory
            stride = max(1, total_frames // sample_limit)
            sampled_indices = list(range(0, total_frames, stride))[:sample_limit]
            sampled_frames = matrix[sampled_indices, :, :, :]

        # Missingness per channel
        missing_pct = {}
        for ch_idx, ch_name in enumerate(EXPECTED_CHANNELS):
            ch_data = sampled_frames[:, :, :, ch_idx]
            n_nan = np.isnan(ch_data).sum()
            total_px = ch_data.size
            missing_pct[ch_name] = round(float(n_nan / total_px * 100.0), 3)

        # Basin statistics
        basin_col = "basin" if "basin" in df.columns else None
        basin_counts = (
            {str(k): int(v) for k, v in df[basin_col].value_counts().items()} if basin_col else {}
        )

        # Identify NIO frames
        nio_frames = 0
        lat_col = (
            "lat" if "lat" in df.columns else ("latitude" if "latitude" in df.columns else None)
        )
        if basin_col and lat_col:
            nio_mask = (df[basin_col].isin(["NI", "BB", "AS"])) | (
                (df[basin_col] == "IO") & (pd.to_numeric(df[lat_col], errors="coerce") >= 0.0)
            )
            nio_frames = int(nio_mask.sum())

        # Storm counts
        sid_col = "sid" if "sid" in df.columns else ("id" if "id" in df.columns else None)
        unique_storms = int(df[sid_col].nunique()) if sid_col else 0

        # Season years
        yr_col = "season" if "season" in df.columns else ("year" if "year" in df.columns else None)
        unique_seasons = sorted([int(s) for s in df[yr_col].dropna().unique()]) if yr_col else []

        # Intensity ranges
        vmax_col = "vmax" if "vmax" in df.columns else ("wind" if "wind" in df.columns else None)
        vmax_min = float(df[vmax_col].min()) if vmax_col and not df[vmax_col].empty else None
        vmax_max = float(df[vmax_col].max()) if vmax_col and not df[vmax_col].empty else None

        mslp_col = "mslp" if "mslp" in df.columns else ("pres" if "pres" in df.columns else None)
        mslp_min = float(df[mslp_col].min()) if mslp_col and not df[mslp_col].empty else None
        mslp_max = float(df[mslp_col].max()) if mslp_col and not df[mslp_col].empty else None

        return TCIRDatasetProfile(
            file_path=str(self.file_path.as_posix()),
            file_size_bytes=file_stat.st_size,
            sha256_checksum=self.sha256,
            total_frames=total_frames,
            matrix_shape=matrix_shape,
            matrix_dtype=matrix_dtype,
            channels=EXPECTED_CHANNELS,
            unique_storms_count=unique_storms,
            unique_seasons=unique_seasons,
            basin_counts=basin_counts,
            north_indian_ocean_frames=nio_frames,
            channel_missing_percentages=missing_pct,
            vmax_range_knots=(vmax_min, vmax_max),
            mslp_range_hpa=(mslp_min, mslp_max),
        )
