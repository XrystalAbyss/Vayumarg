"""Verify PostgreSQL database entities and invariant counts after Gate C Batch 1."""

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from vayumarg.core.config import settings
from vayumarg.database.schema import (
    DatasetSnapshot,
    SatelliteGranule,
    SatelliteProcessedCrop,
    SatelliteTrackAssociation,
    Storm,
    TrackObservation,
)


def main():
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as s:
        # Granules
        real_g = (
            s.execute(
                select(SatelliteGranule).where(
                    SatelliteGranule.verification_status == "REAL_VERIFIED"
                )
            )
            .scalars()
            .all()
        )
        print(f"REAL_VERIFIED Granules: {len(real_g)}")
        for g in real_g:
            print(
                f"  {g.granule_name} | {g.file_size_bytes:,} bytes | {g.sha256_checksum[:16]}... | UUID: {g.id}"
            )

        # Crops
        real_c = (
            s.execute(
                select(SatelliteProcessedCrop).where(
                    SatelliteProcessedCrop.verification_status == "REAL_VERIFIED"
                )
            )
            .scalars()
            .all()
        )
        print(f"\nREAL_VERIFIED Crops: {len(real_c)}")
        for c in real_c:
            me = (c.quality_control_flags or {}).get("model_eligibility", {})
            print(
                f"  {c.storage_uri} | SHA: {c.sha256_checksum[:16]}... | IMD Eligible: {me.get('primary_imd_category_classification')} | JTWC Eligible: {me.get('agency_conditioned_jtwc_intensity')}"
            )

        # Associations
        real_a = (
            s.execute(
                select(SatelliteTrackAssociation).where(
                    SatelliteTrackAssociation.verification_status == "REAL_VERIFIED"
                )
            )
            .scalars()
            .all()
        )
        print(f"\nREAL_VERIFIED Associations: {len(real_a)}")

        # Historical Invariants
        storm_cnt = s.execute(select(func.count(Storm.id))).scalar_one()
        obs_cnt = s.execute(select(func.count(TrackObservation.id))).scalar_one()
        snap = s.execute(select(DatasetSnapshot)).scalar_one()

        print("\nHistorical Invariants:")
        print(f"  Total Storms: {storm_cnt} (Expected: 1860, Match: {storm_cnt == 1860})")
        print(f"  Total Observations: {obs_cnt} (Expected: 104374, Match: {obs_cnt == 104374})")
        print(f"  Snapshot SHA-256: {snap.manifest_sha256}")
        print(
            f"  Match: {snap.manifest_sha256 == '441ab5008e2793deb957e95cdd19ae6c3fd66ab39c2944a9838ab453b7680107'}"
        )


if __name__ == "__main__":
    main()
