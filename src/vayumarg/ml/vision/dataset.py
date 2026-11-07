"""PyTorch Dataset Implementations for Satellite Cyclone Vision Tasks.

Provides:
1. `CycloneImageDataset`: Single-frame satellite infrared dataset for intensity regression.
2. `CycloneSequenceDataset`: Multi-frame chronological sequence dataset for ConvLSTM.
"""

import json
from pathlib import Path

import torch
import torchvision.transforms as T
from PIL import Image
from torch.utils.data import Dataset


# Standard meteorological intensity categorization based on IMD / NHC operational scales
def wind_to_category_index(wind_kt: float) -> int:
    """Map continuous maximum sustained wind speed (knots) to category index.

    0: Tropical Depression (<28 kt)
    1: Deep Depression (28–33 kt)
    2: Cyclonic Storm (34–47 kt)
    3: Severe Cyclonic Storm (48–63 kt)
    4: Very Severe Cyclonic Storm (64–89 kt)
    5: Extremely Severe / Super Cyclone (>=90 kt)
    """
    if wind_kt < 28.0:
        return 0
    elif wind_kt < 34.0:
        return 1
    elif wind_kt < 48.0:
        return 2
    elif wind_kt < 64.0:
        return 3
    elif wind_kt < 90.0:
        return 4
    else:
        return 5


CATEGORY_NAMES = [
    "Tropical Depression (<28 kt)",
    "Deep Depression (28-33 kt)",
    "Cyclonic Storm (34-47 kt)",
    "Severe Cyclonic Storm (48-63 kt)",
    "Very Severe Cyclonic Storm (64-89 kt)",
    "Extremely Severe / Super Cyclone (>=90 kt)",
]


class CycloneImageDataset(Dataset):
    """Dataset for single-frame satellite infrared intensity regression."""

    def __init__(
        self,
        manifest_path: str | Path,
        split: str = "train",
        image_size: int = 128,
        augment: bool = False,
        base_dir: Path | None = None,
    ):
        self.manifest_path = Path(manifest_path)
        self.split = split
        self.image_size = image_size
        self.augment = augment
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Navigate up until we find project root containing 'data'
            curr = self.manifest_path.resolve().parent
            while curr.parent != curr and not (curr / "data" / "raw").is_dir():
                curr = curr.parent
            self.base_dir = curr

        with open(self.manifest_path, encoding="utf-8") as f:
            data = json.load(f)

        all_frames = data.get("frames", [])
        self.frames = [f for f in all_frames if f.get("split") == split]

        if not self.frames:
            raise ValueError(f"No frames found for split '{split}' in manifest {manifest_path}")

        # Transforms
        base_transforms = [
            T.Resize((image_size, image_size)),
            T.ToTensor(),  # Scales uint8 [0, 255] -> float32 [0.0, 1.0]
            T.Normalize(mean=[0.45], std=[0.22]),  # Standard satellite IR normalization
        ]
        if self.augment:
            self.transforms = T.Compose(
                [
                    T.RandomHorizontalFlip(p=0.5),
                    T.RandomVerticalFlip(p=0.5),
                ]
                + base_transforms
            )
        else:
            self.transforms = T.Compose(base_transforms)

    def __len__(self) -> int:
        return len(self.frames)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor | str | float]:
        item = self.frames[idx]
        img_rel_path = item["image_path"]
        img_full_path = self.base_dir / img_rel_path

        # Load single-channel grayscale
        img = Image.open(img_full_path).convert("L")
        tensor = self.transforms(img)

        wind_speed = float(item["wind_speed_knots"])
        cat_idx = wind_to_category_index(wind_speed)

        return {
            "image": tensor,
            "wind_speed": torch.tensor(wind_speed, dtype=torch.float32),
            "category": torch.tensor(cat_idx, dtype=torch.long),
            "storm_id": item["storm_id"],
            "frame_id": item["frame_id"],
        }


class CycloneSequenceDataset(Dataset):
    """Dataset for chronological multi-frame satellite image sequences."""

    def __init__(
        self,
        manifest_path: str | Path,
        split: str = "train",
        image_size: int = 64,
        base_dir: Path | None = None,
    ):
        self.manifest_path = Path(manifest_path)
        self.split = split
        self.image_size = image_size
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Navigate up until we find project root containing 'data'
            curr = self.manifest_path.resolve().parent
            while curr.parent != curr and not (curr / "data" / "raw").is_dir():
                curr = curr.parent
            self.base_dir = curr

        with open(self.manifest_path, encoding="utf-8") as f:
            data = json.load(f)

        all_seqs = data.get("sequences", [])
        self.sequences = [s for s in all_seqs if s.get("split") == split]

        if not self.sequences:
            raise ValueError(f"No sequences found for split '{split}' in manifest {manifest_path}")

        self.transform = T.Compose(
            [
                T.Resize((image_size, image_size)),
                T.ToTensor(),
                T.Normalize(mean=[0.45], std=[0.22]),
            ]
        )
        self.target_transform = T.Compose(
            [
                T.Resize((image_size, image_size)),
                T.ToTensor(),  # Target frame normalized [0, 1] for visual reconstruction
            ]
        )

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor | str | float]:
        item = self.sequences[idx]

        # Load input past frames
        input_tensors = []
        for rel_path in item["input_frames"]:
            img_path = self.base_dir / rel_path
            img = Image.open(img_path).convert("L")
            input_tensors.append(self.transform(img))

        # Stack along time dimension: shape (T, 1, H, W)
        seq_tensor = torch.stack(input_tensors, dim=0)

        # Target next frame
        target_path = self.base_dir / item["target_frame"]
        target_img = Image.open(target_path).convert("L")
        target_frame_tensor = self.target_transform(target_img)

        target_wind = float(item["target_wind"])

        return {
            "sequence": seq_tensor,
            "target_wind": torch.tensor(target_wind, dtype=torch.float32),
            "target_frame": target_frame_tensor,
            "storm_id": item["storm_id"],
            "sequence_id": item["sequence_id"],
        }
