"""Independent verification script for Gate B acceptance and Gate C baseline."""

import hashlib
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.schema import (
    DatasetSnapshot,
    SatelliteGranule,
    SatelliteProcessedCrop,
    SatelliteTrackAssociation,
)


def main():
    dana_path = Path("data/raw/satellite/insat_real/3SIMG_25OCT2024_2330_L1B_STD_V01R00.h5")
    remal_path = Path("data/raw/satellite/insat_real/3RIMG_26MAY2024_1802_L1B_STD_V01R00.h5")

    assert dana_path.is_file(), "DANA file missing"
    assert remal_path.is_file(), "REMAL file missing"

    dana_size = dana_path.stat().st_size
    remal_size = remal_path.stat().st_size

    hasher = hashlib.sha256()
    with open(dana_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    dana_sha = hasher.hexdigest()

    expected_dana_sha = "98f3e5640bbc8c1d42da0fd090c0b93ead2d239718946ce69c25d59921ad4fcf"
    print(f"DANA File: {dana_path.name}")
    print(f"  Size: {dana_size} bytes (Expected: 275275100, Match: {dana_size == 275275100})")
    print(f"  SHA256: {dana_sha}")
    print(f"  Hash Match: {dana_sha == expected_dana_sha}")

    hasher_remal = hashlib.sha256()
    with open(remal_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher_remal.update(chunk)
    remal_sha = hasher_remal.hexdigest()
    expected_remal_sha = "5cfa552f68cebd1ab6c387b457803634b3bc9b211f84ed8d313cf8c0d4a80807"
    print(f"\nREMAL File: {remal_path.name}")
    print(f"  Size: {remal_size} bytes (Expected: 294275518, Match: {remal_size == 294275518})")
    print(f"  SHA256: {remal_sha}")
    print(f"  Hash Match: {remal_sha == expected_remal_sha}")

    # Check F1.1 snapshot
    f1_1_path = Path("reports/F1_DATA_QUALITY.json")
    if f1_1_path.is_file():
        h = hashlib.sha256(f1_1_path.read_bytes()).hexdigest()
        print(f"\nF1.1 JSON Hash: {h}")

    # DB Checks
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as s:
        granules = s.execute(select(SatelliteGranule)).scalars().all()
        print(f"\nTotal Granules in DB: {len(granules)}")
        real_granules = [g for g in granules if g.verification_status == "REAL_VERIFIED"]
        synth_granules = [g for g in granules if g.verification_status == "SYNTHETIC_FIXTURE"]
        print(f"  REAL_VERIFIED: {len(real_granules)}")
        print(f"  SYNTHETIC_FIXTURE: {len(synth_granules)}")
        for g in granules:
            print(
                f"    {g.granule_name} | Status: {g.verification_status} | Size: {g.file_size_bytes} | SHA: {g.sha256_checksum[:16]}..."
            )

        crops = s.execute(select(SatelliteProcessedCrop)).scalars().all()
        real_crops = [c for c in crops if c.verification_status == "REAL_VERIFIED"]
        synth_crops = [c for c in crops if c.verification_status == "SYNTHETIC_FIXTURE"]
        print(f"\nTotal Crops in DB: {len(crops)}")
        print(f"  REAL_VERIFIED: {len(real_crops)}")
        print(f"  SYNTHETIC_FIXTURE: {len(synth_crops)}")
        for c in real_crops:
            print(
                f"    REAL CROP: {c.storage_uri} | Channels: {c.channels} | SHA: {c.sha256_checksum[:16]}..."
            )

        assocs = s.execute(select(SatelliteTrackAssociation)).scalars().all()
        real_assocs = [a for a in assocs if a.verification_status == "REAL_VERIFIED"]
        synth_assocs = [a for a in assocs if a.verification_status == "SYNTHETIC_FIXTURE"]
        print(f"\nTotal Associations in DB: {len(assocs)}")
        print(f"  REAL_VERIFIED: {len(real_assocs)}")
        print(f"  SYNTHETIC_FIXTURE: {len(synth_assocs)}")
        for a in real_assocs:
            print(
                f"    Assoc {a.id}: Crop {a.crop_id} -> Obs {a.track_observation_id} | dt={a.temporal_offset_minutes}m, dr={a.spatial_offset_km}km"
            )

        # Snapshot count
        snapshots = s.execute(select(DatasetSnapshot)).scalars().all()
        print(f"\nDataset Snapshots: {len(snapshots)}")
        for snap in snapshots:
            print(
                f"  Snapshot: {snap.snapshot_name} | Version: {snap.transformation_version} | Manifest SHA: {snap.manifest_sha256}"
            )


if __name__ == "__main__":
    main()
