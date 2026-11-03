#!/usr/bin/env python3
"""Build source-checked v9 name records from small hand-written spec files.

Spec:   upgrading/v9_specs/<tradition>/<slug>.json   (see v9_specs/README.md)
Output: upgrading/names_upgraded/<tradition>/<slug>.json  (+ --news copy)
Tracker: upgrading/V9_UPGRADE_TRACKER.json / .md

Every claim in a spec names a source id and a few `terms`. The source page is
fetched and each term must literally occur in it (case/diacritic-insensitive)
or the record is NOT written. This is a guard against invented facts, not a
proof of truth: the terms are chosen by the editor.

Usage:
  v9_upgrade.py --news ../news [SPEC ...]      build given specs (default: all)
  v9_upgrade.py --tracker-only                 rebuild tracker markdown
"""
import argparse, datetime as dt, hashlib, html, json, re, sys, unicodedata, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UP = ROOT / "upgrading"
SPECS = UP / "v9_specs"
CACHE = SPECS / ".source_cache"
OUT = UP / "names_upgraded"
TRACKER = UP / "V9_UPGRADE_TRACKER.json"
QUEUE = UP / "V9_FAMOUS_QUEUE.json"
UA = "NameVerseSourceCheck/1.0 (+https://nameverse.site; editorial source verification)"
SET_NAME = {"islamic": "NameVerse Islamic Names", "christian": "NameVerse Christian Names", "hindu": "NameVerse Hindu Names"}
HIDDEN = ["personality_associations", "hidden_personality_traits", "popularity", "real_world_usage", "name_story"]


def norm(s):
    s = unicodedata.normalize("NFKD", html.unescape(str(s)))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u0640", "").replace("’", "'").replace("‘", "'").replace("ʿ", "").replace("ʾ", "")
    return re.sub(r"\s+", " ", s).casefold()


def fetch(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".txt")
    if key.exists():
        return key.read_text(encoding="utf-8")
    u = urllib.parse.urlparse(url)
    title = urllib.parse.unquote(u.path.split("/wiki/", 1)[1]) if "/wiki/" in u.path else None
    if title and u.netloc.endswith("wikipedia.org"):
        api = f"https://{u.netloc}/w/api.php?" + urllib.parse.urlencode(
            {"action": "query", "prop": "extracts", "explaintext": 1, "titles": title, "redirects": 1, "format": "json"})
        pages = json.loads(get(api))["query"]["pages"]
        text = "\n".join(p.get("extract", "") for p in pages.values() if "missing" not in p)
    elif title and u.netloc.endswith("wiktionary.org"):
        api = f"https://{u.netloc}/w/api.php?" + urllib.parse.urlencode(
            {"action": "parse", "page": title, "prop": "wikitext", "redirects": 1, "format": "json"})
        text = json.loads(get(api)).get("parse", {}).get("wikitext", {}).get("*", "")
    else:
        raw = get(url)
        raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
        text = re.sub(r"<[^>]+>", " ", raw)
    if not text.strip():
        raise RuntimeError(f"empty or missing source page: {url}")
    key.write_text(text, encoding="utf-8")
    return text


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def verify(spec):
    src = {s["id"]: s for s in spec["sources"]}
    problems, checked = [], 0
    for c in spec["claims"]:
        s = src.get(c["source"])
        if not s:
            problems.append(f"claim cites unknown source {c['source']}: {c['claim']}"); continue
        try:
            text = norm(fetch(s["url"]))
        except Exception as e:  # noqa: BLE001
            problems.append(f"cannot fetch {s['url']}: {e}"); continue
        missing = [t for t in c["terms"] if norm(t) not in text]
        if missing:
            problems.append(f"[{c['source']}] terms not found {missing} for: {c['claim']}")
        else:
            checked += 1
    return checked, problems


def load_existing(tradition, slug, news):
    for base in ([OUT / tradition] + ([Path(news) / "public/names" / tradition] if news else [])):
        p = base / f"{slug}.json"
        if p.exists():
            o = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(o, dict) and isinstance(o.get("data"), dict):
                return o["data"]
            if isinstance(o, dict) and o.get("name"):
                return o  # flat christian/hindu schema
    return None


def numerology_from(old):
    if not old:
        return None
    n = old.get("numerology") if isinstance(old.get("numerology"), dict) else {}
    la = old.get("lucky_attributes") if isinstance(old.get("lucky_attributes"), dict) else {}
    get_ = lambda k: n.get(k) or la.get(k) or old.get(k)
    num = get_("lucky_number")
    if not num:
        return None
    return {
        "status": "interpretive", "render": True,
        "lucky_number": num, "life_path_number": get_("life_path_number"),
        "lucky_day": str(get_("lucky_day") or "").strip("()"),
        "lucky_colors": get_("lucky_colors") or [], "lucky_stone": get_("lucky_stone") or "",
        "meaning": n.get("meaning") or old.get("numerology_meaning") or "",
        "note": "Numerology is an optional interpretive layer, not a linguistic fact.",
    }


def build(spec, old, now):
    name, slug, trad = spec["name"], spec["slug"], spec["tradition"]
    et, rel, cul, hist = spec["etymology"], spec.get("religion", {}), spec.get("cultural", {}), spec.get("history", {})
    faq = spec["faq"]
    claims = [{"claim": c["claim"], "evidence_type": c["source"], "confidence": c.get("confidence", "HIGH")} for c in spec["claims"]]
    d = {
        "name": name, "slug": slug, "content_revision": "v9", "page_type": "name_meaning",
        "identity": {
            "display_name": name, "normalized_name": slug, "name_type": "given_name",
            "gender": spec["gender"], "gender_confidence": "HIGH", "gender_note": spec.get("gender_note", ""),
            "alternate_spellings": spec.get("variants", []), "name_status": "attested",
            "search_variants": sorted({slug, *[v.lower() for v in spec.get("variants", [])]}),
        },
        "core_meaning": {
            "short_meaning": spec["short_meaning"], "primary_meaning": spec["primary_meaning"],
            "literal_meaning": spec.get("literal_meaning", ""), "meaning_explanation": spec["meaning_explanation"],
            "meaning_confidence": spec.get("meaning_confidence", "HIGH"),
        },
        "etymology": {
            "primary_language": et["language"], "lexical_form": et.get("lexical_form", ""),
            "transliteration": et.get("transliteration", ""), "root": et.get("root", ""),
            "root_transliteration": et.get("root_transliteration", ""), "morphology": et.get("morphology", ""),
            "etymological_meaning": et.get("meanings", []), "etymology_explanation": et["explanation"],
            "etymology_confidence": et.get("confidence", "HIGH"),
            "false_etymology_warning": et.get("false_etymology_warning", ""),
        },
        "language": {"primary": et["language"], "associated_languages": spec.get("languages", [et["language"]]),
                     "language_confidence": "HIGH"},
        "origin": {"primary_origin": spec["origin"]["primary"], "origin_type": "linguistic", "origin_confidence": "HIGH",
                   "origin_explanation": spec["origin"]["explanation"],
                   "cultural_transmission": spec["origin"].get("transmission", [])},
        "religion": {
            "primary_association": rel.get("association", trad.title()),
            "religion_confidence": "HIGH", "religious_status": rel.get("status", ""),
            "religious_explanation": rel.get("explanation", ""),
            "quranic_status": {"is_quranic_name": bool(rel.get("quranic")), "quranic_reference": (rel.get("quranic") or {}).get("ref", ""),
                               "note": (rel.get("quranic") or {}).get("note", "")},
            "prophetic_status": {"prophet_association": bool(rel.get("prophet")), "reference": rel.get("prophet") or ""},
            "companion_status": {"known_companion_association": bool(rel.get("companion")), "reference": rel.get("companion") or ""},
        },
        "cultural_context": {"primary_cultural_associations": cul.get("associations", []),
                             "cultural_meaning": cul.get("meaning", ""), "impact": cul.get("impact", "")},
        "spiritual_meaning": {"status": "interpretive", "render": bool(spec.get("spiritual")),
                              "meaning": spec.get("spiritual", ""), "is_direct_religious_definition": False},
        "personality_associations": {"status": "not_verified", "render": False},
        "hidden_personality_traits": {"status": "not_verified", "render": False},
        "translations": {k: {"name": v["name"], "script": v["name"], "meaning": v.get("meaning", ""),
                             "long_meaning": v.get("long_meaning", "")} for k, v in spec.get("translations", {}).items()},
        "translation_quality": {"strategy": "semantic_translation", "confidence": "MEDIUM", "native_review_required": True},
        "pronunciation": spec.get("pronunciation", {}),
        "name_variants": {"romanized_variants": spec.get("variants", []), "script_variants": spec.get("script_variants", []),
                          "variant_notes": spec.get("variant_notes", "")},
        "related_names": spec.get("related", []),
        "historical_context": {"status": "verified" if hist else "none", "known_linguistic_history": hist.get("items", []),
                               "historical_person_association": hist.get("person", ""),
                               "historical_event_association": hist.get("event", ""),
                               "historical_claim_confidence": "HIGH" if hist else ""},
        "modern_usage": {"status": "qualitative", "modern_context": spec.get("modern_usage", "")},
        "popularity": {"status": "not_measured", "render": False, "score": None, "by_region": []},
        "celebrity_usage": {"status": "verified" if spec.get("celebrities") else "none",
                            "verified": spec.get("celebrities", []), "note": ""},
        "faq": [{"q": f["q"], "a": f["a"]} for f in faq],
        "seo": {"title": spec["seo"]["title"], "meta_description": spec["seo"]["meta_description"],
                "keywords": spec["seo"].get("keywords", []), "description_paragraph": spec["primary_meaning"]},
        "content_quality": {"overall_status": "source-checked", "fabricated_content_removed": True,
                            "meaning_authenticity": "Each core claim checked against a cited source page"},
        "evidence": {"sources": spec["sources"], "core_claims": claims,
                     "verification_method": "v9_upgrade.py: every claim's key terms located in the cited source text"},
        "provenance": {"pipeline": "NameVerse v9 source-checked upgrade", "upgraded_from": (old or {}).get("content_revision") or ("flat" if old else "new"),
                       "processed_at": now},
        "structured_data": {"@context": "https://schema.org", "@graph": [
            {"@type": "DefinedTerm", "name": name, "description": f"{name} — {spec['short_meaning']}",
             "inDefinedTermSet": {"@type": "DefinedTermSet", "name": SET_NAME.get(trad, "NameVerse Names")}},
            {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": f["q"],
                                                 "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]}]},
        "editorial_validation": {"needs_manual_verification": False, "confidence": "HIGH",
                                 "flags": ["translations pending native-speaker review"], "reviewed_at": now},
        "render_policy": {"render_verified": True, "render_interpretive": True, "hide_unverified": False,
                          "hidden_sections": HIDDEN + ([] if spec.get("spiritual") else ["spiritual_meaning"]),
                          "source_checked": True},
    }
    if trad == "islamic" and spec.get("naming_context"):
        d["islamic_naming_context"] = {"can_be_used_by_muslims": True, **spec["naming_context"]}
    if rel.get("biblical"):
        d["biblical_reference"] = {"is_biblical": True, **rel["biblical"]}
    if rel.get("saint"):
        d["saint_reference"] = {"is_saint_name": True, **rel["saint"]}
    if rel.get("vedic"):
        d["vedic_reference"] = {"is_vedic": True, "reference": rel["vedic"]}
    pop = (old or {}).get("popularity_score")
    if isinstance(pop, (int, float)):
        d["popularity_score"] = pop  # internal sort key used by news; not a statistic
    num = numerology_from(old)
    if num:
        d["numerology"] = num
        d["lucky_attributes"] = {k: num[k] for k in ("lucky_number", "lucky_day", "lucky_colors", "lucky_stone")}
    return {"schema_version": "super-2.0", "success": True, "data": d}


def write_tracker(tracker):
    TRACKER.write_text(json.dumps(tracker, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    queue = json.loads(QUEUE.read_text(encoding="utf-8")) if QUEUE.exists() else {}
    done = tracker["records"]
    lines = ["# v9 source-checked upgrade tracker", "",
             "Generated by `upgrading/scripts/v9_upgrade.py` — do not edit by hand.", "",
             f"Upgraded records: **{len(done)}**", ""]
    for trad in ("islamic", "christian", "hindu"):
        q = queue.get(trad, [])
        up = sorted(k.split("/", 1)[1] for k in done if k.startswith(trad + "/"))
        lines += [f"## {trad.title()} — {len(up)} upgraded" + (f" of {len(q)} queued famous names" if q else ""), ""]
        lines += ["| Name | Action | Sources | Claims checked | Date |", "|---|---|---|---|---|"]
        for s in up:
            r = done[f"{trad}/{s}"]
            lines.append(f"| {r['name']} | {r['action']} | {r['sources']} | {r['claims_checked']} | {r['date'][:10]} |")
        pending = [s for s in q if f"{trad}/{s}" not in done]
        if pending:
            lines += ["", f"Next in queue ({len(pending)}): " + ", ".join(pending[:40]) + (" …" if len(pending) > 40 else "")]
        lines.append("")
    TRACKER.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="*")
    ap.add_argument("--news", help="path to the news repo; also writes public/names/<tradition>/<slug>.json")
    ap.add_argument("--tracker-only", action="store_true")
    a = ap.parse_args()
    tracker = json.loads(TRACKER.read_text(encoding="utf-8")) if TRACKER.exists() else {"records": {}}
    if a.tracker_only:
        write_tracker(tracker); return
    paths = [Path(p) for p in a.specs] or sorted(SPECS.glob("*/*.json"))
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    failed = 0
    for p in paths:
        spec = json.loads(p.read_text(encoding="utf-8"))
        checked, problems = verify(spec)
        if problems:
            failed += 1
            print(f"FAIL {p}:"); [print("   -", x) for x in problems]; continue
        old = load_existing(spec["tradition"], spec["slug"], a.news)
        rec = build(spec, old, now)
        text = json.dumps(rec, ensure_ascii=False, indent=2) + "\n"
        targets = [OUT / spec["tradition"]] + ([Path(a.news) / "public/names" / spec["tradition"]] if a.news else [])
        for t in targets:
            t.mkdir(parents=True, exist_ok=True); (t / f"{spec['slug']}.json").write_text(text, encoding="utf-8")
        key = f"{spec['tradition']}/{spec['slug']}"
        tracker["records"][key] = {"name": spec["name"], "action": "upgraded" if old else "new page",
                                   "sources": len(spec["sources"]), "claims_checked": checked, "date": now}
        print(f"OK   {key}: {checked} claims verified against {len(spec['sources'])} sources")
    write_tracker(tracker)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
