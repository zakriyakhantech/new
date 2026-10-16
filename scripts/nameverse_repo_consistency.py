#!/usr/bin/env python3
"""Repository-wide, conservative NameVerse JSON consistency audit.

This tool does not verify factual truth. By default it is report-only.
With --apply-safe-fixes it only lowers contradictory verification/render flags;
it never invents or rewrites meanings, translations, sources, slugs, or variants.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_ROOTS = [
    "upgrading/names_upgraded",
    "upgrades-namesv2",
]
LOW_CONFIDENCE = {
    "", "low", "unknown", "unverified", "not_verified", "not_established",
    "none", "draft", "pending", "requires_source_review",
}
UNCERTAIN_STATUS = re.compile(
    r"(not[_ -]?verified|unverified|pending|requires[_ -]?review|"
    r"not[_ -]?measured|not[_ -]?published|unresolved|draft|unknown)",
    re.I,
)


def obj(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def get_path(root: dict, dotted: str, default=None):
    cur: Any = root
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def source_urls(data: dict) -> list[str]:
    result = []
    sources = obj(data.get("evidence")).get("sources", [])
    if not isinstance(sources, list):
        return result
    for source in sources:
        if isinstance(source, str) and source.strip().startswith(("https://", "http://")):
            result.append(source.strip())
        elif isinstance(source, dict):
            for key in ("url", "uri", "source_url", "href"):
                value = source.get(key)
                if isinstance(value, str) and value.strip().startswith(("https://", "http://")):
                    result.append(value.strip())
    return result


def faq_questions(data: dict) -> list[str]:
    faq = data.get("faq", [])
    if not isinstance(faq, list):
        return []
    return [
        " ".join(str(item.get("q", item.get("question", ""))).casefold().split())
        for item in faq if isinstance(item, dict)
    ]


def structured_faq_questions(data: dict) -> list[str] | None:
    graph = obj(data.get("structured_data")).get("@graph", [])
    if not isinstance(graph, list):
        return None
    for node in graph:
        if not isinstance(node, dict) or node.get("@type") != "FAQPage":
            continue
        entities = node.get("mainEntity", [])
        if not isinstance(entities, list):
            return []
        return [
            " ".join(str(item.get("name", "")).casefold().split())
            for item in entities if isinstance(item, dict)
        ]
    return None


def audit_file(path: Path, apply_safe_fixes: bool) -> tuple[dict, bool]:
    entry = {"path": path.as_posix(), "issues": [], "safe_fixes": []}
    changed = False
    try:
        raw = path.read_text(encoding="utf-8")
        record = json.loads(raw)
    except Exception as exc:
        entry["issues"].append({"code": "INVALID_JSON", "detail": str(exc)})
        return entry, False

    data = record.get("data") if isinstance(record, dict) else None
    if not isinstance(data, dict):
        entry["issues"].append({"code": "MISSING_DATA_OBJECT"})
        return entry, False

    name = str(data.get("name", "")).strip()
    identity = obj(data.get("identity"))
    slug = str(data.get("slug", "")).strip()
    filename_slug = path.stem.casefold().replace("_", "-")
    if not name:
        entry["issues"].append({"code": "MISSING_NAME"})
    if not slug:
        entry["issues"].append({"code": "MISSING_SLUG"})
    elif slug.casefold() != filename_slug:
        entry["issues"].append({
            "code": "SLUG_FILENAME_MISMATCH",
            "detail": f"slug={slug!r}; filename={path.stem!r}; review only (not auto-corrected)",
        })
    if identity.get("display_name") and name and identity["display_name"].strip().casefold() != name.casefold():
        entry["issues"].append({"code": "DISPLAY_NAME_MISMATCH", "detail": "data.name and identity.display_name differ"})
    if identity.get("normalized_name") and slug and identity["normalized_name"].strip().casefold() != slug.casefold():
        entry["issues"].append({"code": "NORMALIZED_NAME_SLUG_MISMATCH", "detail": "review aliases/normalization; not auto-corrected"})

    urls = source_urls(data)
    confidence_paths = (
        "core_meaning.meaning_confidence",
        "etymology.etymology_confidence",
        "origin.origin_confidence",
    )
    weak_confidence = [
        key for key in confidence_paths
        if str(get_path(data, key, "")).strip().casefold() in LOW_CONFIDENCE
    ]
    verification = obj(data.get("verification"))
    editorial = obj(data.get("editorial"))
    quality = obj(data.get("content_quality"))
    manual = obj(data.get("editorial_validation"))

    if not urls:
        entry["issues"].append({"code": "NO_TRACEABLE_SOURCE_URL"})
    if verification.get("tier1_verified") is True and (weak_confidence or not urls):
        entry["issues"].append({"code": "TIER1_CONTRADICTS_EVIDENCE"})
        if apply_safe_fixes:
            verification["tier1_verified"] = False
            entry["safe_fixes"].append("verification.tier1_verified -> false")
            changed = True
    if quality.get("tier1_verified") is True and (weak_confidence or not urls):
        entry["issues"].append({"code": "CONTENT_TIER1_CONTRADICTS_EVIDENCE"})
        if apply_safe_fixes:
            quality["tier1_verified"] = False
            entry["safe_fixes"].append("content_quality.tier1_verified -> false")
            changed = True
    if editorial.get("needs_manual_verification") is False and (weak_confidence or not urls):
        entry["issues"].append({"code": "MANUAL_REVIEW_INCORRECTLY_DISABLED"})
        if apply_safe_fixes:
            editorial["needs_manual_verification"] = True
            entry["safe_fixes"].append("editorial.needs_manual_verification -> true")
            changed = True
    if manual.get("needs_manual_verification") is False and (weak_confidence or not urls):
        entry["issues"].append({"code": "EDITORIAL_VALIDATION_REVIEW_CONTRADICTION"})
        if apply_safe_fixes:
            manual["needs_manual_verification"] = True
            entry["safe_fixes"].append("editorial_validation.needs_manual_verification -> true")
            changed = True

    # Conservative display rule: uncertain sections should not be publicly rendered.
    for section_name, section in data.items():
        if not isinstance(section, dict) or "render" not in section:
            continue
        status = str(section.get("status", ""))
        if section.get("render") is True and UNCERTAIN_STATUS.search(status):
            entry["issues"].append({"code": "UNCERTAIN_SECTION_RENDERED", "detail": section_name})
            if apply_safe_fixes:
                section["render"] = False
                entry["safe_fixes"].append(f"{section_name}.render -> false")
                changed = True

    questions = faq_questions(data)
    if len(questions) != len(set(questions)):
        duplicates = sorted(q for q, count in Counter(questions).items() if q and count > 1)
        entry["issues"].append({"code": "DUPLICATE_FAQ_QUESTIONS", "detail": duplicates})

    structured_questions = structured_faq_questions(data)
    if structured_questions is not None and questions != structured_questions:
        entry["issues"].append({
            "code": "FAQ_STRUCTURED_DATA_MISMATCH",
            "detail": f"faq_items={len(questions)}, structured_items={len(structured_questions)}; order/content review required",
        })

    translations = data.get("translations")
    if isinstance(translations, dict):
        for lang, translation in translations.items():
            if not isinstance(translation, dict):
                entry["issues"].append({"code": "INVALID_TRANSLATION_OBJECT", "detail": str(lang)})
                continue
            for field in ("meaning", "long_meaning"):
                if field in translation and not str(translation[field]).strip():
                    entry["issues"].append({"code": "BLANK_TRANSLATION_FIELD", "detail": f"{lang}.{field}"})
    quality_score = get_path(data, "content_quality.quality_score")
    if isinstance(quality_score, (int, float)) and not get_path(data, "content_quality.quality_score_basis"):
        entry["issues"].append({"code": "UNEXPLAINED_QUALITY_SCORE"})
    seo_score = get_path(data, "seo.seo_score")
    if isinstance(seo_score, (int, float)) and not get_path(data, "seo.seo_score_basis"):
        entry["issues"].append({"code": "UNEXPLAINED_SEO_SCORE"})

    if changed:
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return entry, changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", dest="roots", help="Dataset root; repeat for multiple roots.")
    parser.add_argument("--report", default="nameverse-consistency-report.json", help="JSON report output path.")
    parser.add_argument("--apply-safe-fixes", action="store_true", help="Only lower contradictory verification/render flags.")
    args = parser.parse_args()
    roots = [Path(root) for root in (args.roots or DEFAULT_ROOTS)]
    files: list[Path] = []
    missing_roots = []
    for root in roots:
        if not root.exists():
            missing_roots.append(root.as_posix())
            continue
        files.extend(p for p in root.rglob("*.json") if not any(
            part in {".git", "node_modules", "dist", "build", ".venv"} for part in p.parts
        ))
    files = sorted(set(files))
    report_entries = []
    changed_count = 0
    for path in files:
        result, changed = audit_file(path, args.apply_safe_fixes)
        if result["issues"] or result["safe_fixes"]:
            report_entries.append(result)
        changed_count += int(changed)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "roots": [root.as_posix() for root in roots],
        "missing_roots": missing_roots,
        "files_checked": len(files),
        "files_with_findings": len(report_entries),
        "safe_fixes_applied": changed_count,
        "mode": "apply-safe-fixes" if args.apply_safe_fixes else "report-only",
        "limitations": [
            "A source URL does not prove that it supports the associated claim.",
            "Automated checks cannot certify meanings, etymologies, religious claims, or translation fluency.",
            "Potential aliases and mismatches are reported for human review and are never auto-merged or renamed.",
        ],
        "findings": report_entries,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = Counter(issue["code"] for row in report_entries for issue in row["issues"])
    print(json.dumps({
        "files_checked": len(files),
        "files_with_findings": len(report_entries),
        "safe_fixes_applied": changed_count,
        "issue_counts": dict(sorted(counts.items())),
        "report": report_path.as_posix(),
        "missing_roots": missing_roots,
    }, ensure_ascii=False, indent=2))
    return 1 if any(issue["code"] == "INVALID_JSON" for row in report_entries for issue in row["issues"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
