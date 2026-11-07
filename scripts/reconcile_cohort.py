import json
from collections import Counter

with open("reports/F2_4_GATE_D_CANDIDATE_INVENTORY.json") as f:
    inv = json.load(f)

existing = inv["existing_corpus"]
candidates = inv["candidate_cohort"]
existing_sids = {e["sid"]: e["storm_name"] for e in existing}

print("=== EXISTING STORMS (4) ===")
for sid, name in existing_sids.items():
    print(f"  {name:10s} : {sid}")

print("\n=== CANDIDATE GRANULES (14) ===")
for i, c in enumerate(candidates, 1):
    is_new = c["canonical_sid"] not in existing_sids
    print(
        f"{i:2d}. {c['candidate_id']:15s} | {c['storm_name']:15s} | SID: {c['canonical_sid']} | New: {is_new}"
    )

candidate_sids = [c["canonical_sid"] for c in candidates]
unique_candidate_sids = set(candidate_sids)
newly_introduced_sids = unique_candidate_sids - set(existing_sids.keys())
repeated_existing_sids = unique_candidate_sids.intersection(set(existing_sids.keys()))
all_cohort_sids = set(existing_sids.keys()).union(unique_candidate_sids)

print("\n=== EXACT ARITHMETIC RECONCILIATION ===")
print("Existing granules:", len(existing))
print("Candidate granules:", len(candidates))
print("Total granules in cohort:", len(existing) + len(candidates))
print("Unique existing SIDs:", len(existing_sids))
print("Unique candidate SIDs:", len(unique_candidate_sids))
print("Newly introduced unique SIDs:", len(newly_introduced_sids))
print(
    "Existing SIDs repeated in candidates:",
    len(repeated_existing_sids),
    [existing_sids[s] for s in repeated_existing_sids],
)
print("Total unique storm SIDs in cohort (existing + new):", len(all_cohort_sids))

# Granules per storm breakdown

all_sids_list = list(existing_sids.keys()) + candidate_sids
sid_counts = Counter(all_sids_list)
print("\n=== GRANULES PER STORM IN FULL 18-GRANULE COHORT ===")
for sid, cnt in sid_counts.items():
    # find name
    name = existing_sids.get(sid)
    if not name:
        for c in candidates:
            if c["canonical_sid"] == sid:
                name = c["storm_name"]
                break
    print(f"  {name:15s} (SID {sid}): {cnt} granule(s)")

# Breakdown by basin and sensor across 18 granules
basin_counts = Counter()
sensor_counts = Counter()
for e in existing:
    basin_counts[e["basin"]] += 1
    sensor_counts[e["satellite"]] += 1
for c in candidates:
    basin_counts[c["basin"]] += 1
    sensor_counts[c["satellite"]] += 1

print("\n=== GRANULES PER BASIN (18) ===")
for b, cnt in basin_counts.items():
    print(f"  {b}: {cnt} ({cnt / 18 * 100:.1f}%)")

print("\n=== GRANULES PER SENSOR (18) ===")
for s, cnt in sensor_counts.items():
    print(f"  {s}: {cnt} ({cnt / 18 * 100:.1f}%)")
