"""Test MultiChannelCropEngine extraction on authentic INSAT-3DR Remal granule."""

from pathlib import Path

from vayumarg.satellite.crop_engine import MultiChannelCropEngine

HDF5_FILE = Path("data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5")
OUT_CROP = Path("data/processed/satellite/crops/REMAL_20240526_1802_MULTICHANNEL.h5")


def main():
    engine = MultiChannelCropEngine(extent_km=800.0, target_resolution_km=4.0)
    print(
        f"Engine Target Shape: {engine.target_shape} ({engine.extent_km} km at {engine.target_resolution_km} km/px)"
    )

    # Extract TIR-1, WV, TIR-2, MIR
    res = engine.extract_crop(
        hdf5_path=HDF5_FILE,
        center_lat=21.70,
        center_lon=89.20,
        channels=["TIR-1", "WV", "TIR-2", "MIR"],
    )

    print("\n--- EXTRACTION RESULTS ---")
    print(f"Granule: {res.granule_filename}")
    print(f"Target: Lat {res.center_target_lat}°N, Lon {res.center_target_lon}°E")
    print(f"Is fully on Earth disk: {res.is_fully_on_disk}")
    print(f"Combined valid pixel ratio: {res.qc_flags['combined_valid_ratio'] * 100:.2f}%")

    for ch_name, data in res.channels.items():
        print(f"\nChannel: {ch_name}")
        print(f"  Native Shape: {data.native_shape} | Native Res: {data.native_resolution_km} km")
        print(
            f"  Coregistered Shape: {data.coregistered_shape} | Effective Res: {data.effective_resolution_km} km (Resampling: {data.resampling_method})"
        )
        print(
            f"  Center Pixel Grid: {data.center_pixel_row_col} -> Lat {data.center_pixel_lat_lon[0]:.4f}°N, Lon {data.center_pixel_lat_lon[1]:.4f}°E"
        )
        print(
            f"  Center Pixel TB: {data.center_pixel_tb_k:.2f} K ({data.center_pixel_tb_k - 273.15:.2f} °C)"
        )
        print(f"  Valid Temp Range: {data.min_tb_k:.2f} K to {data.max_tb_k:.2f} K")
        print(f"  Mean Valid Temp: {data.mean_tb_k:.2f} K")
        print(f"  Fill Pixel Ratio: {data.fill_pixel_ratio * 100:.2f}%")
        print(f"  Clamped (Lower LUT limit) Ratio: {data.clamped_pixel_ratio * 100:.2f}%")

    # Save to HDF5 container
    crop_sha256 = engine.save_to_hdf5(res, OUT_CROP)
    print(f"\nSaved Multi-Channel HDF5: {OUT_CROP}")
    print(f"Size: {OUT_CROP.stat().st_size} bytes | SHA-256: {crop_sha256}")


if __name__ == "__main__":
    main()
