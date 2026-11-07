"""Acquire authentic NASA Tropical Cyclone Wind Dataset from Hugging Face.

Streams authentic geostationary infrared cyclone imagery (366x366 single-channel IR),
filters for a balanced cohort of 25 unique tropical cyclones across the intensity spectrum,
enforces strict storm-disjoint train/val/test splits, and builds sequence manifests for ConvLSTM.
"""

import hashlib
import io
import json
import logging
import tarfile
import urllib.request
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("acquire_data")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_IMG_DIR = DATA_DIR / "raw" / "satellite" / "nasa_cyclone" / "images"
PROCESSED_DIR = DATA_DIR / "processed" / "satellite" / "nasa_cyclone"

RAW_IMG_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INFO_CSV_URL = (
    "https://huggingface.co/datasets/torchgeo/tropical_cyclone/resolve/main/train_info.csv"
)
TAR_GZ_URL = "https://huggingface.co/datasets/torchgeo/tropical_cyclone/resolve/main/nasa_tropical_storm_competition_train_source.tar.gz"

# 25 Target Storms with broad intensity coverage (20 kt to 150 kt)
TRAIN_STORMS = [
    "psz",  # Peak: 150 kt (Major Category 5 equivalent)
    "eoi",  # Peak: 125 kt
    "kqu",  # Peak: 120 kt
    "vxf",  # Peak: 115 kt
    "fcr",  # Peak: 105 kt
    "ipa",  # Peak: 110 kt
    "fna",  # Peak: 95 kt
    "xjo",  # Peak: 85 kt
    "gic",  # Peak: 80 kt
    "ing",  # Peak: 75 kt
    "ywf",  # Peak: 70 kt
    "vye",  # Peak: 65 kt
    "blq",  # Peak: 65 kt
    "rml",  # Peak: 45 kt
    "ojv",  # Peak: 35 kt (Tropical Depression / Weak)
]

VAL_STORMS = [
    "wsy",  # Peak: 135 kt
    "pjj",  # Peak: 105 kt
    "bkh",  # Peak: 85 kt
    "zny",  # Peak: 75 kt
    "woc",  # Peak: 65 kt
]

TEST_STORMS = [
    "xtd",  # Peak: 125 kt
    "dzw",  # Peak: 115 kt
    "hig",  # Peak: 110 kt
    "qpq",  # Peak: 95 kt
    "gme",  # Peak: 45 kt
]

TARGET_STORMS_SET = set(TRAIN_STORMS + VAL_STORMS + TEST_STORMS)


def get_split(storm_id: str) -> str:
    if storm_id in TRAIN_STORMS:
        return "train"
    elif storm_id in VAL_STORMS:
        return "val"
    elif storm_id in TEST_STORMS:
        return "test"
    return "other"


def main():
    logger.info("Step 1: Downloading train_info.csv from Hugging Face...")
    req = urllib.request.Request(INFO_CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        df_info = pd.read_csv(io.StringIO(resp.read().decode("utf-8")))

    logger.info(
        "Loaded train_info.csv: %d rows across %d storms",
        len(df_info),
        df_info["storm_id"].nunique(),
    )

    # Filter for target storms
    df_target = df_info[df_info["storm_id"].isin(TARGET_STORMS_SET)].copy()
    df_target["split"] = df_target["storm_id"].apply(get_split)
    df_target.sort_values(by=["storm_id", "relative_time"], inplace=True)
    df_target.reset_index(drop=True, inplace=True)

    logger.info(
        "Target cohort filtered: %d frames across %d storms (Train: %d, Val: %d, Test: %d)",
        len(df_target),
        df_target["storm_id"].nunique(),
        (df_target["split"] == "train").sum(),
        (df_target["split"] == "val").sum(),
        (df_target["split"] == "test").sum(),
    )

    # Map paths to record metadata
    path_to_meta = {row["path"]: row for row in df_target.to_dict(orient="records")}
    extracted_records = []

    # Step 2: Stream tar.gz and extract images for target storms
    logger.info("Step 2: Streaming tar.gz archive over HTTP and extracting target frames...")
    req_tar = urllib.request.Request(TAR_GZ_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp_tar = urllib.request.urlopen(req_tar)

    target_paths_set = set(path_to_meta.keys())
    saved_count = 0
    stride_step = 2  # Sample every 2nd frame to keep training fast while preserving dense chronological sequences (~1-hr interval)

    # Track frames per storm
    storm_frame_counters = dict.fromkeys(TARGET_STORMS_SET, 0)

    with tarfile.open(fileobj=resp_tar, mode="r|gz") as tar:
        for member in tar:
            if not member.name.endswith("image.jpg"):
                continue

            # member.name format: nasa_tropical_storm_competition_train_source/nasa_tropical_storm_competition_train_source_{storm_id}_{idx}/image.jpg
            parts = member.name.split("/")
            if len(parts) < 2:
                continue
            folder_name = parts[-2]

            if folder_name not in target_paths_set:
                continue

            meta = path_to_meta[folder_name]
            storm_id = meta["storm_id"]

            storm_frame_counters[storm_id] += 1
            # Apply stride to maintain reasonable total dataset volume (~2,500 frames)
            if storm_frame_counters[storm_id] % stride_step != 0:
                continue

            extracted_file = tar.extractfile(member)
            if extracted_file is None:
                continue

            img_bytes = extracted_file.read()
            img_sha256 = hashlib.sha256(img_bytes).hexdigest()

            # Save locally
            filename = f"{folder_name}.jpg"
            out_path = RAW_IMG_DIR / filename
            out_path.write_bytes(img_bytes)

            # Record in manifest
            rel_path = f"data/raw/satellite/nasa_cyclone/images/{filename}"
            extracted_records.append(
                {
                    "frame_id": folder_name,
                    "storm_id": storm_id,
                    "relative_time_seconds": int(meta["relative_time"]),
                    "wind_speed_knots": float(meta["wind_speed"]),
                    "ocean_basin": int(meta["ocean"]),
                    "split": meta["split"],
                    "image_path": rel_path,
                    "image_sha256": img_sha256,
                    "width": 366,
                    "height": 366,
                    "channels": 1,
                    "source": "NASA_TROPICAL_CYCLONE_WIND_NOAA_GOES_IR",
                }
            )

            saved_count += 1
            if saved_count % 250 == 0:
                logger.info("Extracted %d authentic cyclone images...", saved_count)

            # Cap at 2,500 frames for optimal sprint training time (< 5 min on RTX 4050)
            if saved_count >= 2500:
                logger.info(
                    "Reached target capacity of %d authentic frames. Finalizing stream.",
                    saved_count,
                )
                break

    logger.info("Total images extracted: %d", len(extracted_records))

    # Save dataset manifest
    manifest_df = pd.DataFrame(extracted_records)
    manifest_df.sort_values(by=["storm_id", "relative_time_seconds"], inplace=True)
    manifest_csv = PROCESSED_DIR / "dataset_manifest.csv"
    manifest_df.to_csv(manifest_csv, index=False)

    manifest_json = PROCESSED_DIR / "dataset_manifest.json"
    manifest_data = {
        "dataset_name": "NASA Tropical Cyclone Wind Estimation Benchmark Subset",
        "provenance": "NASA IMPACT / NOAA GOES Infrared Imagery",
        "licensing": "CC-BY-4.0 / Open Benchmark",
        "total_images": len(extracted_records),
        "unique_storms": manifest_df["storm_id"].nunique(),
        "train_storms": TRAIN_STORMS,
        "val_storms": VAL_STORMS,
        "test_storms": TEST_STORMS,
        "train_samples": int((manifest_df["split"] == "train").sum()),
        "val_samples": int((manifest_df["split"] == "val").sum()),
        "test_samples": int((manifest_df["split"] == "test").sum()),
        "wind_speed_summary": {
            "min_kt": float(manifest_df["wind_speed_knots"].min()),
            "max_kt": float(manifest_df["wind_speed_knots"].max()),
            "mean_kt": float(round(manifest_df["wind_speed_knots"].mean(), 2)),
            "std_kt": float(round(manifest_df["wind_speed_knots"].std(), 2)),
        },
        "frames": extracted_records,
    }
    manifest_json.write_text(json.dumps(manifest_data, indent=2))

    # Step 3: Build ConvLSTM Sequence Manifest (Chronological sequences of length 4)
    logger.info("Step 3: Building ConvLSTM chronological sequence manifest...")
    seq_records = []
    seq_length = 4

    for storm_id, group in manifest_df.groupby("storm_id"):
        group_sorted = group.sort_values("relative_time_seconds").reset_index(drop=True)
        split = group_sorted["split"].iloc[0]

        if len(group_sorted) < seq_length:
            continue

        for i in range(len(group_sorted) - seq_length + 1):
            window = group_sorted.iloc[i : i + seq_length]
            # Ensure chronological order
            times = window["relative_time_seconds"].tolist()
            if times != sorted(times):
                continue

            frame_paths = window["image_path"].tolist()
            winds = window["wind_speed_knots"].tolist()

            seq_records.append(
                {
                    "sequence_id": f"{storm_id}_seq_{i:04d}",
                    "storm_id": storm_id,
                    "split": split,
                    "input_frames": frame_paths[: seq_length - 1],  # 3 past frames
                    "target_frame": frame_paths[-1],  # Next frame
                    "past_winds": winds[: seq_length - 1],
                    "target_wind": winds[-1],  # Target wind at next step
                    "time_step_seconds": times[-1] - times[-2],
                }
            )

    seq_manifest_json = PROCESSED_DIR / "sequences_manifest.json"
    seq_manifest_data = {
        "sequence_length": seq_length,
        "input_frames_count": seq_length - 1,
        "total_sequences": len(seq_records),
        "train_sequences": sum(1 for s in seq_records if s["split"] == "train"),
        "val_sequences": sum(1 for s in seq_records if s["split"] == "val"),
        "test_sequences": sum(1 for s in seq_records if s["split"] == "test"),
        "sequences": seq_records,
    }
    seq_manifest_json.write_text(json.dumps(seq_manifest_data, indent=2))
    logger.info(
        "ConvLSTM Sequences created: %d (Train: %d, Val: %d, Test: %d)",
        seq_manifest_data["total_sequences"],
        seq_manifest_data["train_sequences"],
        seq_manifest_data["val_sequences"],
        seq_manifest_data["test_sequences"],
    )
    logger.info("Acquisition complete! Manifests saved to %s", PROCESSED_DIR)


if __name__ == "__main__":
    main()
