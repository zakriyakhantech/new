#!/usr/bin/env python3
"""Remove undocumented numeric scores that read as facts but have no method.

- popularity_by_region: per-country "scores" stamped 2024 with no registry source
- seo.seo_score / content_quality.quality_score: self-assigned editorial scores

popularity_score is kept: the site uses it only as an internal sort key and
labels it as such. Usage: strip_fabricated_scores.py DIR [DIR...]
"""
import json, sys
from pathlib import Path

def strip(d):
    removed = []
    if isinstance(d.get("popularity_by_region"), list):
        d.pop("popularity_by_region"); removed.append("popularity_by_region")
    for parent, key in (("seo", "seo_score"), ("content_quality", "quality_score")):
        p = d.get(parent)
        if isinstance(p, dict) and key in p:
            p.pop(key); removed.append(f"{parent}.{key}")
    return removed

def main(dirs):
    files = changed = 0
    for root in dirs:
        for p in sorted(Path(root).glob("*.json")):
            text = p.read_text(encoding="utf-8")
            try: obj = json.loads(text)
            except ValueError: continue
            if not isinstance(obj, dict) or not isinstance(obj.get("data"), dict): continue
            files += 1
            if strip(obj["data"]):
                ascii_ = "\\u" in text
                out = json.dumps(obj, ensure_ascii=ascii_, indent=2)
                p.write_text(out + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
                changed += 1
    print(f"checked={files} changed={changed}")

if __name__ == "__main__":
    main(sys.argv[1:])
