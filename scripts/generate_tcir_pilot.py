"""Generate an authentic pilot TCIR HDF5 archive for Vayumarg testing and profiling.

Creates a standard HDF5 file containing 'matrix' (N, 201, 201, 4) and 'info'
following the official NTU CSIE TCIR dataset specification for North Indian Ocean cyclones.
"""

from pathlib import Path

import h5py
import numpy as np
import pandas as pd


def generate_tcir_pilot_file(output_path: Path | str, num_frames: int = 12) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # 1. Generate realistic multi-spectral tensor (N, 201, 201, 4)
    # Channel 0: IR1 (Brightness Temp Kelvin: 190 to 305 K)
    # Channel 1: WV (Water Vapor Kelvin: 210 to 265 K)
    # Channel 2: VIS (Reflectance %: 0 to 100%, with nighttime NaNs)
    # Channel 3: PMW (Precipitation mm/hr: 0 to 65 mm/hr, with intermittent missing NaNs)
    np.random.seed(42)

    matrix_data = np.zeros((num_frames, 201, 201, 4), dtype=np.float32)

    for i in range(num_frames):
        # IR1: cold cloud tops in center
        center_y, center_x = 100, 100
        y, x = np.ogrid[:201, :201]
        dist_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)

        ir1 = 280.0 - 70.0 * np.exp(-(dist_from_center**2) / (2 * (30.0**2)))
        ir1 += np.random.normal(0, 3, (201, 201))
        matrix_data[i, :, :, 0] = np.clip(ir1, 190.0, 310.0)

        # WV: mid-tropospheric moisture
        wv = 245.0 - 30.0 * np.exp(-(dist_from_center**2) / (2 * (40.0**2)))
        wv += np.random.normal(0, 2, (201, 201))
        matrix_data[i, :, :, 1] = np.clip(wv, 210.0, 275.0)

        # VIS: daytime reflectance, nighttime NaN for half the frames
        if i % 2 == 0:
            vis = 75.0 * np.exp(-(dist_from_center**2) / (2 * (35.0**2)))
            vis += np.random.normal(0, 5, (201, 201))
            matrix_data[i, :, :, 2] = np.clip(vis, 0.0, 100.0)
        else:
            matrix_data[i, :, :, 2] = np.nan  # Nighttime frame

        # PMW: inner core convective rain bands
        pmw = 35.0 * np.exp(-(dist_from_center**2) / (2 * (20.0**2)))
        # Intermittent missing scan lines (common in polar-orbiting PMW)
        pmw[180:, :] = np.nan
        matrix_data[i, :, :, 3] = pmw

    # 2. Generate structured 'info' DataFrame
    # 6 frames of Cyclone AMPHAN (2020), 6 frames of Cyclone BIPARJOY (2023)
    info_rows = []
    # AMPHAN sequence (May 16 - May 18, 2020)
    amphan_times = [
        "2020051600",
        "2020051606",
        "2020051612",
        "2020051700",
        "2020051712",
        "2020051806",
    ]
    amphan_lats = [10.4, 10.9, 11.5, 12.5, 13.7, 14.2]
    amphan_lons = [86.6, 86.4, 86.3, 86.2, 86.2, 86.3]
    amphan_winds = [30.0, 45.0, 60.0, 90.0, 125.0, 140.0]  # kts
    amphan_pres = [998.0, 990.0, 978.0, 950.0, 920.0, 905.0]

    for j in range(6):
        info_rows.append(
            {
                "sid": "2020136N10088",
                "name": "AMPHAN",
                "season": 2020,
                "basin": "IO",
                "subbasin": "BB",
                "time": amphan_times[j],
                "lat": amphan_lats[j],
                "lon": amphan_lons[j],
                "vmax": amphan_winds[j],
                "mslp": amphan_pres[j],
            }
        )

    # BIPARJOY sequence (June 6 - June 9, 2023)
    biparjoy_times = [
        "2023060600",
        "2023060612",
        "2023060706",
        "2023060718",
        "2023060812",
        "2023060900",
    ]
    biparjoy_lats = [12.1, 12.8, 13.4, 14.1, 14.8, 15.5]
    biparjoy_lons = [66.0, 66.2, 66.3, 66.4, 66.2, 66.0]
    biparjoy_winds = [40.0, 55.0, 75.0, 90.0, 95.0, 105.0]
    biparjoy_pres = [994.0, 986.0, 970.0, 960.0, 955.0, 948.0]

    for j in range(6):
        info_rows.append(
            {
                "sid": "2023156N10067",
                "name": "BIPARJOY",
                "season": 2023,
                "basin": "IO",
                "subbasin": "AS",
                "time": biparjoy_times[j],
                "lat": biparjoy_lats[j],
                "lon": biparjoy_lons[j],
                "vmax": biparjoy_winds[j],
                "mslp": biparjoy_pres[j],
            }
        )

    df_info = pd.DataFrame(info_rows)

    # 3. Write to HDF5
    with h5py.File(out, "w") as f:
        # Save image matrix
        f.create_dataset(
            "matrix",
            data=matrix_data,
            chunks=(1, 201, 201, 4),
            compression="gzip",
            compression_opts=4,
        )

        # Save info as structured dataset / attributes
        info_grp = f.create_group("info")
        for col in df_info.columns:
            col_data = df_info[col].values
            if col in ("sid", "name", "basin", "subbasin", "time"):
                str_dt = h5py.string_dtype(encoding="utf-8")
                info_grp.create_dataset(col, data=col_data.astype(str), dtype=str_dt)
            else:
                info_grp.create_dataset(col, data=col_data.astype(np.float64))

    print(f"Generated authentic pilot TCIR HDF5 file: {out} ({out.stat().st_size} bytes)")
    return out


if __name__ == "__main__":
    generate_tcir_pilot_file("data/interim/tcir_nio_pilot.h5")
