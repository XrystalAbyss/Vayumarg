"""Quantitative Scientific Satellite Image Analytics Engine.

Computes rigorous physical observations and meteorological metrics from 201x201
calibrated INSAT satellite crops without ML or speculative inferences:
- Valid and missing pixel fractions.
- Lower LUT radiometric clamping detection and censoring distinction.
- Brightness temperature minimum among non-clamped valid pixels.
- Exact temperature percentiles (p10, p25, p50, p75, p90) and moments.
- Cold-cloud pixel fractions at justified, documented meteorological thresholds.
- Radial temperature profiles centered on cyclone eye fix.
- Spatial gradient and boundary sharpness statistics.
- Basic azimuthal cloud-field symmetry/asymmetry measures.
- Native sensor vs delivered product resolution preservation.
"""

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ThresholdFraction:
    """Cold-cloud pixel fraction for a scientifically justified temperature threshold."""

    threshold_k: float
    threshold_celsius: float
    pixel_count: int
    fraction_of_valid: float
    fraction_of_total: float
    scientific_justification: str


@dataclass(frozen=True)
class RadialBinStats:
    """Temperature statistics within a radial ring centered on the cyclone center."""

    bin_name: str
    radius_inner_km: float
    radius_outer_km: float
    valid_pixel_count: int
    mean_tb_k: float | None
    min_tb_k: float | None
    max_tb_k: float | None
    std_tb_k: float | None


@dataclass(frozen=True)
class GradientStats:
    """Spatial temperature gradient statistics across valid pixels."""

    mean_k_per_km: float
    median_k_per_km: float
    max_k_per_km: float
    p95_k_per_km: float
    computation_method: str = "2D central finite differences on valid neighbors"


@dataclass(frozen=True)
class CloudFieldSymmetry:
    """Azimuthal quadrant temperature distribution in the inner core region (<= 200 km)."""

    quadrant_means_k: dict[str, float]
    quadrant_cold_fractions: dict[str, float]
    azimuthal_std_k: float
    azimuthal_asymmetry_index: float
    core_radius_km: float = 200.0
    scientific_disclaimer: str = (
        "Basic physical cloud-field azimuthal distribution measure; "
        "does not represent a calibrated cyclone intensity predictor."
    )


@dataclass(frozen=True)
class ResolutionLineage:
    """Source sensor native resolution vs delivered product grid spacing."""

    native_instrument_resolution_km: float
    delivered_product_grid_spacing_km: float
    target_crop_grid_spacing_km: float
    effective_resolution_km: float
    resampling_method: str
    scientific_caveat: str | None


@dataclass(frozen=True)
class ChannelAnalytics:
    """Comprehensive scientific analytics package for a single satellite channel."""

    channel_name: str
    total_pixels: int
    valid_pixels: int
    valid_fraction: float
    missing_pixels: int
    missing_fraction: float
    clamped_pixels: int
    clamped_fraction: float
    lut_boundary_kelvin: float
    is_lut_censored: bool
    min_tb_k: float | None
    min_non_clamped_tb_k: float | None
    max_tb_k: float | None
    mean_tb_k: float | None
    std_tb_k: float | None
    percentiles_tb_k: dict[str, float]
    cold_cloud_fractions: list[ThresholdFraction]
    radial_profile: list[RadialBinStats]
    gradient_statistics: GradientStats
    symmetry_metrics: CloudFieldSymmetry
    resolution_lineage: ResolutionLineage

    def to_dict(self) -> dict[str, Any]:
        """Convert analytics dataclass to JSON-serializable dictionary."""
        return asdict(self)


# Meteorological Cold-Cloud Threshold Definitions with Scientific Justifications
COLD_CLOUD_THRESHOLDS = [
    (
        240.0,
        "General tropical cyclone anvil canopy and cirrus outflow shield (-33.15°C).",
    ),
    (
        220.0,
        "Standard deep convective cloud threshold corresponding to the Central Dense Overcast (CDO) boundary in operational Dvorak technique (-53.15°C).",
    ),
    (
        200.0,
        "Intense deep convection representing vigorous convective cores in tropical cyclone eyewall and inner rainbands (-73.15°C).",
    ),
    (
        190.0,
        "Extreme cold cloud tops near the tropical tropopause (-83.15°C; cautiously defined; not all cold pixels represent overshooting convective tops).",
    ),
]

# Standard radial ring boundaries (km) from cyclone eye center
RADIAL_BINS_KM = [
    (0.0, 25.0, "0-25 km (Eye / Inner Core)"),
    (25.0, 50.0, "25-50 km (Eyewall Ring)"),
    (50.0, 100.0, "50-100 km (Inner Rainbands)"),
    (100.0, 150.0, "100-150 km (Inner Spiral Bands)"),
    (150.0, 200.0, "150-200 km (Outer Convective Bands)"),
    (200.0, 300.0, "200-300 km (Outer Rainband Shield)"),
    (300.0, 400.0, "300-400 km (Peripheral Canopy)"),
]


class SatelliteImageAnalyticsEngine:
    """Engine for computing quantitative physical observations from satellite crops."""

    @classmethod
    def compute_channel_analytics(
        cls,
        channel_name: str,
        temps_k: np.ndarray,
        valid_mask: np.ndarray | None = None,
        clamped_mask: np.ndarray | None = None,
        grid_spacing_km: float = 4.0,
        native_resolution_km: float = 4.0,
        delivered_resolution_km: float = 4.0,
        resampling_method: str = "native/none",
        satellite_name: str = "INSAT-3DR",
        lut_boundary_kelvin: float = 179.86,
    ) -> ChannelAnalytics:
        """Compute comprehensive scientific analytics on a 2D brightness temperature array."""
        if temps_k.ndim != 2:
            raise ValueError(f"Expected 2D array, got shape {temps_k.shape}")

        h, w = temps_k.shape
        total_pixels = h * w

        # Build clean validity mask
        if valid_mask is not None:
            eff_valid = valid_mask & (~np.isnan(temps_k)) & (temps_k > 0.0)
        else:
            eff_valid = (~np.isnan(temps_k)) & (temps_k > 0.0)

        valid_count = int(np.sum(eff_valid))
        missing_count = total_pixels - valid_count
        valid_fraction = float(valid_count / total_pixels) if total_pixels > 0 else 0.0
        missing_fraction = float(missing_count / total_pixels) if total_pixels > 0 else 0.0

        # Clamping detection
        if clamped_mask is not None:
            clamped_on_valid = clamped_mask & eff_valid
        else:
            clamped_on_valid = (temps_k <= (lut_boundary_kelvin + 0.15)) & eff_valid

        clamped_count = int(np.sum(clamped_on_valid))
        clamped_fraction = float(clamped_count / valid_count) if valid_count > 0 else 0.0
        is_lut_censored = clamped_count > 0

        # Temperature statistics
        if valid_count > 0:
            valid_temps = temps_k[eff_valid]
            min_tb_k = float(np.min(valid_temps))
            max_tb_k = float(np.max(valid_temps))
            mean_tb_k = float(np.mean(valid_temps))
            std_tb_k = float(np.std(valid_temps))

            # Non-clamped valid temperatures
            non_clamped = eff_valid & (~clamped_on_valid)
            if np.any(non_clamped):
                min_non_clamped_tb_k = float(np.min(temps_k[non_clamped]))
            else:
                min_non_clamped_tb_k = None  # All valid pixels are at the LUT boundary

            # Percentiles on valid pixels
            percentiles = {
                "p10": float(np.percentile(valid_temps, 10)),
                "p25": float(np.percentile(valid_temps, 25)),
                "p50": float(np.percentile(valid_temps, 50)),
                "p75": float(np.percentile(valid_temps, 75)),
                "p90": float(np.percentile(valid_temps, 90)),
            }
        else:
            min_tb_k = None
            min_non_clamped_tb_k = None
            max_tb_k = None
            mean_tb_k = None
            std_tb_k = None
            percentiles = {"p10": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p90": 0.0}

        # Cold cloud threshold fractions
        cold_fractions: list[ThresholdFraction] = []
        for thresh_k, justification in COLD_CLOUD_THRESHOLDS:
            if valid_count > 0:
                cold_mask = eff_valid & (temps_k < thresh_k)
                cnt = int(np.sum(cold_mask))
                frac_valid = float(cnt / valid_count)
                frac_total = float(cnt / total_pixels)
            else:
                cnt = 0
                frac_valid = 0.0
                frac_total = 0.0

            cold_fractions.append(
                ThresholdFraction(
                    threshold_k=thresh_k,
                    threshold_celsius=round(thresh_k - 273.15, 2),
                    pixel_count=cnt,
                    fraction_of_valid=round(frac_valid, 6),
                    fraction_of_total=round(frac_total, 6),
                    scientific_justification=justification,
                )
            )

        # Radial temperature profile from center
        radial_stats = cls._compute_radial_profile(
            temps_k=temps_k,
            eff_valid=eff_valid,
            grid_spacing_km=grid_spacing_km,
        )

        # Gradient statistics
        grad_stats = cls._compute_gradients(
            temps_k=temps_k,
            eff_valid=eff_valid,
            grid_spacing_km=grid_spacing_km,
        )

        # Cloud-field symmetry
        symm_stats = cls._compute_symmetry(
            temps_k=temps_k,
            eff_valid=eff_valid,
            grid_spacing_km=grid_spacing_km,
        )

        # Resolution lineage and scientific caveat
        caveat = None
        if satellite_name == "INSAT-3DS" and channel_name == "WV":
            caveat = (
                "INSAT-3DS delivered WV product is sampled on a 4.0 km grid spacing, "
                "but native instrument spatial resolution is 8.0 km. "
                "Delivered grid must not be treated as 4.0 km independent physical sensor resolution."
            )
        elif native_resolution_km != grid_spacing_km:
            caveat = (
                f"Native sensor resolution is {native_resolution_km:.1f} km, "
                f"resampled to uniform {grid_spacing_km:.1f} km analysis grid spacing."
            )

        res_lineage = ResolutionLineage(
            native_instrument_resolution_km=native_resolution_km,
            delivered_product_grid_spacing_km=delivered_resolution_km,
            target_crop_grid_spacing_km=grid_spacing_km,
            effective_resolution_km=native_resolution_km,
            resampling_method=resampling_method,
            scientific_caveat=caveat,
        )

        return ChannelAnalytics(
            channel_name=channel_name,
            total_pixels=total_pixels,
            valid_pixels=valid_count,
            valid_fraction=round(valid_fraction, 6),
            missing_pixels=missing_count,
            missing_fraction=round(missing_fraction, 6),
            clamped_pixels=clamped_count,
            clamped_fraction=round(clamped_fraction, 6),
            lut_boundary_kelvin=lut_boundary_kelvin,
            is_lut_censored=is_lut_censored,
            min_tb_k=round(min_tb_k, 2) if min_tb_k is not None else None,
            min_non_clamped_tb_k=round(min_non_clamped_tb_k, 2)
            if min_non_clamped_tb_k is not None
            else None,
            max_tb_k=round(max_tb_k, 2) if max_tb_k is not None else None,
            mean_tb_k=round(mean_tb_k, 2) if mean_tb_k is not None else None,
            std_tb_k=round(std_tb_k, 2) if std_tb_k is not None else None,
            percentiles_tb_k={k: round(v, 2) for k, v in percentiles.items()},
            cold_cloud_fractions=cold_fractions,
            radial_profile=radial_stats,
            gradient_statistics=grad_stats,
            symmetry_metrics=symm_stats,
            resolution_lineage=res_lineage,
        )

    @classmethod
    def _compute_radial_profile(
        cls,
        temps_k: np.ndarray,
        eff_valid: np.ndarray,
        grid_spacing_km: float,
    ) -> list[RadialBinStats]:
        """Compute mean, min, max, std of temperature in radial rings from array center."""
        h, w = temps_k.shape
        cy, cx = (h - 1) / 2.0, (w - 1) / 2.0

        y_coords, x_coords = np.ogrid[:h, :w]
        dist_km = np.sqrt((y_coords - cy) ** 2 + (x_coords - cx) ** 2) * grid_spacing_km

        results: list[RadialBinStats] = []
        for r_in, r_out, name in RADIAL_BINS_KM:
            ring_mask = eff_valid & (dist_km >= r_in) & (dist_km < r_out)
            cnt = int(np.sum(ring_mask))
            if cnt > 0:
                ring_vals = temps_k[ring_mask]
                mean_v = float(np.mean(ring_vals))
                min_v = float(np.min(ring_vals))
                max_v = float(np.max(ring_vals))
                std_v = float(np.std(ring_vals))
            else:
                mean_v = min_v = max_v = std_v = None

            results.append(
                RadialBinStats(
                    bin_name=name,
                    radius_inner_km=r_in,
                    radius_outer_km=r_out,
                    valid_pixel_count=cnt,
                    mean_tb_k=round(mean_v, 2) if mean_v is not None else None,
                    min_tb_k=round(min_v, 2) if min_v is not None else None,
                    max_tb_k=round(max_v, 2) if max_v is not None else None,
                    std_tb_k=round(std_v, 2) if std_v is not None else None,
                )
            )
        return results

    @classmethod
    def _compute_gradients(
        cls,
        temps_k: np.ndarray,
        eff_valid: np.ndarray,
        grid_spacing_km: float,
    ) -> GradientStats:
        """Compute spatial temperature gradient magnitude using 2D central differences."""
        h, w = temps_k.shape
        if h < 3 or w < 3 or not np.any(eff_valid):
            return GradientStats(0.0, 0.0, 0.0, 0.0)

        # Central differences: dy and dx
        # Only valid where row-1, row+1, col-1, col+1 are all valid
        interior_valid = (
            eff_valid[1:-1, 1:-1]
            & eff_valid[:-2, 1:-1]
            & eff_valid[2:, 1:-1]
            & eff_valid[1:-1, :-2]
            & eff_valid[1:-1, 2:]
        )

        if not np.any(interior_valid):
            return GradientStats(0.0, 0.0, 0.0, 0.0)

        dy = (temps_k[2:, 1:-1] - temps_k[:-2, 1:-1]) / (2.0 * grid_spacing_km)
        dx = (temps_k[1:-1, 2:] - temps_k[1:-1, :-2]) / (2.0 * grid_spacing_km)

        grad_mag = np.sqrt(dy**2 + dx**2)[interior_valid]

        return GradientStats(
            mean_k_per_km=round(float(np.mean(grad_mag)), 3),
            median_k_per_km=round(float(np.median(grad_mag)), 3),
            max_k_per_km=round(float(np.max(grad_mag)), 3),
            p95_k_per_km=round(float(np.percentile(grad_mag, 95)), 3),
        )

    @classmethod
    def _compute_symmetry(
        cls,
        temps_k: np.ndarray,
        eff_valid: np.ndarray,
        grid_spacing_km: float,
        core_radius_km: float = 200.0,
    ) -> CloudFieldSymmetry:
        """Measure brightness temperature distribution across 4 inner core quadrants."""
        h, w = temps_k.shape
        cy, cx = (h - 1) / 2.0, (w - 1) / 2.0

        y_coords, x_coords = np.ogrid[:h, :w]
        dy = y_coords - cy  # positive = South (downwards)
        dx = x_coords - cx  # positive = East (rightwards)
        dist_km = np.sqrt(dy**2 + dx**2) * grid_spacing_km

        in_core = eff_valid & (dist_km <= core_radius_km)

        # Quadrants:
        # NE: y <= cy (North), x >= cx (East)
        # NW: y <= cy (North), x < cx (West)
        # SE: y > cy (South), x >= cx (East)
        # SW: y > cy (South), x < cx (West)
        quadrants = {
            "NE": in_core & (dy <= 0) & (dx >= 0),
            "NW": in_core & (dy <= 0) & (dx < 0),
            "SE": in_core & (dy > 0) & (dx >= 0),
            "SW": in_core & (dy > 0) & (dx < 0),
        }

        means: dict[str, float] = {}
        cold_fracs: dict[str, float] = {}
        q_mean_vals: list[float] = []

        for q_name, mask in quadrants.items():
            cnt = int(np.sum(mask))
            if cnt > 0:
                q_temps = temps_k[mask]
                m_val = float(np.mean(q_temps))
                means[q_name] = round(m_val, 2)
                q_mean_vals.append(m_val)
                # Cold cloud (< 220 K) fraction in this quadrant
                cold_frac = float(np.mean(q_temps < 220.0))
                cold_fracs[q_name] = round(cold_frac, 4)
            else:
                means[q_name] = 0.0
                cold_fracs[q_name] = 0.0

        if len(q_mean_vals) >= 2:
            azimuthal_std = float(np.std(q_mean_vals))
            mean_core = float(np.mean(q_mean_vals))
            # Normalized asymmetry index: (max_q - min_q) / mean_core
            asymmetry_index = float(
                (max(q_mean_vals) - min(q_mean_vals)) / (mean_core if mean_core > 0 else 1.0)
            )
        else:
            azimuthal_std = 0.0
            asymmetry_index = 0.0

        return CloudFieldSymmetry(
            quadrant_means_k=means,
            quadrant_cold_fractions=cold_fracs,
            azimuthal_std_k=round(azimuthal_std, 2),
            azimuthal_asymmetry_index=round(asymmetry_index, 4),
            core_radius_km=core_radius_km,
        )
