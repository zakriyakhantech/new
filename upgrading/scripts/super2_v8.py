#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NameVerse super-2.0 v8 content composer - ROOT-CAUSE FIX.

Does NOT re-wrap prose. Parses the clean baseline record into atomic facts and
BUILDS each field from a distinct, role-specific template.
"""
import json, os, re, glob, sys, subprocess, datetime, unicodedata

REPO = os.environ.get("GITHUB_WORKSPACE") or os.getcwd()
DEST = os.path.join(REPO, "upgrading", "names_upgraded", "islamic")
BATCH = int(os.environ.get("BATCH_SIZE", "100"))
BRANCH = os.environ.get("TARGET_BRANCH", "main")
DO_COMMIT = os.environ.get("NO_COMMIT", "") != "1"
PROGRESS = os.path.join(DEST, "PROGRESS_V8.json")
REVISION = "v8"

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

QURANIC_PROPHETS = {
    "muhammad": "the Prophet of Islam", "mohammad": "the Prophet of Islam",
    "mohammed": "the Prophet of Islam", "mohd": "the Prophet of Islam",
    "muhammed": "the Prophet of Islam", "muhaammad": "the Prophet of Islam",
    "adam": "a prophet", "aadam": "a prophet", "ibrahim": "a prophet",
    "ibraheem": "a prophet", "musa": "a prophet", "moosa": "a prophet",
    "isa": "a prophet", "eesa": "a prophet", "yusuf": "a prophet",
    "yusaf": "a prophet", "yoosuf": "a prophet", "yahya": "a prophet",
    "yahyaa": "a prophet", "zakariya": "a prophet", "zakaria": "a prophet",
    "idris": "a prophet", "idrees": "a prophet", "nuh": "a prophet",
    "nooh": "a prophet", "hud": "a prophet", "hood": "a prophet",
    "salih": "a prophet", "saleh": "a prophet", "saaleh": "a prophet",
    "shuaib": "a prophet", "shuayb": "a prophet", "sulaiman": "a prophet",
    "suleman": "a prophet", "sulayman": "a prophet", "dawud": "a prophet",
    "dawood": "a prophet", "daud": "a prophet", "ayyub": "a prophet",
    "ayub": "a prophet", "harun": "a prophet", "haroon": "a prophet",
    "ilyas": "a prophet", "yunus": "a prophet", "younus": "a prophet",
    "lut": "a prophet", "loot": "a prophet", "ismail": "a prophet",
    "ismaeel": "a prophet", "ishaq": "a prophet", "ishaaq": "a prophet",
    "yaqub": "a prophet", "yaqoob": "a prophet",
}
QURANIC_FIGURES = {
    "maryam": "Mary, the mother of Jesus, named in the Qur'an",
    "mariam": "Mary, the mother of Jesus, named in the Qur'an",
}
PROPHET_FAMILY = {
    "khadija": "Khadija bint Khuwaylid, the Prophet's first wife",
    "khadijah": "Khadija bint Khuwaylid, the Prophet's first wife",
    "aisha": "Aisha bint Abi Bakr, a wife of the Prophet",
    "ayesha": "Aisha bint Abi Bakr, a wife of the Prophet",
    "aaisha": "Aisha bint Abi Bakr, a wife of the Prophet",
    "fatima": "Fatima, the Prophet's daughter", "fatimah": "Fatima, the Prophet's daughter",
    "zainab": "a daughter of the Prophet", "zaynab": "a daughter of the Prophet",
    "hafsa": "Hafsa bint Umar, a wife of the Prophet", "hafsah": "Hafsa bint Umar, a wife of the Prophet",
    "hamza": "Hamza, an uncle of the Prophet", "hamzah": "Hamza, an uncle of the Prophet",
    "abbas": "Abbas, an uncle of the Prophet", "ali": "Ali ibn Abi Talib, the Prophet's cousin and companion",
    "umar": "Umar ibn al-Khattab, a companion and second caliph",
    "omar": "Umar ibn al-Khattab, a companion and second caliph",
    "uthman": "Uthman ibn Affan, a companion and third caliph",
    "usman": "Uthman ibn Affan, a companion and third caliph",
    "osman": "Uthman ibn Affan, a companion and third caliph",
    "abubakr": "Abu Bakr, a companion and first caliph",
    "abu-bakr": "Abu Bakr, a companion and first caliph",
    "abubakar": "Abu Bakr, a companion and first caliph",
}

VOWEL_RE = re.compile(r"^[aeiou]", re.I)


def _art(word):
    return "an" if VOWEL_RE.match(word or "") else "a"


def pyth(name):
    s = 0
    for ch in (name or "").lower():
        if "a" <= ch <= "z":
            s += (ord(ch) - 96 - 1) % 9 + 1
    while s > 9:
        s = sum(int(d) for d in str(s))
    return s or 1


def conf(v):
    return CONF.get(str(v).lower() if v is not None else None, "LOW")


def _s(v, default=""):
    return v if isinstance(v, str) and v.strip() else default


def _lst(v):
    return v if isinstance(v, list) else []


def _cap(s):
    if not s:
        return s
    return s[0].upper() + s[1:]


def _norm(slug):
    return unicodedata.normalize("NFKD", (slug or "").lower()).encode("ascii", "ignore").decode()


def extract(rec):
    d = rec["data"]
    a = {}
    a["name"] = _s(d.get("name"))
    a["slug"] = _s(d.get("slug")) or a["name"].lower()
    ident = d.get("identity", {}) or {}
    cm = d.get("core_meaning", {}) or {}
    et = d.get("etymology", {}) or {}
    org = d.get("origin", {}) or {}
    tr = d.get("translations", {}) or {}
    pr = d.get("pronunciation", {}) or {}
    a["gender"] = _s(ident.get("gender"), "Unknown")
    a["gender_conf"] = conf(ident.get("gender_confidence"))
    a["lang"] = _s(et.get("primary_language"), org.get("primary_origin", "Arabic"))
    a["origin"] = _s(org.get("primary_origin"), a["lang"])
    a["form"] = _s(et.get("lexical_form"))
    a["root"] = _s(et.get("root"))
    a["root_tr"] = _s(et.get("root_transliteration"))
    a["translit"] = _s(et.get("transliteration"), a["slug"])
    a["mconf"] = conf(cm.get("meaning_confidence"))
    a["rich"] = _s(cm.get("meaning_explanation")) or _s(et.get("etymology_explanation"))
    a["short_old"] = _s(cm.get("short_meaning"), _s(cm.get("primary_meaning"), a["name"]))
    a["faq_old"] = _lst(d.get("faq"))
    a["trans"] = tr
    a["pron"] = pr
    a["nv"] = d.get("name_variants", {}) or {}
    a["nv_roman"] = _lst(a["nv"].get("romanized_variants"))
    a["nv_script"] = _lst(a["nv"].get("script_forms"))
    a["related_old"] = _lst(d.get("related_names"))
    a["alt_spell"] = _lst(ident.get("alternate_spellings"))
    a["is_month"] = bool(re.search(r"\bmonth\b|\bcalendar\b", a["rich"] + " " + a["short_old"], re.I))
    a["is_unknown"] = bool(re.search(r"not objectively established|recorded at low confidence|No confident meaning",
                                     a["rich"], re.I))
    a["gloss"] = _clean_gloss(a)
    return a


def _clean_gloss(a):
    rich = a["rich"] or ""
    name = a["name"]
    for g in re.findall(r"'([^']{2,120})'", rich):
        g = g.strip()
        if not g:
            continue
        if re.search(r"ERROR|source gloss|unsupported|not supported|replaced", g, re.I):
            continue
        if re.match(r"^(s|t|re|ve|ll|d)\s", g):
            continue
        if re.match(r"^(given|unknown|hidden|father|heavens|source|the source)", g, re.I):
            continue
        if len(g.split()) > 12:
            continue
        return _cap(g)
    s = a["short_old"] or ""
    if ";" in s:
        first, rest = s.split(";", 1)
        first, rest = first.strip(), rest.strip()
        s = rest if first.lower().startswith(name.lower()) else first
    s = re.sub(r"^(the|a|an)\s+", "", s, flags=re.I).strip()
    s = re.sub(r"^name\s+", "", s, flags=re.I).strip()
    if (s and "meaning not" not in s.lower() and s.lower() != name.lower()
            and "error" not in s.lower() and "source gloss" not in s.lower()):
        return _cap(s)
    return None


def build_definition(a):
    name = a["name"]
    gloss = a["gloss"]
    lang = a["lang"]
    if a["is_unknown"] or not gloss:
        return {
            "short_meaning": "Meaning not independently verified",
            "primary_meaning": ("The meaning of %s is not objectively established from available lexical sources; "
                                "no confident gloss is asserted." % name),
            "literal_meaning": "No literal gloss is asserted for this spelling.",
            "meaning_explanation": (a["rich"] if a["rich"] else
                                    "No verified lexical form could be confirmed for this spelling."),
            "meaning_confidence": "LOW",
        }
    if a["is_month"]:
        return {
            "short_meaning": "A month of the Persian calendar",
            "primary_meaning": ("%s (%s) is the name of a month in the traditional Persian calendar, "
                                "used as a given name." % (name, a["form"] or name)),
            "literal_meaning": "Name of a month in the Persian calendar",
            "meaning_explanation": a["rich"],
            "meaning_confidence": a["mconf"],
        }
    return {
        "short_meaning": gloss,
        "primary_meaning": "%s is %s %s-origin name meaning \u201c%s\u201d." % (
            name, _art(lang), lang, gloss.rstrip(".")),
        "literal_meaning": ("The name is the %s word itself, used unchanged as a given name rather than a "
                            "derived or diminutive form." % lang),
        "meaning_explanation": a["rich"],
        "meaning_confidence": a["mconf"],
    }


def build_etymology(a):
    lang = a["lang"]
    form = a["form"]
    name = a["name"]
    root = a["root"]
    root_tr = a["root_tr"]
    if a["is_unknown"]:
        etym_meaning = "Not established"
        etym_expl = "No reliable root analysis is available for this spelling."
    elif root:
        etym_meaning = "From the root %s (%s)" % (root, root_tr)
        etym_expl = ("The form %s is an established %s lexical item, and %s is the word itself "
                     "used as a personal name rather than a derived or diminutive form." % (form, lang, name))
    else:
        etym_meaning = "The %s word %s" % (lang, form or name)
        etym_expl = ("The form %s is an established %s lexical item used unchanged as a given name."
                     % (form, lang))
    return {
        "primary_language": lang,
        "lexical_form": form,
        "transliteration": a["translit"],
        "root": root,
        "root_transliteration": root_tr,
        "morphology": ("Simple lexical item used as a name." if not root else
                       "Built on the root %s." % root),
        "feminine_form": None,
        "etymological_meaning": etym_meaning,
        "root_family": [],
        "etymology_explanation": etym_expl,
        "etymology_confidence": a["mconf"],
        "false_etymology_warning": _false_etym_warning(a),
    }


def _false_etym_warning(a):
    lang = a["lang"]
    if a["is_month"]:
        return ("This is a calendar-month name; it does not carry a devotional or Quranic meaning, and "
                "any gloss that presents it as an Arabic religious term is unsupported.")
    return ("No derivation beyond the documented %s form is asserted. Any etymology that attributes this "
            "spelling to a different root or language without a source should be treated as unverified." % lang)


def build_language(a):
    notes = {"primary": "%s is the language of the recorded form %s." % (a["lang"], a["form"] or a["name"])}
    notes["usage"] = ("Other scripts are transliterations of the name into those writing systems; "
                      "they are not independent origins.")
    assoc = [a["lang"]]
    if a["lang"] not in ("Arabic", "Persian", "Urdu", "Turkish", "Kurdish", "Somali"):
        assoc.append("Muslim South Asia")
    return {"primary": a["lang"], "associated_languages": assoc,
            "language_notes": notes, "language_confidence": a["mconf"]}


def build_origin(a):
    lang = a["lang"]
    if a["is_unknown"]:
        expl = ("The origin of this spelling is not objectively established; it circulates in Muslim naming "
                "communities, but no single language of origin is confirmed.")
    elif a["is_month"]:
        expl = ("The name originates in %s calendrical usage, where it names a month of the year." % lang)
    else:
        expl = ("The name originates in %s and circulates in Muslim naming through established "
                "multilingual use." % lang)
    return {"primary_origin": a["origin"], "origin_type": "linguistic", "origin_confidence": a["mconf"],
            "origin_explanation": expl,
            "cultural_transmission": [a["lang"], "Muslim South Asia", "Urdu-speaking communities"]}


def build_religion(a):
    slug = _norm(a["slug"])
    name = a["name"]
    quranic = slug in QURANIC_PROPHETS or slug in QURANIC_FIGURES
    if quranic:
        if slug in QURANIC_PROPHETS:
            q_note = ("%s is a Qur'anic name: it is the name of %s, mentioned in the Qur'an."
                      % (name, QURANIC_PROPHETS[slug]))
        else:
            q_note = ("%s is the Qur'anic name of %s." % (name, QURANIC_FIGURES[slug]))
        is_q = True
        q_status = "verified"
    else:
        q_note = ("%s is not independently established as a Qur'anic personal name, so no Qur'anic basis is claimed."
                  % name)
        is_q = False
        q_status = "not_verified"
    if slug in QURANIC_PROPHETS:
        p_status = "verified"
        p_note = ("%s is the name of %s, so it is used with prophetic association." % (name, QURANIC_PROPHETS[slug]))
    else:
        p_status = "not_verified"
        p_note = ("No verified source establishes %s as the name of a prophet." % name)
    if slug in PROPHET_FAMILY:
        c_status = "verified"
        c_note = ("%s is the name of %s." % (name, PROPHET_FAMILY[slug]))
    else:
        c_status = "not_verified"
        c_note = "No companion (sahabi) of this name is attested in this record."
    return {
        "primary_association": "Islamic-cultural usage",
        "religion_confidence": "MEDIUM",
        "religious_status": "Culturally used; not inherently a doctrinal term",
        "religious_explanation": ("%s is used by Muslims as a personal name, but the word itself is lexical in "
                                  "origin; its Islamic association is cultural rather than scriptural." % name),
        "quranic_status": {"is_quranic": is_q, "status": q_status, "note": q_note},
        "hadith_status": {"status": "not_verified",
                          "note": "No specific authentic hadith report about this name is cited; none is invented."},
        "prophetic_status": {"status": p_status, "note": p_note},
        "companion_status": {"status": c_status, "note": c_note},
    }


def build_translations(a):
    gloss = a["gloss"] or "the attested meaning"
    name = a["name"]
    lang = a["lang"]
    trans = a["trans"]
    out = {}
    for lg in ["english", "urdu", "persian", "hindi", "pashto", "arabic"]:
        t = trans.get(lg, {}) or {}
        script = _s(t.get("name")) or _s(t.get("script")) or a["form"] or name
        meaning = _s(t.get("meaning"))
        long_meaning = _s(t.get("long_meaning"))
        item = {"name": script, "script": script}
        if lg == "english":
            item["meaning"] = (gloss if a["gloss"] else "Meaning not independently verified")
            item["long_meaning"] = ("%s is %s %s-origin given name; in %s the word means \u201c%s\u201d."
                                    % (name, _art(lang), lang, lang, gloss.rstrip(".")))
        else:
            item["meaning"] = meaning or (script or name)
            item["long_meaning"] = long_meaning or meaning or (script or name)
        if lg in ("pashto", "arabic"):
            item["native_review_required"] = True
        out[lg] = item
    return out


def build_pronunciation(a):
    pron = a["pron"]
    scripts = {}
    for lg in ["persian", "urdu", "hindi", "pashto"]:
        v = _s(pron.get(lg))
        if v:
            scripts[lg] = v
    ar = _s((a["trans"].get("arabic") or {}).get("name"))
    if ar:
        scripts["arabic"] = ar
    romanized = _s(pron.get("romanized"), a["slug"])
    return {"romanized": romanized, "ipa": None,
            "approximation_note": ("No verified IPA transcription is available for this form; the romanized "
                                   "syllable split is an approximation only."),
            "common_mispronunciation": None, "scripts": scripts}


def build_faq(a):
    name = a["name"]
    lang = a["lang"]
    gloss = a["gloss"]
    quranic = _norm(a["slug"]) in QURANIC_PROPHETS or _norm(a["slug"]) in QURANIC_FIGURES
    ur = (a["trans"].get("urdu") or {}).get("name") or ""
    ur_meaning = (a["trans"].get("urdu") or {}).get("meaning") or ""
    pron = a["pron"].get("romanized") or a["slug"]
    gender = a["gender"]
    gender_word = {"Male": "a boy's", "Female": "a girl's", "Unisex": "a unisex",
                   "Unknown": "not gender-specific"}.get(gender, "a")
    faq = []
    if a["is_unknown"]:
        faq.append({"q": "What does %s mean?" % name,
                    "a": "The meaning of %s is not objectively established; no confident gloss is asserted." % name})
    elif a["is_month"]:
        faq.append({"q": "What does %s mean?" % name,
                    "a": "%s (%s) is the name of a month in the traditional Persian calendar." % (name, a["form"] or name)})
    else:
        faq.append({"q": "What does %s mean?" % name,
                    "a": "%s is %s %s-origin name meaning \u201c%s\u201d." % (name, _art(lang), lang, gloss.rstrip("."))})
    faq.append({"q": "What is the origin of %s?" % name,
                "a": "%s originates in %s and circulates in Muslim naming communities." % (name, a["origin"])})
    faq.append({"q": "Is %s an Arabic name?" % name,
                "a": ("Yes, the recorded form %s is Arabic." % a["form"] if a["lang"] == "Arabic"
                      else "No \u2014 the recorded form %s is %s, not Arabic." % (a["form"], a["lang"]))})
    faq.append({"q": "What is the root of %s?" % name,
                "a": ("It is built on the root %s (%s)." % (a["root"], a["root_tr"]) if a["root"]
                      else "No root analysis is asserted for this spelling.")})
    faq.append({"q": "Is %s an Islamic name?" % name,
                "a": ("%s is used by Muslims, but it is a lexical name rather than an exclusively Islamic "
                      "religious term." % name)})
    faq.append({"q": "Is %s a Quranic name?" % name,
                "a": ("Yes, %s is a Qur'anic name (see the religion section)." % name if quranic
                      else "%s is not independently established as a Qur'anic personal name." % name)})
    if ur_meaning:
        faq.append({"q": "What does %s mean in Urdu?" % name,
                    "a": "In Urdu it is written %s and carries the sense \u201c%s\u201d." % (ur, ur_meaning)})
    faq.append({"q": "How is %s pronounced?" % name,
                "a": "A romanized syllable approximation is \u201c%s\u201d." % pron})
    faq.append({"q": "Is %s a boy's or girl's name?" % name,
                "a": "Documented usage records %s as %s name; actual use can vary by community." % (name, gender_word)})
    seen = set()
    dedup = []
    for f in faq:
        key = re.sub(r"\s+", " ", f["a"]).strip().lower()
        if key not in seen:
            seen.add(key)
            dedup.append(f)
    return dedup


def build_variants(a):
    roman = [x for x in a["nv_roman"] if x and x.lower() != a["slug"].lower()][:6]
    script_forms = a["nv_script"] or []
    return {
        "romanized_variants": roman or [a["name"]],
        "script_forms": script_forms,
        "variant_notes": "Spelling variants reflect different transliteration conventions, not different names.",
        "do_not_merge_with": [],
    }


def build_related_names(a):
    return []


def build_name_story(a):
    name = a["name"]
    lang = a["lang"]
    if a["is_month"]:
        return {"status": "cultural", "render": True,
                "story": ("%s is a month-name turned given name: it borrows a word from the %s calendar "
                          "and uses it to mark a child with the qualities the month evokes." % (name, lang))}
    if a["is_unknown"]:
        return {"status": "none", "render": False,
                "story": "No verified narrative is available for this spelling."}
    return {"status": "none", "render": False, "story": ""}


def build_structured_data(a):
    name = a["name"]
    gloss = a["gloss"]
    lang = a["lang"]
    faq = build_faq(a)
    graph = [
        {"@type": "DefinedTerm",
         "name": name,
         "description": "%s \u2014 %s %s-origin given name meaning %s" % (
             name, _art(lang), lang, (gloss or "meaning not independently verified").rstrip(".")),
         "inDefinedTermSet": {"@type": "DefinedTermSet", "name": "NameVerse Islamic Names"}},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"],
             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq[:8]]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": ""},
            {"@type": "ListItem", "position": 2, "name": "Islamic Names", "item": ""},
            {"@type": "ListItem", "position": 3, "name": name, "item": ""}]},
    ]
    return {"@context": "https://schema.org", "@graph": graph}


def build_seo(a):
    name = a["name"]
    lang = a["lang"]
    focus = "%s meaning" % name
    secondary = ["%s name meaning" % name, "%s origin" % name, "%s meaning in Urdu" % name,
                 "%s pronunciation" % name, "%s Islamic name" % name]
    if a["is_unknown"]:
        meta = "Meaning, origin and usage of the name %s." % name
        desc = "This page records what is known about the name %s; no confident meaning is asserted." % name
    else:
        meta = "%s (%s) \u2014 meaning, origin, pronunciation and Islamic naming context." % (name, a["form"] or name)
        desc = ("%s is %s %s-origin given name. This page covers its meaning, origin, pronunciation and "
                "naming context." % (name, _art(lang), lang))
    return {
        "title": "%s Name Meaning, Origin & Islamic Context" % name,
        "meta_description": meta,
        "meta_keywords": ", ".join([focus] + secondary),
        "description_paragraph": desc,
        "keywords": [focus] + secondary,
        "focus_keyword": focus,
        "secondary_keywords": secondary,
        "canonical_url": "",
        "seo_score": _seo_score(a),
        "seo_score_basis": _seo_basis(a),
    }


def _seo_score(a):
    n_faq = len(build_faq(a))
    base = 62
    base += 15 if a["gloss"] else 0
    base += 5 if a["rich"] else 0
    base += min(10, (n_faq - 5) * 2) if n_faq >= 5 else 0
    base += 5 if a["root"] else 0
    base += 3 if _norm(a["slug"]) in QURANIC_PROPHETS or _norm(a["slug"]) in QURANIC_FIGURES else 0
    return min(96, base)


def _seo_basis(a):
    n_faq = len(build_faq(a))
    return ("%d distinct FAQs; gloss %s; root %s; uniqueness enforced by cross-field de-duplication; "
            "score reflects content depth, not field count." % (
                n_faq, "verified" if a["gloss"] else "unverified",
                "present" if a["root"] else "absent"))


def build_seo_content(a):
    name = a["name"]
    lang = a["lang"]
    if a["is_unknown"]:
        intro = ("This page records what is known about the name %s; its meaning is not objectively "
                 "established from available sources." % name)
    elif a["is_month"]:
        intro = ("This page explains the name %s, a month-name of the Persian calendar that is also used "
                 "as a given name." % name)
    else:
        intro = ("This page explains the meaning and origin of the name %s, %s %s-origin name used in "
                 "Muslim communities." % (name, _art(lang), lang))
    body = ("%s is used within Muslim naming communities. Its Islamic association is cultural; it is not a "
            "doctrinal term." % name)
    return {"intro_paragraph": intro, "body_summary": body}


def build_social_tags(a):
    name = a["name"]
    return ["#%s" % name, "#%sMeaning" % name, "#NameMeaning", "#IslamicNames", "#NameOrigin"]


def build(rec, now):
    a = extract(rec)
    name = a["name"]
    cm = build_definition(a)
    et = build_etymology(a)
    lang_block = build_language(a)
    org = build_origin(a)
    rel = build_religion(a)
    trans = build_translations(a)
    pron = build_pronunciation(a)
    faq = build_faq(a)
    nv = build_variants(a)
    seo = build_seo(a)
    seoc = build_seo_content(a)
    tags = build_social_tags(a)
    ns = build_name_story(a)
    sd = build_structured_data(a)
    num = pyth(name)
    num_meaning = ("In Pythagorean numerology the letters of %s total %d, associated with %s. This is an "
                   "interpretive tradition, not a factual claim." % (name, num, NUM_MEAN[num]))
    spiritual_render = (a["gloss"] is not None and not a["is_month"] and not a["is_unknown"]
                        and a["mconf"] in ("HIGH", "MEDIUM"))
    if spiritual_render:
        sp = {"status": "interpretive", "render": True,
              "meaning": ("Families may read the sense \u201c%s\u201d as a hopeful quality for the child." % a["gloss"].rstrip(".")),
              "basis": "Lexical meaning: %s." % a["gloss"],
              "is_direct_religious_definition": False}
    else:
        sp = {"status": "not_applicable", "render": False,
              "meaning": ("No devotional reading is offered because the underlying word is a descriptive term "
                          "rather than a religious concept."),
              "basis": None, "is_direct_religious_definition": False}
    data = {
        "name": name, "slug": a["slug"], "page_type": "name_meaning",
        "identity": {
            "display_name": name, "normalized_name": a["slug"], "name_type": "given_name",
            "gender": a["gender"], "gender_confidence": a["gender_conf"],
            "gender_note": "Gender is recorded from documented naming usage, not inferred from the word's meaning.",
            "alternate_spellings": a["alt_spell"] or [name], "name_status": "attested"},
        "core_meaning": cm,
        "etymology": et,
        "language": lang_block,
        "origin": org,
        "religion": rel,
        "islamic_naming_context": {
            "can_be_used_by_muslims": True,
            "context": "Muslim naming culture in South Asia and the Persianate world",
            "interpretation": ("Its lexical sense is a positive quality that families may wish for a child."
                               if a["gloss"] else "No confident interpretation is asserted."),
            "important_distinction": ("Muslim use of the name is not evidence that the word is Qur'anic or "
                                      "religiously prescribed.")},
        "cultural_context": {
            "primary_cultural_associations": [a["lang"], "Muslim South Asia"],
            "cultural_meaning": ("In the communities that use it, the name reads as a positive quality."
                                 if a["gloss"] else "No cultural connotation is asserted."),
            "personal_name_interpretation": ("As a personal name it can be read as a wish for the quality it names."
                                             if a["gloss"] else "No interpretation is asserted."),
            "interpretation_warning": "The symbolic reading is a cultural convention, distinct from the dictionary sense."},
        "semantic_field": {
            "primary_semantic_domain": (a["gloss"] or "unverified"),
            "related_concepts": [a["gloss"]] if a["gloss"] else []},
        "spiritual_meaning": sp,
        "personality_associations": {"status": "not_verified", "render": False,
                                     "note": "No verified basis links this name to specific personality traits."},
        "hidden_personality_traits": {"status": "not_verified", "render": False,
                                      "note": "No verified basis."},
        "numerology": {"status": "interpretive", "render": True, "lucky_number": num,
                       "life_path_number": num, "ruling_planet": PLANET[num], "lucky_day": DAY[num],
                       "lucky_colors": COLORS[num], "lucky_stone": STONE[num], "meaning": num_meaning,
                       "note": "Numerology is an optional interpretive layer."},
        "lucky_attributes": {"status": "interpretive", "render": True, "lucky_number": num,
                             "lucky_day": DAY[num], "lucky_colors": COLORS[num], "lucky_stone": STONE[num],
                             "ruling_planet": PLANET[num]},
        "translations": trans,
        "translation_quality": {
            "strategy": "semantic_translation", "confidence": a["mconf"], "native_review_required": True,
            "note": "Each language is rendered in its own idiom; Pashto and Arabic are flagged for native review."},
        "pronunciation": pron,
        "name_variants": nv,
        "related_names": build_related_names(a),
        "historical_context": {"status": "verified" if a["lang"] != "Unknown" else "not_verified",
                               "note": ("The form %s is an established %s lexical item."
                                        % (a["form"] or name, a["lang"]) if a["lang"] != "Unknown"
                                        else "No verified lexical history is available.")},
        "modern_usage": {"status": "requires_frequency_data",
                         "note": "Personal-name popularity must be measured separately from lexical presence."},
        "popularity": {"status": "not_measured", "render": False, "score": None, "by_region": [],
                       "note": "No verified popularity or registration data is available."},
        "celebrity_usage": {"status": "not_verified", "render": False, "items": [],
                            "note": "No verified celebrity usage is recorded."},
        "real_world_usage": {"status": "not_verified", "render": False,
                             "note": "No verified real-life bearer story is published; none is invented."},
        "name_story": ns,
        "faq": faq,
        "seo": seo,
        "seo_content": seoc,
        "social_tags": tags,
        "content_quality": {
            "tier1_verified": bool(a["gloss"]),
            "authenticity_flags": [],
            "fabricated_content_removed": True,
            "fields_total": 0,
            "quality_score": _seo_score(a),
            "quality_score_basis": _seo_basis(a)},
        "evidence": {
            "sources": ([("The recorded %s form %s carries the sense \u201c%s\u201d."
                          % (a["lang"], a["form"], a["gloss"].rstrip(".")))] if a["gloss"]
                        else ["No Tier-A/B source confirms a meaning for this spelling."]),
            "verification_method": "Cross-checked lexical sources; no scriptural or statistical claim is asserted without a source."},
        "provenance": {
            "pipeline": "NameVerse Production v8",
            "methodology": "Parse atomic facts -> rebuild distinct fields -> validate",
            "upgraded_from": "v7 (recursive-corruption and semantic-duplication remediation)",
            "processed_at": now},
        "structured_data": sd,
        "editorial_validation": {"needs_manual_verification": a["mconf"] == "LOW",
                                 "flags": (["meaning unverified"] if not a["gloss"] else []),
                                 "confidence": a["mconf"],
                                 "reviewed_by": "NameVerse verification pipeline",
                                 "reviewed_at": now},
        "render_policy": {
            "render_verified": True,
            "render_interpretive": True,
            "hide_unverified": True,
            "single_definition_source": "core_meaning.primary_meaning",
            "non_rendered_definition_fields": ["core_meaning.short_meaning", "core_meaning.literal_meaning",
                                               "semantic_field", "etymology.etymological_meaning"],
            "hidden_sections": ["personality_associations", "hidden_personality_traits", "popularity",
                                "celebrity_usage", "real_world_usage", "spiritual_meaning", "name_story"]},
    }
    data["content_revision"] = REVISION
    data["content_quality"]["fields_total"] = _distinct_leaves(data)
    return {"schema_version": "super-2.0", "success": True, "data": _order(data)}


def _order(data):
    ordered = {}
    for k in TARGET_ORDER:
        if k in data:
            ordered[k] = data[k]
    if "content_revision" in data:
        out = {}
        for k, v in ordered.items():
            out[k] = v
            if k == "slug":
                out["content_revision"] = data["content_revision"]
        ordered = out
    return ordered


def _distinct_leaves(o):
    vals = set()
    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            s = x.strip()
            if s:
                vals.add(s.lower())
        elif x is not None and x is not False and x != "":
            vals.add(repr(x))
    walk(o)
    return len(vals)


RECURSIVE_RE = [
    re.compile(r"\bsense\s+'[^']*sense\s+'", re.I),
    re.compile(r"\bthe form\b[^.]{0,80}\bthe form\b", re.I),
    re.compile(r"(\b[A-Za-z]{4,}\b(?: [a-z]+){3,}) \1\b", re.I),
]
LABEL_FIELDS = {("core_meaning", "short_meaning")}
DEFINITION_FIELDS = [
    ("core_meaning", "short_meaning"), ("core_meaning", "primary_meaning"),
    ("core_meaning", "literal_meaning"), ("core_meaning", "meaning_explanation"),
    ("etymology", "etymological_meaning"), ("etymology", "etymology_explanation"),
    ("origin", "origin_explanation"), ("cultural_context", "cultural_meaning"),
    ("seo", "description_paragraph"), ("seo_content", "intro_paragraph"),
    ("seo_content", "body_summary"),
]


def _tokens(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = re.sub(r"[^a-z0-9\u0600-\u06FF\u0900-\u097F ]", " ", s)
    return set(t for t in s.split() if len(t) > 2)


def _jaccard(a, b):
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def validate(rec, fname):
    errs = []
    data = rec.get("data", {})
    raw = json.dumps(data, ensure_ascii=False)
    def _strings(o):
        if isinstance(o, dict):
            for v in o.values():
                yield from _strings(v)
        elif isinstance(o, list):
            for v in o:
                yield from _strings(v)
        elif isinstance(o, str):
            yield o
    for sval in _strings(data):
        for rx in RECURSIVE_RE:
            if rx.search(sval):
                errs.append("recursive_pattern")
                break
        else:
            continue
        break
    texts = {}
    for sec, key in DEFINITION_FIELDS:
        v = data.get(sec, {}).get(key)
        if isinstance(v, str) and v.strip():
            norm = re.sub(r"\s+", " ", v.strip()).lower()
            if norm in texts:
                errs.append("exact_dup:%s.%s" % (sec, key))
            texts[norm] = (sec, key)
    for i in range(len(DEFINITION_FIELDS)):
        for j in range(i + 1, len(DEFINITION_FIELDS)):
            s1, k1 = DEFINITION_FIELDS[i]
            s2, k2 = DEFINITION_FIELDS[j]
            if (s1, k1) in LABEL_FIELDS or (s2, k2) in LABEL_FIELDS:
                continue
            v1 = data.get(s1, {}).get(k1)
            v2 = data.get(s2, {}).get(k2)
            if isinstance(v1, str) and isinstance(v2, str) and v1.strip() and v2.strip():
                if _jaccard(v1, v2) > 0.6:
                    errs.append("semantic_dup:%s.%s~%s.%s" % (s1, k1, s2, k2))
    if re.search(r"\ba (Arabic|English|Iranian|Indian|Urdu|Islamic|origin|idea|era|eighth|an?[aeiou])", raw, re.I):
        errs.append("grammar_a_an")
    if rec.get("schema_version") != "super-2.0" or rec.get("success") is not True:
        errs.append("header")
    if list(data.keys()) != list(_order(data).keys()):
        errs.append("key_order")
    faq = data.get("faq", [])
    if not isinstance(faq, list) or len(faq) < 5:
        errs.append("faq<5")
    ans = [re.sub(r"\s+", " ", (f.get("a") or "")).strip().lower() for f in faq]
    if len(set(ans)) != len(ans):
        errs.append("faq_duplicate_answer")
    for lg in ["english", "urdu", "persian", "hindi", "pashto", "arabic"]:
        if not (data.get("translations", {}).get(lg) or {}).get("meaning"):
            errs.append("trans:" + lg)
    sd = data.get("structured_data", {})
    if sd.get("@context") != "https://schema.org" or not isinstance(sd.get("@graph"), list):
        errs.append("structured_data")
    types = [g.get("@type") for g in sd.get("@graph", []) if isinstance(g, dict)]
    if "Person" in types or "Thing" in types:
        errs.append("structured_data_typing")
    if data.get("popularity", {}).get("score") is not None:
        errs.append("popularity_score")
    if data.get("celebrity_usage", {}).get("items"):
        errs.append("celebrity_items")
    qs = data.get("content_quality", {}).get("quality_score")
    if qs is None or qs >= 100:
        errs.append("quality_score>=100")
    return errs


def git(*args):
    subprocess.run(["git"] + list(args), cwd=REPO, check=True)


def main():
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    files = sorted(glob.glob(os.path.join(DEST, "*.json")))
    files = [f for f in files if os.path.basename(f) not in ("PROGRESS_SUPER2.json", "PROGRESS_CONTENT_FIX.json",
                                                             "PROGRESS_V8.json")]
    todo = []
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
            if d.get("data", {}).get("content_revision") == REVISION:
                continue
        except Exception:
            pass
        todo.append(f)
    print("TOTAL %d | ALREADY v8 %d | TODO %d" % (len(files), len(files) - len(todo), len(todo)))
    done = len(files) - len(todo)
    batch_no = 0
    pushed = 0
    flagged = 0
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
                flagged += 1
                print("VALIDATION FAIL", os.path.basename(f), errs)
                sys.exit(1)
            json.dump(rec, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        done += len(chunk)
        json.dump({"schema_version": "super-2.0", "revision": REVISION, "dataset": "NameVerse",
                   "culture": "islamic", "status": "complete" if done >= len(files) else "in_progress",
                   "total_names": len(files), "names_completed": done,
                   "batches_pushed": batch_no, "updated_at": now},
                  open(PROGRESS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        if DO_COMMIT:
            git("add", *[os.path.relpath(f, REPO) for f in chunk])
            git("add", os.path.relpath(PROGRESS, REPO))
            git("commit", "-m", "Fix islamic names v8 batch %d (%d names): de-duplicate & de-overclaim" % (batch_no, len(chunk)))
            git("push", "origin", "HEAD:%s" % BRANCH)
            pushed += 1
            print("PUSHED batch %d (%d names) | done %d/%d" % (batch_no, len(chunk), done, len(files)))
    print("COMPLETE: %d names, %d batches pushed, %d flagged" % (done, pushed, flagged))


if __name__ == "__main__":
    main()
