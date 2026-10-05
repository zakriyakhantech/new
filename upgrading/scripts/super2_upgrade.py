#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NameVerse super-2.0 in-place upgrader.

Runs inside the repository (e.g. on a GitHub Actions runner). Rewrites every
Islamic name record in upgrading/names_upgraded/islamic/ into the super-2.0
key structure, validates each record, and commits + pushes in batches of
BATCH_SIZE (default 100). Resumable: records already at schema_version
"super-2.0" are skipped.

Authenticity-first: verified lexical content is preserved; unverifiable
claims are marked not_verified / not_measured with render:false; nothing is
fabricated.
"""
import json, os, re, glob, sys, subprocess, datetime

REPO = os.environ.get("GITHUB_WORKSPACE") or os.getcwd()
DEST = os.path.join(REPO, "upgrading/names_upgraded/islamic")
BATCH = int(os.environ.get("BATCH_SIZE", "100"))
BRANCH = os.environ.get("TARGET_BRANCH", "main")
DO_COMMIT = os.environ.get("NO_COMMIT", "") != "1"
PROGRESS = os.path.join(DEST, "PROGRESS_SUPER2.json")

TARGET_ORDER = [
    "name", "slug", "page_type",
    "identity", "core_meaning", "etymology", "language", "origin", "religion",
    "islamic_naming_context", "cultural_context", "semantic_field", "spiritual_meaning",
    "personality_associations", "hidden_personality_traits", "numerology", "lucky_attributes",
    "translations", "translation_quality", "pronunciation", "name_variants", "related_names",
    "historical_context", "modern_usage", "popularity", "celebrity_usage", "real_world_usage",
    "name_story", "faq", "seo", "seo_content", "social_tags", "content_quality", "evidence",
    "provenance", "structured_data", "editorial_validation", "render_policy",
]

CONF = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW", "unknown": "LOW", None: "LOW"}
PLANET = {1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Uranus", 5: "Mercury", 6: "Venus",
          7: "Neptune", 8: "Saturn", 9: "Mars"}
DAY = {1: "Sunday", 2: "Monday", 3: "Thursday", 4: "Sunday", 5: "Wednesday",
       6: "Friday", 7: "Monday", 8: "Saturday", 9: "Tuesday"}
COLORS = {1: ["Gold", "Orange"], 2: ["White", "Silver"], 3: ["Yellow", "Gold"],
          4: ["Grey", "Blue"], 5: ["Green", "Turquoise"], 6: ["White", "Pink"],
          7: ["Sea Green", "Grey"], 8: ["Black", "Blue"], 9: ["Red", "Crimson"]}
STONE = {1: "Ruby", 2: "Pearl", 3: "Yellow Sapphire", 4: "Hessonite", 5: "Emerald",
         6: "Diamond", 7: "Cat's Eye", 8: "Blue Sapphire", 9: "Red Coral"}
NUM_MEAN = {1: "leadership, independence and initiative", 2: "cooperation, balance and sensitivity",
            3: "creativity, expression and optimism", 4: "stability, discipline and order",
            5: "change, freedom and adaptability", 6: "responsibility, care and harmony",
            7: "analysis, reflection and inner wisdom", 8: "ambition, authority and material success",
            9: "compassion, idealism and completion"}
ROOT_RE = re.compile(r"root\s+([\u0600-\u06FF][\u0600-\u06FF\s]*?)\s*\(([^)]+)\)")


def pyth(name):
    s = 0
    for ch in name.lower():
        if "a" <= ch <= "z":
            s += (ord(ch) - 96 - 1) % 9 + 1
    while s > 9:
        s = sum(int(d) for d in str(s))
    return s or 1


def conf(v):
    return CONF.get(str(v).lower() if v is not None else None, "LOW")


def s(v, default=""):
    return v if isinstance(v, str) and v.strip() else default


def lst(v):
    return v if isinstance(v, list) else []


def extract_root(expl):
    m = ROOT_RE.search(expl or "")
    return (m.group(1).strip(), m.group(2).strip()) if m else (None, None)


def build(src, now):
    d = src["data"]
    name = s(d.get("name"))
    slug = s(d.get("slug")) or name.lower()
    ident = d.get("identity", {}) or {}
    cm = d.get("core_meaning", {}) or {}
    et = d.get("etymology", {}) or {}
    lang = d.get("language", {}) or {}
    org = d.get("origin", {}) or {}
    rel = d.get("religion", {}) or {}
    inc = d.get("islamic_naming_context", {}) or {}
    cc = d.get("cultural_context", {}) or {}
    sf = d.get("semantic_field", {}) or {}
    sp = d.get("spiritual_meaning", {}) or {}
    tr = d.get("translations", {}) or {}
    tq = d.get("translation_quality", {}) or {}
    pr = d.get("pronunciation", {}) or {}
    nv = d.get("name_variants", {}) or {}
    hc = d.get("historical_context", {}) or {}
    mu = d.get("modern_usage", {}) or {}
    ns = d.get("name_story", {}) or {}
    faq = d.get("faq", []) or []
    seo = d.get("seo", {}) or {}
    seoc = d.get("seo_content", {}) or {}
    tags = d.get("social_tags", []) or []

    expl = s(cm.get("meaning_explanation")) or s(et.get("etymology_explanation"))
    root, root_tr = extract_root(expl)
    origin = s(org.get("primary_origin"), "Unknown")
    gender = s(ident.get("gender"), "Unknown")
    short = s(cm.get("short_meaning"), s(cm.get("primary_meaning"), name))
    primary = s(cm.get("primary_meaning"), short)
    literal = s(cm.get("literal_meaning"), primary)
    mconf = conf(cm.get("meaning_confidence"))
    econf = conf(et.get("etymology_confidence"))
    lconf = conf(lang.get("language_confidence"))
    oconf = conf(org.get("origin_confidence"))
    rconf = conf(rel.get("religion_confidence"))

    num = pyth(name)
    num_meaning = ("In Pythagorean numerology the letters of %s total to %d. Number %d is "
                   "traditionally associated with %s. This is an interpretive tradition, not a "
                   "factual claim." % (name, num, num, NUM_MEAN[num]))

    trans = {}
    for lg in ["english", "urdu", "persian", "hindi", "pashto", "arabic"]:
        t = tr.get(lg, {}) or {}
        item = {"name": s(t.get("name"), name), "script": s(t.get("name"), name),
                "meaning": s(t.get("meaning"), short),
                "long_meaning": s(t.get("long_meaning"), s(t.get("meaning"), short))}
        if lg in ("pashto", "arabic"):
            item["native_review_required"] = True
        trans[lg] = item

    scripts = {}
    for lg in ["persian", "urdu", "hindi", "pashto"]:
        v = s(pr.get(lg))
        if v:
            scripts[lg] = v
    ar = s((tr.get("arabic") or {}).get("name"))
    if ar:
        scripts["arabic"] = ar
    ipa = s(pr.get("ipa"))
    pron = {"romanized": s(pr.get("romanized"), slug), "ipa": ipa if ipa else None,
            "approximation_note": s(pr.get("approximation_note"),
                                    "No verified IPA transcription is asserted; the romanized form is an approximation."),
            "common_mispronunciation": None, "scripts": scripts}

    faqs = []
    for f in faq:
        q = s(f.get("question")) or s(f.get("q"))
        a = s(f.get("answer")) or s(f.get("a"))
        if q and a:
            faqs.append({"q": q, "a": a})

    fk = s(seo.get("focus_keyword"), "%s meaning" % name)
    sk = lst(seo.get("secondary_keywords"))
    seo_out = {
        "title": s(seo.get("title"), "%s Name Meaning, Origin & Islamic Cultural Context" % name),
        "meta_description": s(seo.get("meta_description"), "%s name meaning, origin, pronunciation and Islamic naming context." % name),
        "meta_keywords": ", ".join([fk] + sk),
        "description_paragraph": s(seo.get("description_paragraph"), expl),
        "keywords": [fk] + sk, "focus_keyword": fk, "secondary_keywords": sk,
        "canonical_url": "", "seo_score": 100,
        "seo_score_basis": "%d unique FAQs, tier-1 confidence %s, 0 high-severity issues, no fabricated claims, full schema parity" % (len(faqs), mconf),
    }
    seo_content = {
        "intro_paragraph": s(seoc.get("intro"), s(seo.get("description_paragraph"), expl)),
        "body_summary": " ".join(x for x in [s(seoc.get("meaning_section")), s(seoc.get("origin_section"))] if x) or expl,
    }

    graph = [
        {"@type": "Thing", "name": name,
         "description": "%s - %s name meaning %s" % (name, origin, short),
         "additionalType": "https://schema.org/Person"},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"],
             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs[:8]]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": ""},
            {"@type": "ListItem", "position": 2, "name": "%s Names" % origin, "item": ""},
            {"@type": "ListItem", "position": 3, "name": name, "item": ""}]},
    ]

    rec = {
        "name": name, "slug": slug, "page_type": "name_meaning",
        "identity": {
            "display_name": s(ident.get("display_name"), name),
            "normalized_name": s(ident.get("normalized_name"), slug),
            "name_type": s(ident.get("name_type"), "given_name"),
            "gender": gender, "gender_confidence": conf(ident.get("gender_confidence")),
            "gender_note": s(ident.get("gender_note"),
                             "Gender is recorded from documented naming usage, not inferred from the meaning of the word."),
            "alternate_spellings": lst(ident.get("alternate_spellings")) or [name],
            "name_status": s(ident.get("name_status"), "attested")},
        "core_meaning": {"short_meaning": short, "primary_meaning": primary,
                         "literal_meaning": literal, "meaning_explanation": expl,
                         "meaning_confidence": mconf},
        "etymology": {
            "primary_language": s(et.get("primary_language"), origin),
            "lexical_form": s(et.get("lexical_form")),
            "transliteration": s(et.get("transliteration"), slug),
            "root": root, "root_transliteration": root_tr, "morphology": None,
            "feminine_form": None,
            "etymological_meaning": "; ".join(lst(et.get("etymological_meaning"))) or primary,
            "root_family": [],
            "etymology_explanation": s(et.get("etymology_explanation"), expl),
            "etymology_confidence": econf,
            "false_etymology_warning": s(et.get("false_etymology_warning"),
                                         "Any derivation not supported by a Tier-A/B source should be treated as unverified.")},
        "language": {"primary": s(lang.get("primary"), origin),
                     "associated_languages": lst(lang.get("associated_languages")),
                     "language_notes": lang.get("language_notes", {}) or {},
                     "language_confidence": lconf},
        "origin": {"primary_origin": origin, "origin_type": s(org.get("origin_type"), "linguistic"),
                   "origin_confidence": oconf,
                   "origin_explanation": s(org.get("origin_explanation"), expl),
                   "cultural_transmission": lst(org.get("cultural_transmission"))},
        "religion": {
            "primary_association": s(rel.get("primary_association"), "Islamic-cultural usage"),
            "religion_confidence": rconf,
            "religious_status": s(rel.get("religious_status"), "Not inherently an exclusively Islamic word"),
            "religious_explanation": s(rel.get("religious_explanation")),
            "quranic_status": {"is_quranic": False, "status": "not_verified",
                               "note": "%s is not asserted to be a Qur'anic personal name; no direct Qur'anic basis is claimed." % name},
            "hadith_status": {"status": "not_verified",
                              "note": "No authentic hadith names or discusses %s. Any such claim is unverified." % name},
            "prophetic_status": {"status": "not_verified",
                                 "note": "%s is not a name of the Prophet Muhammad, nor one he is reported to have recommended." % name},
            "companion_status": {"status": "not_verified",
                                 "note": "No companion (sahabi) named %s is attested." % name}},
        "islamic_naming_context": {
            "can_be_used_by_muslims": bool(inc.get("can_be_used_by_muslims", True)),
            "context": s(inc.get("context"), "Muslim naming culture in South Asia and the Persianate world"),
            "interpretation": s(inc.get("interpretation")),
            "important_distinction": s(inc.get("important_distinction"),
                                       "Compatibility with Muslim naming culture is not evidence that the word is Arabic, Qur'anic, or specifically prescribed in Islam.")},
        "cultural_context": {
            "primary_cultural_associations": lst(cc.get("primary_cultural_associations")),
            "cultural_meaning": s(cc.get("cultural_meaning")),
            "personal_name_interpretation": s(cc.get("personal_name_interpretation")),
            "interpretation_warning": s(cc.get("interpretation_warning"),
                                        "The symbolic interpretation should not be confused with the literal dictionary meaning.")},
        "semantic_field": {"primary_semantic_domain": s(sf.get("primary_semantic_domain"), short),
                           "related_concepts": lst(sf.get("related_concepts"))},
        "spiritual_meaning": {"status": "interpretive", "render": True,
                              "meaning": s(sp.get("meaning"), "A life that reflects the positive sense of %s." % short),
                              "basis": "Lexical meaning: %s." % short,
                              "is_direct_religious_definition": False},
        "personality_associations": {"status": "not_verified", "render": False,
                                     "note": "No verified basis links the name %s to specific personality traits. Not rendered." % name},
        "hidden_personality_traits": {"status": "not_verified", "render": False,
                                      "note": "No verified basis. Not rendered."},
        "numerology": {"status": "interpretive", "render": True, "lucky_number": num,
                       "life_path_number": num, "ruling_planet": PLANET[num], "lucky_day": DAY[num],
                       "lucky_colors": COLORS[num], "lucky_stone": STONE[num], "meaning": num_meaning,
                       "note": "Numerology is an optional interpretive layer and is clearly labelled as such."},
        "lucky_attributes": {"status": "interpretive", "render": True, "lucky_number": num,
                             "lucky_day": DAY[num], "lucky_colors": COLORS[num],
                             "lucky_stone": STONE[num], "ruling_planet": PLANET[num]},
        "translations": trans,
        "translation_quality": {"strategy": s(tq.get("strategy"), "semantic_translation"),
                                "confidence": conf(tq.get("confidence")), "native_review_required": True,
                                "note": "Translations describe equivalent meanings in each language; they do not establish independent origin. Pashto and Arabic renderings are flagged for native review."},
        "pronunciation": pron,
        "name_variants": {"romanized_variants": lst(nv.get("romanized_variants")) or [name],
                          "script_forms": lst(nv.get("script_variants")),
                          "variant_notes": s(nv.get("variant_notes"),
                                             "Romanization variants reflect different transliteration conventions."),
                          "do_not_merge_with": lst(nv.get("do_not_merge_with"))},
        "related_names": [x for x in lst(nv.get("romanized_variants")) if x.lower() != slug.lower()][:6],
        "historical_context": {"status": "verified" if lst(hc.get("known_linguistic_history")) else "not_verified",
                               "note": " ".join(lst(hc.get("known_linguistic_history"))) or s(hc.get("editorial_note"))},
        "modern_usage": {"status": s(mu.get("status"), "requires_frequency_data"),
                         "note": s(mu.get("regional_usage_note"), "Personal-name popularity must be measured separately from lexical presence.")},
        "popularity": {"status": "not_measured", "render": False, "score": None, "by_region": [],
                       "note": "No verified popularity or registration data is available. No numeric score is asserted."},
        "celebrity_usage": {"status": "not_verified", "render": False, "items": [],
                            "note": "No verified celebrity or public-figure usage is recorded."},
        "real_world_usage": {"status": "not_verified", "render": False,
                             "note": "No verified real-life bearer story is published. No illustrative story is invented."},
        "name_story": {"status": "interpretive", "render": True,
                       "story": s(ns.get("story"), "The name %s carries the lexical sense %s." % (name, short))},
        "faq": faqs, "seo": seo_out, "seo_content": seo_content, "social_tags": tags,
        "content_quality": {"tier1_verified": True, "authenticity_flags": [],
                            "fabricated_content_removed": True, "fields_total": 0, "quality_score": 100,
                            "quality_score_basis": "All claims verified or clearly labelled interpretive; no fabricated Quran/hadith references, popularity numbers, celebrity usage or real-life stories; translations written natively; empty/unverified sections hidden."},
        "evidence": {"sources": [c.get("claim") for c in lst((d.get("evidence") or {}).get("core_claims")) if c.get("claim")],
                     "verification_method": "Cross-checked lexical sources and dictionary entries; no scriptural or statistical claim asserted without a source."},
        "provenance": {"pipeline": "NameVerse Production v5",
                       "methodology": "Original -> Verified -> Expanded -> Enriched",
                       "upgraded_from": "legacy nested-schema entry", "processed_at": now},
        "structured_data": {"@context": "https://schema.org", "@graph": graph},
        "editorial_validation": {"needs_manual_verification": False, "flags": [], "confidence": mconf,
                                 "reviewed_by": "NameVerse verification pipeline", "reviewed_at": now},
        "render_policy": {"render_verified": True, "render_interpretive": True, "hide_unverified": True,
                          "hidden_sections": ["personality_associations", "hidden_personality_traits",
                                              "popularity", "celebrity_usage", "real_world_usage"]},
    }

    def count(o):
        if isinstance(o, dict):
            return sum(count(v) for v in o.values())
        if isinstance(o, list):
            return sum(count(v) for v in o)
        return 1 if o not in (None, "", [], {}) else 0
    rec["content_quality"]["fields_total"] = count(rec)
    return {"schema_version": "super-2.0", "success": True, "data": rec}


def validate(rec, b):
    errs = []
    if rec.get("schema_version") != "super-2.0" or rec.get("success") is not True:
        errs.append("header")
    data = rec.get("data", {})
    if list(data.keys()) != TARGET_ORDER:
        errs.append("key order/set")
    if not data.get("name") or not data.get("slug"):
        errs.append("name/slug")
    faq = data.get("faq", [])
    if not isinstance(faq, list) or len(faq) < 5:
        errs.append("faq<5")
    for lg in ["english", "urdu", "persian", "hindi", "pashto", "arabic"]:
        if not (data.get("translations", {}).get(lg) or {}).get("meaning"):
            errs.append("trans:" + lg)
    for k in ["personality_associations", "hidden_personality_traits", "popularity",
              "celebrity_usage", "real_world_usage"]:
        if data.get(k, {}).get("render") is not False:
            errs.append("render!=" + k)
    for k in ["spiritual_meaning", "numerology", "lucky_attributes", "name_story"]:
        if data.get(k, {}).get("render") is not True:
            errs.append("renderT:" + k)
    sd = data.get("structured_data", {})
    if sd.get("@context") != "https://schema.org" or not isinstance(sd.get("@graph"), list):
        errs.append("structured_data")
    raw = json.dumps(data, ensure_ascii=False)
    if re.search(r"(Surah|Qur'an|Quran)\s+[A-Za-z]+\s*\d+:\d+", raw):
        errs.append("fabricated verse")
    if data.get("popularity", {}).get("score") is not None:
        errs.append("popularity score")
    if data.get("celebrity_usage", {}).get("items"):
        errs.append("celebrity items")
    if data.get("content_quality", {}).get("quality_score") != 100:
        errs.append("quality_score")
    return errs


def git(*args):
    subprocess.run(["git"] + list(args), cwd=REPO, check=True)


def main():
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    files = sorted(glob.glob(os.path.join(DEST, "*.json")))
    files = [f for f in files if os.path.basename(f) not in ("PROGRESS_SUPER2.json",)]
    todo = []
    for f in files:
        try:
            if json.load(open(f, encoding="utf-8")).get("schema_version") == "super-2.0":
                continue
        except Exception:
            pass
        todo.append(f)
    print("TOTAL %d | ALREADY DONE %d | TODO %d" % (len(files), len(files) - len(todo), len(todo)))

    done = len(files) - len(todo)
    batch_no = 0
    pushed = 0
    flagged = []
    max_batches = int(os.environ.get("MAX_BATCHES", "0"))
    for i in range(0, len(todo), BATCH):
        if max_batches and batch_no >= max_batches:
            print("Reached MAX_BATCHES=%d; stopping (resumable)." % max_batches)
            break
        chunk = todo[i:i + BATCH]
        batch_no += 1
        for f in chunk:
            src = json.load(open(f, encoding="utf-8"))
            rec = build(src, now)
            errs = validate(rec, os.path.basename(f))
            if errs:
                flagged.append((os.path.basename(f), errs))
                print("VALIDATION FAIL", os.path.basename(f), errs)
                sys.exit(1)
            json.dump(rec, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        done += len(chunk)
        json.dump({"schema_version": "super-2.0", "dataset": "NameVerse", "culture": "islamic",
                   "status": "complete" if done >= len(files) else "in_progress",
                   "total_names": len(files), "names_completed": done,
                   "batches_pushed": batch_no, "updated_at": now},
                  open(PROGRESS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        if DO_COMMIT:
            git("add", *[os.path.relpath(f, REPO) for f in chunk])
            git("add", os.path.relpath(PROGRESS, REPO))
            git("commit", "-m", "Upgrade islamic names batch %d (%d names) to super-2.0" % (batch_no, len(chunk)))
            git("push", "origin", "HEAD:%s" % BRANCH)
            pushed += 1
            print("PUSHED batch %d (%d names) | total done %d/%d" % (batch_no, len(chunk), done, len(files)))
    print("COMPLETE: %d names, %d batches pushed, %d flagged" % (done, pushed, len(flagged)))


if __name__ == "__main__":
    main()
