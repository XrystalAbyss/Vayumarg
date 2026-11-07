from vayumarg.satellite.preview import compute_physical_crop_metrics, render_crop_png

crops = [
    "BIPARJOY_20230612_2358_MULTICHANNEL.h5",
    "AMPHAN_20200519_2358_MULTICHANNEL.h5",
    "DANA_20241025_2330_MULTICHANNEL.h5",
    "REMAL_20240526_1802_MULTICHANNEL.h5",
]

for crop in crops:
    p = f"data/processed/satellite/crops/{crop}"
    for ch in ["TIR-1", "WV"]:
        png = render_crop_png(p, ch)
        m = compute_physical_crop_metrics(p, ch)
        min_k = m["temperature_quantiles_kelvin"]["min_kelvin"]
        mean_k = m["temperature_quantiles_kelvin"]["mean_kelvin"]
        sym = m["azimuthal_symmetry_index"]
        c200 = m["cold_cloud_analytics"]["area_under_200k_km2"]
        print(
            f"{crop:38s} | {ch:5s} | PNG: {len(png):6d} bytes | Min: {min_k:6.1f} K | Mean: {mean_k:6.1f} K | Sym: {sym:.2f} | Area<200K: {c200:7.0f} km2"
        )
