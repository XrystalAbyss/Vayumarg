import re
from pathlib import Path

out_path = Path("C:/Users/astra/.gemini/antigravity/brain/8152f11a-8dc5-4be3-acc8-0db9055af803/.system_generated/steps/4002/output.txt")
text = out_path.read_text(encoding="utf-8")

lines = text.splitlines()
cur_pkg = ""
cur_mod = ""
counts = {}
all_tests = []

for line in lines:
    line_s = line.strip()
    if "<Package " in line_s:
        cur_pkg = line_s.split()[1].strip("<>")
    elif "<Module " in line_s:
        cur_mod = line_s.split()[1].strip("<>")
        counts[f"{cur_pkg}/{cur_mod}"] = 0
    elif "<Function " in line_s:
        fn = line_s.split()[1].strip("<>")
        counts[f"{cur_pkg}/{cur_mod}"] += 1
        all_tests.append(f"tests/{cur_pkg}/{cur_mod}::{fn}")

print(f"Total collected tests: {len(all_tests)}")
int_c = sum(v for k, v in counts.items() if k.startswith("integration/"))
unit_c = sum(v for k, v in counts.items() if k.startswith("unit/"))
int_mods = [k for k in counts if k.startswith("integration/")]
unit_mods = [k for k in counts if k.startswith("unit/")]

print(f"Integration: {int_c} tests across {len(int_mods)} files")
print(f"Unit: {unit_c} tests across {len(unit_mods)} files")
print("\nBreakdown per file:")
for k, v in sorted(counts.items()):
    print(f"  {k}: {v}")
