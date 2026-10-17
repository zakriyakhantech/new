#!/usr/bin/env python3
"""Evidence-first audit of NameVerse core meanings. Report-only; never rewrites name records."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKIP_DIRS = {".git", "node_modules", "dist", "build", ".next"}
SKIP_NAMES = {
    "manifest.json", "index.json", "_search-index.json",
    "CORE_MEANING_UPGRADE_REPORT.json", "CLEANUP_REPORT.json",
}
LOW_CONFIDENCE = {"", "LOW", "UNKNOWN", "UNVERIFIED", "NOT_ESTABLISHED", "NONE"}
HIGH_CONFIDENCE = {"HIGH", "VERY_HIGH", "VERIFIED"}
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
SPACE_RE = re.compile(r"\s+")
PLACEHOLDER_RE = re.compile(
    r"\b(?:todo|tbd|lorem ipsum|meaning not available|unknown meaning|"
    r"insert meaning|not yet researched|placeholder)\b", re.I
)
GENERIC_RE = re.compile(
    r"\b(?:is an? (?:arabic|persian|urdu|islamic|hindu|christian|"
    r"sanskrit|hebrew|greek|latin|turkish|african|indian)-origin name meaning|"
    r"the name means|is a beautiful name|is a unique name|"
    r"this name symbolizes|the name is associated with)\b", re.I
)


def normalize(value: Any) -> str:
    return SPACE_RE.sub(" ", str(value or "")).strip()


def walk_strings(value: Any):
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_strings(child)
    elif isinstance(value, str):
        yield value


def collect_urls(data: dict[str, Any]) -> list[str]:
    evidence = data.get("evidence", {})
    urls: list[str] = []
    if isinstance(evidence, dict):
        for key in ("sources", "source_references", "references", "citations", "core_claims"):
            value = evidence.get(key)
            if value is not None:
                for s in walk_strings(value):
                    urls.extend(URL_RE.findall(s))
    # Also detect URLs in claim-specific source objects elsewhere, but do not
    # treat an arbitrary URL elsewhere in the record as lexical evidence.
    if isinstance(evidence, dict):
        for s in walk_strings(evidence):
            urls.extend(URL_RE.findall(s))
    return sorted(set(u.rstrip(".,);]") for u in urls))


def record_issues(path: Path, doc: Any) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    if not isinstance(doc, dict):
        return {"path": str(path), "name": "", "slug": "", "status": "INVALID_JSON_SHAPE",
                "issues": ["top-level JSON value is not an object"]}, issues
    data = doc.get("data", doc)
    if not isinstance(data, dict):
        return {"path": str(path), "name": "", "slug": "", "status": "INVALID_SCHEMA",
                "issues": ["data is not an object"]}, issues

    name = normalize(data.get("name") or data.get("identity", {}).get("display_name"))
    slug = normalize(data.get("slug"))
    cm = data.get("core_meaning") if isinstance(data.get("core_meaning"), dict) else {}
    et = data.get("etymology") if isinstance(data.get("etymology"), dict) else {}
    evidence = data.get("evidence") if isinstance(data.get("evidence"), dict) else {}
    short = normalize(cm.get("short_meaning"))
    primary = normalize(cm.get("primary_meaning"))
    literal = normalize(cm.get("literal_meaning"))
    explanation = normalize(cm.get("meaning_explanation"))
    meaning_conf = normalize(cm.get("meaning_confidence")).upper()
    etym_conf = normalize(et.get("etymology_confidence")).upper()
    urls = collect_urls(data)

    if not name:
        issues.append("missing_name")
    if not slug:
        issues.append("missing_slug")
    elif name and re.sub(r"[^a-z0-9]+", "", name.casefold()) != re.sub(r"[^a-z0-9]+", "", slug.casefold()):
        issues.append("name_slug_mismatch_review")
    if not isinstance(data.get("core_meaning"), dict):
        issues.append("missing_core_meaning_object")
    if not short:
        issues.append("empty_short_meaning")
    if not primary:
        issues.append("empty_primary_meaning")
    if not literal:
        issues.append("empty_literal_meaning")
    if not explanation:
        issues.append("empty_meaning_explanation")

    meaning_text = " ".join((short, primary, literal, explanation))
    if PLACEHOLDER_RE.search(meaning_text):
        issues.append("placeholder_or_research_marker_in_meaning")
    if primary and GENERIC_RE.search(primary):
        issues.append("generic_template_primary_meaning")
    if short and literal and short.casefold() == literal.casefold():
        # This can be legitimate. Keep as a review hint, not an error.
        issues.append("short_and_literal_identical_review")
    if primary and explanation and primary.casefold() == explanation.casefold():
        issues.append("primary_and_explanation_identical")
    if meaning_conf in HIGH_CONFIDENCE and not urls:
        issues.append("high_meaning_confidence_without_evidence_urls")
    if etym_conf in HIGH_CONFIDENCE and not urls:
        issues.append("high_etymology_confidence_without_evidence_urls")
    if meaning_conf in LOW_CONFIDENCE and primary and not re.search(
        r"\b(unverified|uncertain|unclear|not established|not verified|requires research|"
        r"needs review|insufficient evidence|cannot be confirmed)\b", primary, re.I
    ):
        issues.append("low_confidence_but_assertive_primary_meaning_review")
    if not urls:
        issues.append("no_evidence_urls_detected")
    if isinstance(evidence, dict):
        # An empty list or absent claim-level evidence is a review hint. Different
        # historical schemas use different field names, so do not fail the record.
        claims = evidence.get("core_claims")
        if not isinstance(claims, list) or not claims:
            issues.append("no_structured_core_claim_evidence")
    all_text = " ".join(walk_strings(data))
    if "\ufffd" in all_text:
        issues.append("replacement_character_in_text")

    return {
        "path": str(path).replace("\\", "/"),
        "name": name,
        "slug": slug,
        "meaning_confidence": meaning_conf,
        "etymology_confidence": etym_conf,
        "evidence_url_count": len(urls),
        "evidence_urls": urls,
        "status": "REVIEW" if issues else "NO_HEURISTIC_FLAGS",
        "issues": sorted(set(issues)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }, issues


def discover(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.json")
        if not any(part in SKIP_DIRS for part in p.parts)
        and p.name not in SKIP_NAMES
        and not p.name.startswith(("PROGRESS_", "REPORT_", "manifest"))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="upgrading/names_upgraded",
                        help="Directory recursively containing name-record JSON files")
    parser.add_argument("--json-report", default="artifacts/core-meaning-audit.json")
    parser.add_argument("--csv-report", default="artifacts/core-meaning-audit.csv")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero when any record has review flags")
    args = parser.parse_args()
    root = Path(args.root)
    if not root.is_dir():
        raise SystemExit(f"Root directory does not exist: {root}")

    paths = discover(root)
    rows: list[dict[str, Any]] = []
    invalid: list[dict[str, str]] = []
    primary_hashes: dict[str, list[str]] = defaultdict(list)
    issue_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    for path in paths:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            invalid.append({"path": str(path), "error": str(exc)})
            continue
        row, _ = record_issues(path, doc)
        rows.append(row)
        issue_counts.update(row["issues"])
        confidence_counts[row.get("meaning_confidence", "MISSING") or "MISSING"] += 1
        primary = normalize(
            (doc.get("data", doc).get("core_meaning") or {}).get("primary_meaning")
            if isinstance(doc, dict) and isinstance(doc.get("data", doc), dict) else ""
        )
        if primary:
            primary_hashes[re.sub(r"[^a-z0-9]+", " ", primary.casefold()).strip()].append(row["path"])

    repeated = [
        {"normalized_primary_meaning": text, "count": len(items), "paths": items}
        for text, items in primary_hashes.items() if text and len(items) > 1
    ]
    repeated.sort(key=lambda item: (-item["count"], item["normalized_primary_meaning"]))
    flagged = sum(1 for row in rows if row["issues"])
    report = {
        "report_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "policy": "Heuristic triage only; this report does not prove or disprove lexical accuracy. No records were changed.",
        "summary": {
            "discovered_json_files": len(paths),
            "parsed_records": len(rows),
            "invalid_json_files": len(invalid),
            "records_with_review_flags": flagged,
            "records_without_heuristic_flags": len(rows) - flagged,
            "exact_duplicate_primary_meaning_groups": len(repeated),
            "issue_counts": dict(sorted(issue_counts.items())),
            "meaning_confidence_counts": dict(sorted(confidence_counts.items())),
        },
        "records": rows,
        "invalid_files": invalid,
        "exact_duplicate_primary_meanings": repeated,
    }
    json_path, csv_path = Path(args.json_report), Path(args.csv_report)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "path", "name", "slug", "status", "meaning_confidence", "etymology_confidence",
            "evidence_url_count", "issues", "evidence_urls", "sha256"
        ])
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["issues"] = ";".join(row["issues"])
            out["evidence_urls"] = ";".join(row["evidence_urls"])
            writer.writerow(out)

    print(json.dumps({
        **report["summary"],
        "json_report": str(json_path),
        "csv_report": str(csv_path),
        "invalid_files_sample": invalid[:10],
        "top_duplicate_primary_meanings": repeated[:10],
    }, ensure_ascii=False, indent=2))
    if invalid:
        return 2
    if args.strict and flagged:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
