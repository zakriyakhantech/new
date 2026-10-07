#!/usr/bin/env python3
"""Validate the 10 newly added Islamic name records against the super-2.0 schema.

Schema parity is checked key-path-by-key-path against the existing reference
record aaban.json (195 key paths). Exits non-zero on any failure so the CI
workflow aborts before committing.
"""
import json
import os
import sys

BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "names_upgraded", "islamic")
)
NAMES = [
    "zain", "zayan", "taha", "usama", "sara",
    "zoya", "sumayyah", "sidra", "tooba", "hoorain",
]


def key_paths(obj, prefix=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += key_paths(v, prefix + "." + k)
    elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
        out += key_paths(obj[0], prefix + "[]")
    else:
        out.append(prefix)
    return out


def main():
    ref_path = os.path.join(BASE, "aaban.json")
    with open(ref_path, encoding="utf-8") as fh:
        ref = json.load(fh)
    ref_paths = set(key_paths(ref))
    print(f"reference aaban.json key paths: {len(ref_paths)}")

    failures = 0
    for name in NAMES:
        fp = os.path.join(BASE, name + ".json")
        if not os.path.exists(fp):
            print(f"FAIL {name}: file missing")
            failures += 1
            continue
        try:
            with open(fp, encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            print(f"FAIL {name}: invalid JSON ({exc})")
            failures += 1
            continue

        if data.get("schema_version") != "super-2.0":
            print(f"FAIL {name}: schema_version={data.get('schema_version')!r}")
            failures += 1
            continue

        got = set(key_paths(data))
        missing = ref_paths - got
        extra = got - ref_paths
        if missing or extra:
            print(f"FAIL {name}: missing={sorted(missing)[:5]} extra={sorted(extra)[:5]}")
            failures += 1
            continue

        faq = data.get("data", {}).get("faq", [])
        print(f"OK   {name}: {len(got)} key paths, {len(faq)} FAQs, "
              f"seo_score={data.get('data', {}).get('seo', {}).get('seo_score')}")

    print(f"FAILURES: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
