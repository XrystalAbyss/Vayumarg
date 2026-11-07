"""Generate a professional scientific training pipeline diagram for VAYUMARG hackathon evidence."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = PROJECT_ROOT / "hackathon" / "screenshots" / "training_pipeline.png"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Diagram Dimensions
w, h = 1600, 800
img = Image.new("RGB", (w, h), color=(11, 17, 27))
draw = ImageDraw.Draw(img)

# Try loading fonts
try:
    font_title = ImageFont.truetype("arialbd.ttf", 26)
    font_sub = ImageFont.truetype("arial.ttf", 15)
    font_box_title = ImageFont.truetype("arialbd.ttf", 16)
    font_box_body = ImageFont.truetype("arial.ttf", 12)
    font_pill = ImageFont.truetype("arialbd.ttf", 11)
    font_arrow = ImageFont.truetype("arialbd.ttf", 18)
except Exception:
    font_title = font_sub = font_box_title = font_box_body = font_pill = font_arrow = (
        ImageFont.load_default()
    )

# 1. Header Banner
draw.rectangle([(0, 0), (w, 85)], fill=(17, 27, 40))
draw.line([(0, 85), (w, 85)], fill=(30, 46, 66), width=2)
draw.text(
    (30, 16),
    "VAYUMARG — End-to-End Satellite Vision ML Training & Inference Pipeline",
    fill=(237, 243, 249),
    font=font_title,
)
draw.text(
    (30, 50),
    "Authentic NASA GOES Infrared Benchmark Data Flow • Mixed Precision Training on RTX 4050 GPU • Cryptographic Release Gates",
    fill=(150, 168, 187),
    font=font_sub,
)

# Stage Box Definitions: 2 Rows x 4 Stages = 8 Pipeline Stages
stages = [
    # Top Row: Data Ingestion & Preprocessing
    {
        "x": 40,
        "y": 120,
        "w": 330,
        "h": 260,
        "step": "STAGE 1",
        "title": "NASA Source Imagery",
        "badge": "2,500 FRAMES",
        "badge_color": (97, 186, 203),
        "items": [
            "• NASA IMPACT / DrivenData Benchmark",
            "• NOAA GOES-16/17 ABI Band 14 (11.2 µm)",
            "• 25 Unique Tropical Cyclones",
            "• 366×366 Native Spatial Resolution",
            "• Clean Grayscale (Mode L)",
            "• 43.99 MB NVMe Local Cache",
        ],
    },
    {
        "x": 430,
        "y": 120,
        "w": 330,
        "h": 260,
        "step": "STAGE 2",
        "title": "Metadata & Partitioning",
        "badge": "STORM-DISJOINT",
        "badge_color": (231, 173, 101),
        "items": [
            "• dataset_manifest.csv & .json",
            "• Train: 15 storms (1,619 frames)",
            "• Val: 5 storms (467 frames)",
            "• Test: 5 storms (414 frames)",
            "• Labels: 1-min Sustained Wind (kt)",
            "• Zero Storm Overlap (Leakage Free)",
        ],
    },
    {
        "x": 820,
        "y": 120,
        "w": 330,
        "h": 260,
        "step": "STAGE 3",
        "title": "Scientific Preprocessing",
        "badge": "NORMALIZED",
        "badge_color": (160, 210, 120),
        "items": [
            "• Resize: 128×128 (Train) / 224×224 (Eval)",
            "• Tensor Scale: uint8 [0,255] -> [0.0,1.0]",
            "• Normalization: µ=0.45, σ=0.22 (TIR)",
            "• Train Flips: Random H/V (p=0.5)",
            "• Sequence Sliding Window (T=3 frames)",
            "• 6-Class Categorical Binning",
        ],
    },
    {
        "x": 1210,
        "y": 120,
        "w": 350,
        "h": 260,
        "step": "STAGE 4",
        "title": "PyTorch DataLoaders",
        "badge": "ZERO LATENCY",
        "badge_color": (97, 186, 203),
        "items": [
            "• CycloneImageDataset & SequenceDataset",
            "• Batch Size: 32 (51 batches / epoch)",
            "• Pin Memory: True for CUDA Streaming",
            "• Fast NVMe Storage Reading",
            "• Non-blocking GPU Memory Transfer",
            "• Deterministic Val/Test Generators",
        ],
    },
    # Bottom Row: Model Architectures, Training, Checkpoints, Inference
    {
        "x": 40,
        "y": 450,
        "w": 330,
        "h": 270,
        "step": "STAGE 5",
        "title": "Dual Architectures",
        "badge": "ResNet18 & ConvLSTM",
        "badge_color": (231, 173, 101),
        "items": [
            "• ResNet-18 IR: 11.27M Trainable Params",
            "  - 1-channel stem (mean RGB transfer)",
            "  - Huber Regression + Cross-Entropy",
            "• ConvLSTM Forecaster: 360K Params",
            "  - 2-layer ConvLSTM (32 -> 64 filters)",
            "  - Next-frame reconstruction decoder",
        ],
    },
    {
        "x": 430,
        "y": 450,
        "w": 330,
        "h": 270,
        "step": "STAGE 6",
        "title": "GPU Training Execution",
        "badge": "RTX 4050 • 71.35s",
        "badge_color": (160, 210, 120),
        "items": [
            "• NVIDIA GeForce RTX 4050 6GB VRAM",
            "• Mixed Precision (torch.amp.autocast)",
            "• AdamW (lr=5e-4) + CosineAnnealingLR",
            "• CNN Fit Duration: 71.35 seconds (15 ep)",
            "• ConvLSTM Fit Duration: 182.08s (12 ep)",
            "• Peak VRAM: < 1.2 GB (High Efficiency)",
        ],
    },
    {
        "x": 820,
        "y": 450,
        "w": 330,
        "h": 270,
        "step": "STAGE 7",
        "title": "Model Checkpoints",
        "badge": "SHA-256 AUDITED",
        "badge_color": (97, 186, 203),
        "items": [
            "• satellite_cnn_best.pt (129.16 MB)",
            "  SHA256: 2613a63cac762151...",
            "  Held-out Test MAE: 10.00 kt (r=0.864)",
            "• satellite_convlstm_best.pt (4.15 MB)",
            "  SHA256: 007aa5233373dbcc...",
            "  Frame Reconstruction MSE: 0.01084",
        ],
    },
    {
        "x": 1210,
        "y": 450,
        "w": 350,
        "h": 270,
        "step": "STAGE 8",
        "title": "FastAPI Inference Engine",
        "badge": "RELEASE GATES",
        "badge_color": (160, 210, 120),
        "items": [
            "• routes_ml.py & SatelliteInferenceEngine",
            "• Lazy-loaded GPU model weights",
            "• Post /api/ml/infer/satellite_cnn (<5ms)",
            "• Post /api/ml/infer/convlstm (live base64)",
            "• Cryptographic release gate checks",
            "• Cross-sensor INSAT evaluation: 12.2 kt",
        ],
    },
]

# Draw Stages
for s in stages:
    x, y, bw, bh = s["x"], s["y"], s["w"], s["h"]
    # Outer box
    draw.rectangle([(x, y), (x + bw, y + bh)], fill=(17, 27, 40), outline=(30, 46, 66), width=1)
    # Header bar
    draw.rectangle([(x, y), (x + bw, y + 42)], fill=(23, 35, 51))
    draw.line([(x, y + 42), (x + bw, y + 42)], fill=(30, 46, 66), width=1)

    # Step label & Title
    draw.text((x + 12, y + 6), s["step"], fill=(97, 186, 203), font=font_pill)
    draw.text((x + 12, y + 20), s["title"], fill=(237, 243, 249), font=font_box_title)

    # Badge on right
    bw_badge = draw.textlength(s["badge"], font=font_pill) + 12
    bx = x + bw - bw_badge - 12
    by = y + 10
    draw.rectangle(
        [(bx, by), (bx + bw_badge, by + 20)], fill=(11, 17, 27), outline=s["badge_color"], width=1
    )
    draw.text((bx + 6, by + 3), s["badge"], fill=s["badge_color"], font=font_pill)

    # Body items
    iy = y + 54
    for line in s["items"]:
        color = (237, 243, 249) if line.startswith("•") else (150, 168, 187)
        if "SHA256" in line:
            color = (97, 186, 203)
        draw.text((x + 14, iy), line, fill=color, font=font_box_body)
        iy += 26

# Connective Arrows Top Row (Left to Right)
for i in range(3):
    start_x = stages[i]["x"] + stages[i]["w"]
    end_x = stages[i + 1]["x"]
    cy = stages[i]["y"] + 130
    draw.line([(start_x + 5, cy), (end_x - 10, cy)], fill=(97, 186, 203), width=3)
    draw.polygon([(end_x - 2, cy), (end_x - 12, cy - 6), (end_x - 12, cy + 6)], fill=(97, 186, 203))

# Connective Arrow Down from Stage 4 to Stage 8, and wrap to bottom row
draw.line([(1385, 380), (1385, 415), (205, 415), (205, 450)], fill=(231, 173, 101), width=3)
draw.polygon([(205, 450), (199, 440), (211, 440)], fill=(231, 173, 101))

# Connective Arrows Bottom Row (Stage 5 -> 6 -> 7 -> 8)
for i in range(4, 7):
    start_x = stages[i]["x"] + stages[i]["w"]
    end_x = stages[i + 1]["x"]
    cy = stages[i]["y"] + 135
    draw.line([(start_x + 5, cy), (end_x - 10, cy)], fill=(160, 210, 120), width=3)
    draw.polygon(
        [(end_x - 2, cy), (end_x - 12, cy - 6), (end_x - 12, cy + 6)], fill=(160, 210, 120)
    )

# Save
img.save(OUT_PATH, format="PNG")
print(f"Generated pipeline diagram at: {OUT_PATH} ({w}x{h} px, {OUT_PATH.stat().st_size:,} bytes)")
