#!/usr/bin/env python3
"""Carefully improve boilerplate core_meaning fields without inventing lexical claims."""
import json
from pathlib import Path
from collections import Counter

ROOT = Path("upgrading/names_upgraded/islamic")
REPORT = Path("upgrading/CORE_MEANING_UPGRADE_REPORT.json")

def upgrade(data):
    cm = data.get("core_meaning")
    et = data.get("etymology") or {}
    if not isinstance(cm, dict):
        return Counter()
    before = dict(cm)
    name = (data.get("name") or data.get("slug") or "This name").strip()
    short = (cm.get("short_meaning") or "").strip()
    primary = (cm.get("primary_meaning") or "").strip()
    literal = (cm.get("literal_meaning") or "").strip()
    language = (et.get("primary_language") or "").strip()
    lexical_form = (et.get("lexical_form") or "").strip()
    root = (et.get("root") or "").strip()
    root_translit = (et.get("root_transliteration") or "").strip()
    morphology = (et.get("morphology") or "").strip()
    confidence = (cm.get("meaning_confidence") or "").upper()
    all_meaning = " ".join((short, primary, literal)).lower()
    if (not short or confidence == "LOW" or any(term in all_meaning for term in
            ("unverified", "unresolved", "not established", "not sufficiently established",
             "exact lexical gloss unresolved"))):
        return Counter()

    changes = Counter()
    generic_primary = any(phrase in primary for phrase in (
        "is an Arabic-origin name meaning", "is a Persian-origin name meaning",
        "is an Urdu-origin name meaning", "is an Islamic name meaning",
        "is a name meaning"
    ))
    if generic_primary and lexical_form and language and language.lower() not in ("unknown", "unverified"):
        gloss = short.rstrip(".; ")
        root_clause = ""
        if root and root_translit:
            root_clause = f" The record associates the form with root {root} ({root_translit})."
        elif root:
            root_clause = f" The recorded root is {root}."
        morph = morphology.lower()
        if "feminine" in morph:
            morph_clause = " The record identifies the form as feminine."
        elif "plural" in morph:
            morph_clause = " The record identifies the form as plural."
        elif "active participle" in morph:
            morph_clause = " The record identifies the form as an active participle."
        elif "participle" in morph and "masculine" in morph:
            morph_clause = " The record identifies the form as a masculine participle."
        else:
            morph_clause = ""
        cm["primary_meaning"] = (
            f"{name} corresponds to the {language} form {lexical_form} and is glossed in this record "
            f"as “{gloss}.”{root_clause}{morph_clause} The lexical gloss describes the word-form; "
            "Qur’anic occurrence, religious recommendation, popularity, and a name-bearer’s character "
            "are separate claims and are not established by this gloss alone."
        )
        changes["primary_meaning_improved"] += 1

    if (literal.startswith("The name is the Arabic word itself") or
        literal.startswith("The name is the Persian word itself") or
        literal.startswith("The name is the word itself")):
        cm["literal_meaning"] = short
        changes["literal_meaning_fixed"] += 1

    if cm != before:
        changes["records_changed"] += 1
    return changes

def main():
    totals = Counter()
    changed_files = []
    scanned = 0
    errors = []
    for path in sorted(ROOT.glob("*.json")):
        if path.name.startswith("PROGRESS_") or path.name in ("manifest.json", "index.json"):
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            data = doc.get("data", {})
            scanned += 1
            counts = upgrade(data)
            if counts.get("records_changed"):
                path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                changed_files.append(path.name)
            totals.update(counts)
        except Exception as exc:
            errors.append({"file": path.name, "error": str(exc)})
    report = {
        "task": "core_meaning quality upgrade",
        "scope": str(ROOT),
        "records_scanned": scanned,
        "records_changed": totals.get("records_changed", 0),
        "primary_meaning_improved": totals.get("primary_meaning_improved", 0),
        "literal_meaning_fixed": totals.get("literal_meaning_fixed", 0),
        "changed_files": changed_files,
        "errors": errors,
        "policy": [
            "No new source, root, language, Qur'anic-status, religious-prescription, popularity, or gender claim was invented.",
            "Records marked low-confidence or explicitly unverified were left unchanged.",
            "Meaning confidence, evidence, etymology, translations, slugs, and unrelated fields were not changed.",
            "Only boilerplate primary meanings and generic literal-meaning placeholders were revised."
        ]
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit(f"Stopped: {len(errors)} JSON files could not be processed; see {REPORT}")
    print(json.dumps({k: report[k] for k in (
        "records_scanned", "records_changed", "primary_meaning_improved", "literal_meaning_fixed"
    )}, indent=2))

if __name__ == "__main__":
    main()
