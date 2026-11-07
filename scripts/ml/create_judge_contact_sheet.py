"""Create a genuine 12-frame contact sheet of authentic NASA cyclone training images for judge audit."""

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IMG_DIR = PROJECT_ROOT / "data" / "raw" / "satellite" / "nasa_cyclone" / "images"
MANIFEST_CSV = PROJECT_ROOT / "data" / "processed" / "satellite" / "nasa_cyclone" / "dataset_manifest.csv"
OUT_PATH = PROJECT_ROOT / "hackathon" / "screenshots" / "nasa_training_dataset_contact_sheet.png"

df = pd.read_csv(MANIFEST_CSV)

# Select 12 diverse storms across the intensity spectrum from train/val/test
target_specs = [
    ("psz", 130.0, "high"),
    ("eoi", 110.0, "high"),
    ("kqu", 95.0, "med-high"),
    ("vxf", 85.0, "med-high"),
    ("fcr", 75.0, "med"),
    ("fna", 65.0, "med"),
    ("xjo", 55.0, "med-low"),
    ("gic", 45.0, "med-low"),
    ("ing", 40.0, "low"),
    ("blq", 35.0, "low"),
    ("rml", 30.0, "weak"),
    ("ojv", 25.0, "weak"),
]

selected_rows = []
for storm_id, target_w, _ in target_specs:
    storm_df = df[df["storm_id"] == storm_id]
    if not storm_df.empty:
        # find closest to target_w
        idx = (storm_df["wind_speed_knots"] - target_w).abs().idxmin()
        selected_rows.append(storm_df.loc[idx])

selected_df = pd.DataFrame(selected_rows)

print(f"Selected {len(selected_df)} authentic frames for contact sheet:")
for _, r in selected_df.iterrows():
    print(f"  [{r.split.upper()}] {r.storm_id} | {r.frame_id} | {r.wind_speed_knots} kt | t={r.relative_time_seconds}s")

# Create Contact Sheet: 4 columns x 3 rows
cols = 4
rows = 3
cell_w = 366
cell_h = 366
label_h = 74
pad = 16
header_h = 90

grid_w = cols * cell_w + (cols + 1) * pad
grid_h = header_h + rows * (cell_h + label_h) + (rows + 1) * pad

sheet = Image.new("RGB", (grid_w, grid_h), color=(11, 17, 27))
draw = ImageDraw.Draw(sheet)

# Try to load a nice font, otherwise default
try:
    font_title = ImageFont.truetype("arial.ttf", 26)
    font_subtitle = ImageFont.truetype("arial.ttf", 15)
    font_bold = ImageFont.truetype("arialbd.ttf", 15)
    font_meta = ImageFont.truetype("arial.ttf", 13)
    font_tiny = ImageFont.truetype("cour.ttf", 11)
except Exception:
    font_title = font_subtitle = font_bold = font_meta = font_tiny = ImageFont.load_default()

# Header
draw.rectangle([(0, 0), (grid_w, header_h)], fill=(17, 27, 40))
draw.line([(0, header_h), (grid_w, header_h)], fill=(30, 46, 66), width=2)

draw.text((pad, 16), "VAYUMARG — NASA Tropical Cyclone Wind Dataset Judge Audit", fill=(237, 243, 249), font=font_title)
draw.text(
    (pad, 50),
    "12 Genuine Geostationary Infrared Training Frames (366×366 px) • NASA IMPACT / NOAA GOES-16/17 ABI • Intensity Spectrum 25–144 kt",
    fill=(150, 168, 187),
    font=font_subtitle,
)

# Render Cells
for i, (_, r) in enumerate(selected_df.iterrows()):
    c = i % cols
    row = i // cols

    x = pad + c * (cell_w + pad)
    y = header_h + pad + row * (cell_h + label_h + pad)

    img_path = PROJECT_ROOT / r.image_path
    if not img_path.exists():
        print(f"Warning: image path missing: {img_path}")
        continue

    raw_img = Image.open(img_path).convert("RGB")

    # Paste image
    sheet.paste(raw_img, (x, y))
    draw.rectangle([(x, y), (x + cell_w - 1, y + cell_h - 1)], outline=(30, 46, 66), width=1)

    # Label Box below image
    ly = y + cell_h
    draw.rectangle([(x, ly), (x + cell_w - 1, ly + label_h - 1)], fill=(23, 35, 51), outline=(30, 46, 66), width=1)

    # Partition badge color
    split_color = (97, 186, 203) if r.split == "train" else ((231, 173, 101) if r.split == "val" else (160, 210, 120))

    # Text lines
    draw.text((x + 8, ly + 6), f"Storm: {r.storm_id.upper()} [{r.split.upper()}]", fill=split_color, font=font_bold)
    draw.text((x + 180, ly + 6), f"Label: {r.wind_speed_knots:.1f} kt", fill=(237, 243, 249), font=font_bold)

    time_hr = r.relative_time_seconds / 3600.0
    draw.text((x + 8, ly + 28), f"Relative Time: {r.relative_time_seconds:,}s (+{time_hr:.1f}h) | Basin: {r.ocean_basin}", fill=(150, 168, 187), font=font_meta)

    short_id = r.frame_id.replace("nasa_tropical_storm_competition_train_source_", "")
    draw.text((x + 8, ly + 48), f"ID: {short_id} ({raw_img.width}x{raw_img.height} IR)", fill=(97, 186, 203), font=font_tiny)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
sheet.save(OUT_PATH, format="PNG")
print(f"Successfully generated contact sheet at: {OUT_PATH} ({sheet.size[0]}x{sheet.size[1]} px, {OUT_PATH.stat().st_size:,} bytes)")

