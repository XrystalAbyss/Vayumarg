"""Scientific Satellite Visualization and Colormapping Engine.

Provides meteorologically sound, physical Kelvin-preserving color rendering for
multi-spectral INSAT satellite observations (TIR-1, TIR-2, WV, MIR).
Features:
- Physical Kelvin preservation: does not invent arbitrary colors or unphysical ranges.
- Explicit masking: invalid/missing/fill/NaN pixels are masked with alpha=0 or distinct fill.
- LUT lower-boundary clamping indication.
- Standard scientific meteorological palettes:
    * `thermal_ir`: continuous, physically grounded thermal enhancement palette.
    * `grayscale_inv`: standard satellite inverted IR (cold = bright/white, warm = dark).
    * `dvorak_bd`: official Dvorak Bending (BD) curve step enhancement.
    * `water_vapor`: upper-tropospheric humidity and convective moisture enhancement.
- Measurement colorbar and legend generation with visible Kelvin and Celsius units.
- Fast, pure NumPy + Pillow raster rendering to PNG and WebP formats.
"""

import io
from dataclasses import dataclass
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw

# Supported colormap identifiers
ColormapType = Literal["thermal_ir", "grayscale_inv", "dvorak_bd", "water_vapor"]
SUPPORTED_COLORMAPS: list[str] = ["thermal_ir", "grayscale_inv", "dvorak_bd", "water_vapor"]

# Temperature range standards for thermal infrared channels (Kelvin)
IR_TEMP_MIN_K = 180.0
IR_TEMP_MAX_K = 310.0

# Water vapor channel temperature range standards (Kelvin)
WV_TEMP_MIN_K = 190.0
WV_TEMP_MAX_K = 270.0


@dataclass(frozen=True)
class LegendTick:
    """Quantitative tick mark on a scientific measurement legend."""

    kelvin: float
    celsius: float
    hex_color: str
    description: str


@dataclass(frozen=True)
class ColormapSpec:
    """Colormap specification with physical domain and reference legend ticks."""

    name: str
    display_name: str
    channel_affinity: str
    temp_min_k: float
    temp_max_k: float
    ticks: list[LegendTick]
    scientific_description: str


def _interpolate_palette(
    t_norm: np.ndarray,
    anchors: list[tuple[float, tuple[int, int, int]]],
) -> np.ndarray:
    """Interpolate RGB channels linearly between normalized temperature anchor points."""
    pos = [a[0] for a in anchors]
    r_vals = [a[1][0] for a in anchors]
    g_vals = [a[1][1] for a in anchors]
    b_vals = [a[1][2] for a in anchors]

    clean_t = np.nan_to_num(t_norm, nan=0.0)
    r = np.interp(clean_t, pos, r_vals).astype(np.uint8)
    g = np.interp(clean_t, pos, g_vals).astype(np.uint8)
    b = np.interp(clean_t, pos, b_vals).astype(np.uint8)
    return np.stack([r, g, b], axis=-1)


# Anchor tables for continuous scientific thermal palette [180.0 K to 310.0 K]
_THERMAL_IR_ANCHORS = [
    (0.00, (255, 255, 255)),  # 180.0 K: Pure White (Extreme cold / CDO top)
    (0.04, (255, 230, 255)),  # ~185 K: Brightest Pink
    (0.12, (230, 0, 230)),  # ~195 K: Vivid Magenta (Vigorous deep convection)
    (0.23, (0, 220, 255)),  # ~210 K: Bright Cyan
    (0.31, (0, 100, 220)),  # ~220 K: Deep Blue (Deep convective threshold)
    (0.42, (0, 175, 75)),  # ~235 K: Emerald Green
    (0.54, (240, 220, 0)),  # ~250 K: Bright Yellow (Cirrus anvil shield)
    (0.65, (255, 130, 0)),  # ~265 K: Warm Orange
    (0.77, (215, 35, 10)),  # ~280 K: Deep Red
    (0.88, (90, 30, 30)),  # ~295 K: Warm Brown
    (1.00, (20, 20, 25)),  # 310.0 K: Dark Charcoal / Warm ocean surface
]

# Anchor tables for Water Vapor moisture palette [190.0 K to 270.0 K]
_WATER_VAPOR_ANCHORS = [
    (0.00, (240, 250, 255)),  # 190.0 K: Crisp Ice White (Saturated deep core)
    (0.15, (0, 230, 255)),  # ~202 K: Cyan (Very high moisture / active clouds)
    (0.35, (0, 120, 235)),  # ~218 K: Deep Sky Blue (High tropospheric humidity)
    (0.55, (30, 60, 180)),  # ~234 K: Royal Blue (Moderate tropospheric moisture)
    (0.75, (200, 120, 20)),  # ~250 K: Amber (Dry air / subsidence zone)
    (1.00, (70, 25, 5)),  # 270.0 K: Deep Bronze (Severe dry air / subsidence)
]


def _apply_thermal_ir(arr_k: np.ndarray) -> np.ndarray:
    """Render physical Kelvin array into RGB using continuous thermal IR palette."""
    t_norm = np.clip((arr_k - IR_TEMP_MIN_K) / (IR_TEMP_MAX_K - IR_TEMP_MIN_K), 0.0, 1.0)
    return _interpolate_palette(t_norm, _THERMAL_IR_ANCHORS)


def _apply_grayscale_inv(arr_k: np.ndarray) -> np.ndarray:
    """Render physical Kelvin array into standard inverted grayscale (cold=bright)."""
    t_norm = np.clip((arr_k - IR_TEMP_MIN_K) / (IR_TEMP_MAX_K - IR_TEMP_MIN_K), 0.0, 1.0)
    val = ((1.0 - t_norm) * 255.0).astype(np.uint8)
    return np.stack([val, val, val], axis=-1)


def _apply_dvorak_bd(arr_k: np.ndarray) -> np.ndarray:
    """Render physical Kelvin array into official Dvorak BD enhancement steps."""
    # Temperatures in Kelvin corresponding to WMO/NOAA Dvorak BD curve
    r = np.zeros(arr_k.shape, dtype=np.uint8)
    g = np.zeros(arr_k.shape, dtype=np.uint8)
    b = np.zeros(arr_k.shape, dtype=np.uint8)

    # > 282.15 K (+9°C): Warm background ocean / land -> Dark Gray
    mask_warm = arr_k >= 282.15
    r[mask_warm], g[mask_warm], b[mask_warm] = 40, 40, 45

    # 243.15 to 282.15 K (-30°C to +9°C): Low clouds / medium background -> Medium Dark Gray
    mask_low = (arr_k >= 243.15) & (arr_k < 282.15)
    r[mask_low], g[mask_low], b[mask_low] = 100, 100, 105

    # 232.15 to 243.15 K (-41°C to -30°C): Light Gray (CDO outer edge)
    mask_lg = (arr_k >= 232.15) & (arr_k < 243.15)
    r[mask_lg], g[mask_lg], b[mask_lg] = 185, 185, 190

    # 220.15 to 232.15 K (-53°C to -41°C): Dark Gray
    mask_dg = (arr_k >= 220.15) & (arr_k < 232.15)
    r[mask_dg], g[mask_dg], b[mask_dg] = 70, 70, 75

    # 209.15 to 220.15 K (-64°C to -53°C): Black (B step)
    mask_b = (arr_k >= 209.15) & (arr_k < 220.15)
    r[mask_b], g[mask_b], b[mask_b] = 15, 15, 20

    # 203.15 to 209.15 K (-70°C to -64°C): White (W step)
    mask_w = (arr_k >= 203.15) & (arr_k < 209.15)
    r[mask_w], g[mask_w], b[mask_w] = 250, 250, 255

    # 197.15 to 203.15 K (-76°C to -70°C): Medium Gray (M step)
    mask_m = (arr_k >= 197.15) & (arr_k < 203.15)
    r[mask_m], g[mask_m], b[mask_m] = 145, 145, 150

    # 193.15 to 197.15 K (-80°C to -76°C): Cold Dark Gray (CDG step)
    mask_cdg = (arr_k >= 193.15) & (arr_k < 197.15)
    r[mask_cdg], g[mask_cdg], b[mask_cdg] = 30, 30, 35

    # < 193.15 K (< -80°C): Pure White (Extreme Coldest Core / Overshooting Tops)
    mask_extreme = arr_k < 193.15
    r[mask_extreme], g[mask_extreme], b[mask_extreme] = 255, 255, 255

    return np.stack([r, g, b], axis=-1)


def _apply_water_vapor(arr_k: np.ndarray) -> np.ndarray:
    """Render physical Kelvin array into upper-tropospheric WV moisture palette."""
    t_norm = np.clip((arr_k - WV_TEMP_MIN_K) / (WV_TEMP_MAX_K - WV_TEMP_MIN_K), 0.0, 1.0)
    return _interpolate_palette(t_norm, _WATER_VAPOR_ANCHORS)


# Colormap catalog with explicit meteorological documentation and tick marks
COLORMAP_SPECS: dict[str, ColormapSpec] = {
    "thermal_ir": ColormapSpec(
        name="thermal_ir",
        display_name="Continuous Thermal IR",
        channel_affinity="TIR-1, TIR-2, MIR",
        temp_min_k=IR_TEMP_MIN_K,
        temp_max_k=IR_TEMP_MAX_K,
        ticks=[
            LegendTick(180.0, -93.15, "#FFFFFF", "Extreme convective cloud top / sensor floor"),
            LegendTick(195.0, -78.15, "#E600E6", "Vigorous deep convection (< -75°C)"),
            LegendTick(210.0, -63.15, "#00DCFF", "Deep convective cloud canopy (< -60°C)"),
            LegendTick(220.0, -53.15, "#0064DC", "CDO boundary / convective threshold (< -53°C)"),
            LegendTick(240.0, -33.15, "#00AF4B", "Convective anvil / cirrus shield"),
            LegendTick(260.0, -13.15, "#FF8200", "Mid-level clouds / tropospheric air"),
            LegendTick(280.0, 6.85, "#D7230A", "Low stratocumulus / shallow clouds"),
            LegendTick(300.0, 26.85, "#5A1E1E", "Warm ocean surface / sea-surface skin"),
            LegendTick(310.0, 36.85, "#141419", "Tropical land surface / clear sea"),
        ],
        scientific_description="Perceptually continuous meteorological thermal infrared palette preserving physical brightness temperatures from 180 K to 310 K.",
    ),
    "grayscale_inv": ColormapSpec(
        name="grayscale_inv",
        display_name="Standard Inverted Grayscale IR",
        channel_affinity="TIR-1, TIR-2, MIR, WV",
        temp_min_k=IR_TEMP_MIN_K,
        temp_max_k=IR_TEMP_MAX_K,
        ticks=[
            LegendTick(180.0, -93.15, "#FFFFFF", "White: cold high convective tops (180 K)"),
            LegendTick(220.0, -53.15, "#AAAAAA", "Light gray: deep convection (< -53°C)"),
            LegendTick(260.0, -13.15, "#666666", "Medium gray: mid-level clouds"),
            LegendTick(310.0, 36.85, "#000000", "Black: warm ocean / surface (310 K)"),
        ],
        scientific_description="Classical meteorological satellite inverted grayscale: cold cloud tops appear brightest white, warm tropical ocean appears black.",
    ),
    "dvorak_bd": ColormapSpec(
        name="dvorak_bd",
        display_name="Dvorak BD Enhancement Curve",
        channel_affinity="TIR-1",
        temp_min_k=IR_TEMP_MIN_K,
        temp_max_k=IR_TEMP_MAX_K,
        ticks=[
            LegendTick(193.15, -80.0, "#FFFFFF", "White: < -80°C extreme convective tops"),
            LegendTick(197.15, -76.0, "#1E1E23", "CDG: -76°C to -80°C (Cold Dark Gray)"),
            LegendTick(203.15, -70.0, "#919196", "M: -70°C to -76°C (Medium Gray)"),
            LegendTick(209.15, -64.0, "#FAFAFF", "W: -64°C to -70°C (White)"),
            LegendTick(220.15, -53.0, "#0F0F14", "B: -53°C to -64°C (Black)"),
            LegendTick(232.15, -41.0, "#46464B", "DG: -41°C to -53°C (Dark Gray)"),
            LegendTick(243.15, -30.0, "#B9B9BE", "LG: -30°C to -41°C (Light Gray - CDO)"),
            LegendTick(282.15, 9.0, "#646469", "Medium: -30°C to +9°C (Low clouds)"),
            LegendTick(310.0, 36.85, "#28282D", "Dark: > +9°C warm background surface"),
        ],
        scientific_description="Standard WMO/NOAA Dvorak Bending (BD) temperature step enhancement curve used worldwide for operational tropical cyclone intensity estimation.",
    ),
    "water_vapor": ColormapSpec(
        name="water_vapor",
        display_name="Upper Tropospheric Water Vapor",
        channel_affinity="WV",
        temp_min_k=WV_TEMP_MIN_K,
        temp_max_k=WV_TEMP_MAX_K,
        ticks=[
            LegendTick(190.0, -83.15, "#F0FAFF", "Moist saturated convective core"),
            LegendTick(205.0, -68.15, "#00E6FF", "High upper-level humidity / outflow"),
            LegendTick(220.0, -53.15, "#0078EB", "Moderate upper-tropospheric moisture"),
            LegendTick(240.0, -33.15, "#1E3CB4", "Deep tropospheric background moisture"),
            LegendTick(255.0, -18.15, "#C87814", "Dry air intrusion / subsidence band"),
            LegendTick(270.0, -3.15, "#461905", "Severe upper-level subsidence (Warm WV)"),
        ],
        scientific_description="Specialized water vapor absorption band palette highlighting convective moisture plumes, tropospheric humidity, and dry air intrusions.",
    ),
}


class SatelliteVisualizer:
    """Scientific visualizer for physical satellite arrays."""

    @classmethod
    def render_array(
        cls,
        arr_k: np.ndarray,
        valid_mask: np.ndarray | None = None,
        clamped_mask: np.ndarray | None = None,
        colormap: ColormapType = "thermal_ir",
        highlight_clamped: bool = False,
    ) -> Image.Image:
        """Render a 2D physical Kelvin array into an RGBA PIL Image.

        Rules strictly observed:
        - NaNs and invalid pixels are rendered with alpha=0 (transparent), NEVER as 0 K.
        - Clamping boundaries are optionally bordered/highlighted if requested.
        - Preserves exact 1:1 pixel grid geometry.
        """
        if arr_k.ndim != 2:
            raise ValueError(f"Expected 2D array, got ndim={arr_k.ndim}")

        h, w = arr_k.shape
        clean_arr = arr_k.copy().astype(float)

        # Build effective validity mask
        if valid_mask is not None:
            eff_valid = valid_mask & (~np.isnan(clean_arr))
        else:
            eff_valid = ~np.isnan(clean_arr)

        # Apply colormap mapping
        if colormap == "grayscale_inv":
            rgb = _apply_grayscale_inv(clean_arr)
        elif colormap == "dvorak_bd":
            rgb = _apply_dvorak_bd(clean_arr)
        elif colormap == "water_vapor":
            rgb = _apply_water_vapor(clean_arr)
        else:
            rgb = _apply_thermal_ir(clean_arr)

        # Construct RGBA buffer
        alpha = np.full((h, w), 255, dtype=np.uint8)
        alpha[~eff_valid] = 0  # Invalid pixels strictly transparent

        if highlight_clamped and clamped_mask is not None:
            # Highlight LUT clamped boundary pixels with bright magenta border
            clamped_on_valid = clamped_mask & eff_valid
            rgb[clamped_on_valid] = [255, 0, 128]

        rgba = np.dstack([rgb, alpha])
        return Image.fromarray(rgba, mode="RGBA")

    @classmethod
    def render_to_bytes(
        cls,
        arr_k: np.ndarray,
        valid_mask: np.ndarray | None = None,
        clamped_mask: np.ndarray | None = None,
        colormap: ColormapType = "thermal_ir",
        output_format: Literal["PNG", "WEBP"] = "PNG",
        highlight_clamped: bool = False,
    ) -> bytes:
        """Render array directly to compressed image bytes (PNG or WebP)."""
        img = cls.render_array(
            arr_k=arr_k,
            valid_mask=valid_mask,
            clamped_mask=clamped_mask,
            colormap=colormap,
            highlight_clamped=highlight_clamped,
        )
        buf = io.BytesIO()
        if output_format.upper() == "WEBP":
            img.save(buf, format="WEBP", lossless=True)
        else:
            img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    @classmethod
    def render_colorbar_legend(
        cls,
        colormap: ColormapType = "thermal_ir",
        width: int = 500,
        height: int = 65,
    ) -> Image.Image:
        """Render a standalone scientific measurement colorbar legend with Kelvin scale."""
        spec = COLORMAP_SPECS.get(colormap, COLORMAP_SPECS["thermal_ir"])
        t_min, t_max = spec.temp_min_k, spec.temp_max_k

        # 1. Background image
        img = Image.new("RGBA", (width, height), (26, 32, 44, 255))  # Dark slate background
        draw = ImageDraw.Draw(img)

        # 2. Gradient bar dimensions
        margin_left = min(30, max(8, width // 10))
        margin_right = margin_left
        bar_top = 22
        bar_height = 16
        bar_width = max(10, width - margin_left - margin_right)

        # Generate sample temperatures across width
        sample_temps = np.linspace(t_min, t_max, bar_width).reshape(1, bar_width)
        bar_img = cls.render_array(sample_temps, colormap=colormap)
        bar_resized = bar_img.resize((bar_width, bar_height), resample=Image.Resampling.NEAREST)
        img.paste(bar_resized, (margin_left, bar_top))

        # Border around colorbar
        draw.rectangle(
            [margin_left, bar_top, margin_left + bar_width, bar_top + bar_height],
            outline=(100, 116, 139, 255),
            width=1,
        )

        # 3. Colormap Title & Units
        title_text = f"{spec.display_name} [Kelvin (K)]"
        draw.text((margin_left, 6), title_text, fill=(226, 232, 240, 255))

        # 4. Tick marks and labels
        tick_kelvins = [t.kelvin for t in spec.ticks if t_min <= t.kelvin <= t_max]
        for tk in tick_kelvins:
            t_ratio = (tk - t_min) / (t_max - t_min)
            x_pos = int(margin_left + t_ratio * bar_width)

            # Draw tick line
            draw.line(
                [(x_pos, bar_top + bar_height), (x_pos, bar_top + bar_height + 4)],
                fill=(203, 213, 225, 255),
                width=1,
            )

            # Text label: Kelvin value
            txt = f"{int(round(tk))}K"
            # Offset slightly left so text centers under tick
            text_x = max(2, x_pos - 10)
            draw.text((text_x, bar_top + bar_height + 6), txt, fill=(203, 213, 225, 255))

        return img

    @classmethod
    def render_composite_preview(
        cls,
        arr_k: np.ndarray,
        storm_name: str,
        channel_name: str,
        satellite: str,
        valid_mask: np.ndarray | None = None,
        clamped_mask: np.ndarray | None = None,
        colormap: ColormapType = "thermal_ir",
        native_res_km: float = 4.0,
        extent_km: float = 800.0,
    ) -> Image.Image:
        """Render complete scientific visual preview card containing the image and annotated measurement scale."""
        main_img = cls.render_array(
            arr_k=arr_k,
            valid_mask=valid_mask,
            clamped_mask=clamped_mask,
            colormap=colormap,
        )
        total_w = max(main_img.width, 320)
        legend_img = cls.render_colorbar_legend(colormap=colormap, width=total_w, height=60)

        # Header height
        header_h = 36
        total_h = header_h + main_img.height + legend_img.height

        composite = Image.new("RGBA", (total_w, total_h), (15, 23, 42, 255))
        draw = ImageDraw.Draw(composite)

        # Header info
        header_text = f"{storm_name} | {channel_name} ({native_res_km:.1f}km) | {satellite}"
        draw.text((8, 6), header_text, fill=(248, 250, 252, 255))
        extent_text = f"Extent: {extent_km:.0f}km"
        draw.text((8, 20), extent_text, fill=(148, 163, 184, 255))

        # Paste main raster centered horizontally and legend
        x_offset = (total_w - main_img.width) // 2
        composite.paste(main_img, (x_offset, header_h))
        composite.paste(legend_img, (0, header_h + main_img.height))

        return composite
