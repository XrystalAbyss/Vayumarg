"""Integration tests validating real authentic INSAT-3DR HDF5 multi-channel processing."""

from pathlib import Path

import h5py
import pytest

from vayumarg.satellite.crop_engine import MultiChannelCropEngine

REAL_HDF5 = Path("data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5")
REAL_3DS_HDF5 = Path("data/raw/satellite/insat_real/3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5")


@pytest.mark.skipif(
    not REAL_HDF5.is_file(), reason="Authentic INSAT-3DR HDF5 file not found on disk"
)
def test_real_hdf5_multichannel_extraction(tmp_path: Path) -> None:
    """Verify that MultiChannelCropEngine extracts and co-registers real TIR-1 and WV channels."""
    engine = MultiChannelCropEngine(extent_km=800.0, target_resolution_km=4.0)
    res = engine.extract_crop(
        hdf5_path=REAL_HDF5,
        center_lat=21.70,
        center_lon=89.20,
        channels=["TIR-1", "WV"],
    )

    assert res.target_shape == (201, 201)
    assert "TIR-1" in res.channels
    assert "WV" in res.channels

    tir1 = res.channels["TIR-1"]
    wv = res.channels["WV"]

    # Native shape and resolution checks
    assert tir1.native_shape == (201, 201)
    assert tir1.native_resolution_km == 4.0
    assert tir1.effective_resolution_km == 4.0
    assert tir1.resampling_method == "native/none"

    assert wv.native_shape == (101, 101)
    assert wv.native_resolution_km == 8.0
    assert wv.effective_resolution_km == 8.0
    assert wv.resampling_method == "bilinear"

    # Co-registered output shapes
    assert tir1.coregistered_shape == (201, 201)
    assert wv.coregistered_shape == (201, 201)

    # Physical temperature checks
    assert 170.0 < tir1.center_pixel_tb_k < 230.0
    assert 180.0 < wv.center_pixel_tb_k < 230.0

    # Save to HDF5 container and verify
    dest = tmp_path / "test_multichannel.h5"
    sha = engine.save_to_hdf5(res, dest)
    assert dest.is_file()
    assert len(sha) == 64

    # Verify saved HDF5 structure
    with h5py.File(dest, "r") as h5_out:
        assert "coregistered/TIR-1" in h5_out
        assert "coregistered/WV" in h5_out
        assert "native/TIR-1/counts" in h5_out
        assert "native/WV/counts" in h5_out
        assert "masks/combined_valid_mask" in h5_out
        assert h5_out["coregistered/TIR-1"].shape == (201, 201)
        assert h5_out["coregistered/WV"].shape == (201, 201)


@pytest.mark.skipif(
    not REAL_3DS_HDF5.is_file(), reason="Authentic INSAT-3DS HDF5 file not found on disk"
)
def test_real_insat3ds_multichannel_extraction(tmp_path: Path) -> None:
    """Verify that MultiChannelCropEngine extracts authentic INSAT-3DS 4-channel crops."""
    engine = MultiChannelCropEngine(extent_km=800.0, target_resolution_km=4.0)
    res = engine.extract_crop(
        hdf5_path=REAL_3DS_HDF5,
        center_lat=21.20,
        center_lon=86.40,
        channels=["TIR-1", "WV", "TIR-2", "MIR"],
    )

    assert res.target_shape == (201, 201)
    for ch in ["TIR-1", "WV", "TIR-2", "MIR"]:
        assert ch in res.channels
        cdata = res.channels[ch]
        # In INSAT-3DS all IR channels share 4.0 km native grid
        assert cdata.native_shape == (201, 201)
        assert cdata.native_resolution_km == 4.0
        assert cdata.effective_resolution_km == 4.0
        assert cdata.resampling_method == "native/none"
        assert 180.0 <= cdata.min_tb_k <= cdata.max_tb_k <= 350.0

    dest = tmp_path / "test_dana_multichannel.h5"
    sha = engine.save_to_hdf5(res, dest)
    assert dest.is_file()
    assert len(sha) == 64


AMPHAN_HDF5 = Path("data/raw/satellite/insat_real/3RIMG_19MAY2020_2358_L1B_STD_V01R00.h5")
BIPARJOY_HDF5 = Path("data/raw/satellite/insat_real/3RIMG_12JUN2023_2358_L1B_STD_V01R00.h5")


@pytest.mark.skipif(
    not AMPHAN_HDF5.is_file(), reason="Authentic AMPHAN HDF5 file not found on disk"
)
def test_real_amphan_multichannel_extraction(tmp_path: Path) -> None:
    """Verify that MultiChannelCropEngine extracts authentic INSAT-3DR AMPHAN crop."""
    engine = MultiChannelCropEngine(extent_km=800.0, target_resolution_km=4.0)
    res = engine.extract_crop(
        hdf5_path=AMPHAN_HDF5,
        center_lat=19.10,
        center_lon=87.50,
        channels=["TIR-1", "WV", "TIR-2", "MIR"],
    )

    assert res.target_shape == (201, 201)
    assert res.qc_flags["combined_valid_ratio"] == 1.0
    dest = tmp_path / "test_amphan_multichannel.h5"
    sha = engine.save_to_hdf5(res, dest)
    assert dest.is_file()
    assert len(sha) == 64


@pytest.mark.skipif(
    not BIPARJOY_HDF5.is_file(), reason="Authentic BIPARJOY HDF5 file not found on disk"
)
def test_real_biparjoy_multichannel_extraction(tmp_path: Path) -> None:
    """Verify that MultiChannelCropEngine extracts authentic INSAT-3DR BIPARJOY crop."""
    engine = MultiChannelCropEngine(extent_km=800.0, target_resolution_km=4.0)
    res = engine.extract_crop(
        hdf5_path=BIPARJOY_HDF5,
        center_lat=20.60,
        center_lon=67.00,
        channels=["TIR-1", "WV", "TIR-2", "MIR"],
    )

    assert res.target_shape == (201, 201)
    assert res.qc_flags["combined_valid_ratio"] == 1.0
    dest = tmp_path / "test_biparjoy_multichannel.h5"
    sha = engine.save_to_hdf5(res, dest)
    assert dest.is_file()
    assert len(sha) == 64
