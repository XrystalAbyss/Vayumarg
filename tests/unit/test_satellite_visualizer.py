"""Unit tests for scientific satellite visualizer and colormapping engine."""

import numpy as np

from vayumarg.satellite.visualizer import (
    COLORMAP_SPECS,
    SatelliteVisualizer,
)


def test_supported_colormaps_exist():
    """Verify that all required scientific colormaps are registered and documented."""
    required = ["thermal_ir", "grayscale_inv", "dvorak_bd", "water_vapor"]
    for cm in required:
        assert cm in COLORMAP_SPECS
        spec = COLORMAP_SPECS[cm]
        assert spec.temp_min_k < spec.temp_max_k
        assert len(spec.ticks) > 0
        assert spec.scientific_description


def test_grayscale_inv_kelvin_mapping():
    """Verify standard inverted infrared grayscale: 180K = white (255), 310K = black (0)."""
    # 180 K -> Pure white
    arr_cold = np.full((10, 10), 180.0)
    img_cold = SatelliteVisualizer.render_array(arr_cold, colormap="grayscale_inv")
    data_cold = np.array(img_cold)
    assert np.all(data_cold[:, :, :3] == 255)
    assert np.all(data_cold[:, :, 3] == 255)

    # 310 K -> Pure black
    arr_warm = np.full((10, 10), 310.0)
    img_warm = SatelliteVisualizer.render_array(arr_warm, colormap="grayscale_inv")
    data_warm = np.array(img_warm)
    assert np.all(data_warm[:, :, :3] == 0)
    assert np.all(data_warm[:, :, 3] == 255)


def test_invalid_pixels_masked_as_transparent():
    """Verify invalid/fill/NaN pixels have alpha=0 and are NEVER rendered as valid temperature."""
    arr = np.full((20, 20), 250.0)
    arr[5:10, 5:10] = np.nan

    valid_mask = np.ones((20, 20), dtype=bool)
    valid_mask[12:16, 12:16] = False

    img = SatelliteVisualizer.render_array(arr, valid_mask=valid_mask, colormap="thermal_ir")
    rgba = np.array(img)

    # NaN region must have alpha=0
    assert np.all(rgba[5:10, 5:10, 3] == 0)
    # Masked region must have alpha=0
    assert np.all(rgba[12:16, 12:16, 3] == 0)
    # Valid region must have alpha=255
    assert rgba[0, 0, 3] == 255


def test_clamped_boundary_highlighting():
    """Verify lower LUT clamping pixels can be distinctly flagged and highlighted."""
    arr = np.full((20, 20), 220.0)
    clamped_mask = np.zeros((20, 20), dtype=bool)
    clamped_mask[2:5, 2:5] = True

    # Without highlight
    img_normal = SatelliteVisualizer.render_array(
        arr, clamped_mask=clamped_mask, highlight_clamped=False
    )
    # With highlight
    img_highlight = SatelliteVisualizer.render_array(
        arr, clamped_mask=clamped_mask, highlight_clamped=True
    )

    arr_normal = np.array(img_normal)
    arr_hl = np.array(img_highlight)

    # The clamped pixels should differ when highlighted
    assert not np.array_equal(arr_normal[2:5, 2:5, :3], arr_hl[2:5, 2:5, :3])
    # The unclamped pixels should remain identical
    assert np.array_equal(arr_normal[10:15, 10:15], arr_hl[10:15, 10:15])


def test_dvorak_bd_curve_temperature_steps():
    """Verify Dvorak BD curve distinct step intervals."""
    # < 193.15 K (-80C) must be pure white
    extreme = np.array([[190.0]])
    img_ext = SatelliteVisualizer.render_array(extreme, colormap="dvorak_bd")
    assert tuple(np.array(img_ext)[0, 0, :3]) == (255, 255, 255)

    # 209.15 to 220.15 K (-53C to -64C) is Black (B step)
    b_step = np.array([[215.0]])
    img_b = SatelliteVisualizer.render_array(b_step, colormap="dvorak_bd")
    rgb_b = tuple(np.array(img_b)[0, 0, :3])
    assert rgb_b[0] < 30 and rgb_b[1] < 30 and rgb_b[2] < 30


def test_render_to_bytes_png_and_webp():
    """Verify PNG and WebP byte generation from 2D physical arrays."""
    arr = np.linspace(180.0, 310.0, 100).reshape(10, 10)
    png_bytes = SatelliteVisualizer.render_to_bytes(arr, colormap="thermal_ir", output_format="PNG")
    assert len(png_bytes) > 0
    # Verify valid PNG signature
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    webp_bytes = SatelliteVisualizer.render_to_bytes(
        arr, colormap="thermal_ir", output_format="WEBP"
    )
    assert len(webp_bytes) > 0
    # Verify valid RIFF WEBP signature
    assert webp_bytes.startswith(b"RIFF") and b"WEBP" in webp_bytes[:16]


def test_colorbar_legend_and_composite_render():
    """Verify measurement colorbar legend and composite preview rendering."""
    legend = SatelliteVisualizer.render_colorbar_legend("thermal_ir", width=300, height=50)
    assert legend.size == (300, 50)
    assert legend.mode == "RGBA"

    arr = np.full((50, 50), 230.0)
    composite = SatelliteVisualizer.render_composite_preview(
        arr, "REMAL", "TIR-1", "INSAT-3DR", extent_km=800.0
    )
    assert composite.width >= 50
    assert composite.height > 50  # Must include header + raster + legend
