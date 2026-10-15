#!/usr/bin/env python3
"""Conservative structural repair for NameVerse name JSON files.

Repairs deterministic URL/breadcrumb/FAQ structured-data consistency only.
It does NOT invent or rewrite meanings, etymologies, religious claims, or translations.
Default is report-only; pass --apply to write changes.
"""
import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timezone

SITE = "https://nameverse.site"
RELIGION_LABELS = {
    "islamic": "Islamic Names",
    "christian": "Christian Names",
    "hindu": "Hindu Names",
    "italian": "Italian Names",
}


def normalized_question(value):
    return " ".join(str(value or "").casefold().split()).rstrip(" ?.!؟")


def faq_pair(item):
    if not isinstance(item, dict):
        return "", ""
    q = item.get("q", item.get("question", ""))
    a = item.get("a", item.get("answer", ""))
    return str(q or "").strip(), str(a or "").strip()


def get_graph(data):
    sd = data.get("structured_data")
    if not isinstance(sd, dict):
        sd = {"@context": "https://schema.org", "@graph": []}
        data["structured_data"] = sd
    graph = sd.get("@graph")
    if not isinstance(graph, list):
        graph = []
        sd["@graph"] = graph
    return graph


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="upgrading/names_upgraded/islamic")
    ap.add_argument("--site", default=SITE)
    ap.add_argument("--apply", action="store_true", help="write deterministic structural fixes")
    ap.add_argument("--report", default="name-structural-repair-report.json")
    args = ap.parse_args()
    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Dataset folder does not exist: {root}")

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "mode": "apply" if args.apply else "report_only",
        "files_scanned": 0,
        "files_changed": 0,
        "invalid_json": [],
        "records": [],
    }
    religion = root.name.lower()
    religion_label = RELIGION_LABELS.get(religion, f"{religion.title()} Names")

    for path in sorted(root.rglob("*.json")):
        if path.name.startswith("PROGRESS_"):
            continue
        report["files_scanned"] += 1
        row = {"path": str(path), "issues": [], "changes": []}
        try:
            raw = path.read_text(encoding="utf-8")
            obj = json.loads(raw)
        except Exception as exc:
            report["invalid_json"].append({"path": str(path), "error": str(exc)})
            continue
        data = obj.get("data")
        if not isinstance(data, dict):
            row["issues"].append("missing data object")
            report["records"].append(row)
            continue

        slug = str(data.get("slug") or path.stem).strip().strip("/")
        display_name = str(data.get("name") or data.get("identity", {}).get("display_name") or slug)
        canonical = f"{args.site.rstrip('/')}/names/{religion}/{slug}"
        seo = data.get("seo")
        if not isinstance(seo, dict):
            seo = {}
            data["seo"] = seo
        if seo.get("canonical_url") != canonical:
            row["issues"].append("canonical missing or inconsistent with route slug")
            row["changes"].append("seo.canonical_url")
            if args.apply:
                seo["canonical_url"] = canonical

        graph = get_graph(data)
        breadcrumb = next((n for n in graph if isinstance(n, dict) and n.get("@type") == "BreadcrumbList"), None)
        expected_crumbs = [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{args.site.rstrip('/')}/"},
            {"@type": "ListItem", "position": 2, "name": religion_label, "item": f"{args.site.rstrip('/')}/names/{religion}"},
            {"@type": "ListItem", "position": 3, "name": display_name, "item": canonical},
        ]
        if breadcrumb is None:
            row["issues"].append("BreadcrumbList missing")
            row["changes"].append("structured_data.@graph.BreadcrumbList")
            if args.apply:
                graph.append({"@type": "BreadcrumbList", "itemListElement": expected_crumbs})
        elif breadcrumb.get("itemListElement") != expected_crumbs:
            row["issues"].append("breadcrumb URLs/names inconsistent with canonical route")
            row["changes"].append("structured_data.@graph.BreadcrumbList.itemListElement")
            if args.apply:
                breadcrumb["itemListElement"] = expected_crumbs

        faq = data.get("faq")
        if isinstance(faq, list):
            clean_faq, seen = [], set()
            for item in faq:
                q, a = faq_pair(item)
                if not q or not a:
                    row["issues"].append("FAQ entry missing question or answer")
                    continue
                key = normalized_question(q)
                if key in seen:
                    row["issues"].append("duplicate FAQ question: " + q)
                    continue
                seen.add(key)
                clean_faq.append(item)
            if len(clean_faq) != len(faq):
                row["changes"].append("faq (remove exact duplicate/invalid entries)")
                if args.apply:
                    data["faq"] = clean_faq
                    faq = clean_faq

            expected_entities = []
            for item in faq:
                q, a = faq_pair(item)
                if q and a:
                    expected_entities.append({
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a},
                    })
            faq_node = next((n for n in graph if isinstance(n, dict) and n.get("@type") == "FAQPage"), None)
            current_entities = faq_node.get("mainEntity") if isinstance(faq_node, dict) else None
            if current_entities != expected_entities:
                row["issues"].append("FAQPage structured data differs from FAQ array")
                row["changes"].append("structured_data.@graph.FAQPage.mainEntity")
                if args.apply:
                    if faq_node is None:
                        graph.append({"@type": "FAQPage", "mainEntity": expected_entities})
                    else:
                        faq_node["mainEntity"] = expected_entities

        meaning = data.get("core_meaning") if isinstance(data.get("core_meaning"), dict) else {}
        confidence = str(meaning.get("meaning_confidence", "")).strip().upper()
        sources = data.get("evidence", {}).get("sources", []) if isinstance(data.get("evidence"), dict) else []
        traceable = any(
            (isinstance(s, str) and s.strip().startswith(("https://", "http://"))) or
            (isinstance(s, dict) and any(str(s.get(k, "")).startswith(("https://", "http://")) for k in ("url", "source_url", "uri", "href")))
            for s in (sources if isinstance(sources, list) else [])
        )
        if confidence in {"", "LOW", "UNKNOWN", "UNVERIFIED", "NOT_ESTABLISHED"} and traceable:
            row["issues"].append("low/unverified core meaning has source URLs; verify claim-level support")
        if not traceable:
            row["issues"].append("no traceable source URL; meaning/origin claims need evidence review")
        trans_quality = data.get("translation_quality", {})
        if isinstance(trans_quality, dict) and trans_quality.get("native_review_required"):
            row["issues"].append("one or more translations still require native-speaker review")

        if row["changes"]:
            if args.apply:
                path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                report["files_changed"] += 1
            row["status"] = "changed" if args.apply else "would_change"
        else:
            row["status"] = "review_only" if row["issues"] else "pass"
        report["records"].append(row)

    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "mode": report["mode"],
        "files_scanned": report["files_scanned"],
        "files_changed": report["files_changed"],
        "invalid_json": len(report["invalid_json"]),
        "records_with_issues": sum(bool(r["issues"]) for r in report["records"]),
        "report": args.report,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
