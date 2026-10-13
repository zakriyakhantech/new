# -*- coding: utf-8 -*-
"""Build batch 23 (fateema..ferdous) with the curated nv_build renderer.

The ignored work/batch23_src.json snapshot is optional: nv_build uses the
curated table, so a missing snapshot can be reconstructed from curated23.CUR.
If a snapshot exists, its names must exactly match the curated batch.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import curated23
import nv_build

nv_build.CUR = curated23.CUR
nv_build.GLOSSES = curated23.GLOSSES

source_path = os.path.join("work", "batch23_src.json")
if os.path.isfile(source_path):
    with open(source_path, encoding="utf-8") as source_file:
        rows = json.load(source_file)
else:
    rows = [{"name": name} for name in sorted(curated23.CUR)]

expected_names = sorted(curated23.CUR)
valid_rows = isinstance(rows, list) and all(
    isinstance(row, dict) and isinstance(row.get("name"), str) for row in rows
)
source_names = [row["name"] for row in rows] if valid_rows else []
if (
    not valid_rows
    or len(rows) != 100
    or len(set(source_names)) != len(source_names)
    or sorted(source_names) != expected_names
    or expected_names[0] != "fateema"
    or expected_names[-1] != "ferdous"
):
    print("Batch 23 source mismatch; expected 100 curated names fateema..ferdous")
    print("found:", len(source_names), "valid rows; missing:", sorted(set(expected_names) - set(source_names)))
    print("extra:", sorted(set(source_names) - set(expected_names)))
    sys.exit(1)

rows_by_name = {row["name"]: row for row in rows}
for name in expected_names:
    spec = curated23.CUR[name]
    gloss = curated23.GLOSSES.get(spec[5], {}).get("en", "")
    unsupported_glosses = re.findall(
        r"gloss '([^']*)'[^.]{0,120}unsupported", spec[11], re.IGNORECASE
    )
    unsupported_glosses += re.findall(
        r'gloss "([^"]*)"[^.]{0,120}unsupported', spec[11], re.IGNORECASE
    )
    if spec[10] in ("high", "medium") and any(
        gloss.strip().casefold() == unsupported.strip().casefold()
        for unsupported in unsupported_glosses
    ):
        print("Refusing to emit unsupported gloss for", name, ":", gloss)
        sys.exit(1)
    if spec[10] in ("high", "medium") and spec[6] not in ("Unknown", "") and not gloss:
        print("Refusing to emit verified name without an English gloss for", name)
        sys.exit(1)

out = os.path.join("out", "islamic")
os.makedirs(out, exist_ok=True)
for name in expected_names:
    rec = nv_build.build(name, rows_by_name[name])
    with open(os.path.join(out, name + ".json"), "w", encoding="utf-8") as output_file:
        json.dump(rec, output_file, ensure_ascii=False, indent=2)

print("built", len(expected_names), "records:", expected_names[0], "..", expected_names[-1])
