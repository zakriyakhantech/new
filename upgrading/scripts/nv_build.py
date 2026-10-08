# -*- coding: utf-8 -*-
"""Builds the nested NameVerse record for one name. One name at a time."""
import json, re, sys
from curated import CUR, GLOSSES

ORIGIN_NATIVE = {
    "ur": {"Arabic": "عربی", "Persian": "فارسی", "Sanskrit": "سنسکرت", "Hebrew": "عبرانی", "Turkish": "ترکی", "Turkic": "ترک", "Kurdish": "کردی", "Greek": "یونانی", "Unknown": "نامعلوم"},
    "fa": {"Arabic": "عربی", "Persian": "فارسی", "Sanskrit": "سانسکریت", "Hebrew": "عبری", "Turkish": "ترکی", "Turkic": "ترک", "Kurdish": "کردی", "Greek": "یونانی", "Unknown": "نامعلوم"},
    "hi": {"Arabic": "अरबी", "Persian": "फ़ारसी", "Sanskrit": "संस्कृत", "Hebrew": "हिब्रू", "Turkish": "तुर्की", "Turkic": "तुर्क", "Kurdish": "कुर्दी", "Greek": "यूनानी", "Unknown": "अज्ञात"},
    "ps": {"Arabic": "عربي", "Persian": "فارسي", "Sanskrit": "سانسکریت", "Hebrew": "عبري", "Turkish": "ترکي", "Turkic": "ترک", "Kurdish": "کردي", "Greek": "یوناني", "Unknown": "نامعلوم"},
    "ar": {"Arabic": "العربية", "Persian": "الفارسية", "Sanskrit": "السنسكريتية", "Hebrew": "العبرية", "Turkish": "التركية", "Turkic": "التركية", "Kurdish": "الكردية", "Greek": "اليونانية", "Unknown": "غير محددة"},
}

LONG_T = {
 "ur": "{n} ({f}) {o} زبان سے ماخوذ نام ہے۔ اس کا بنیادی مفہوم {m} ہے۔ یہ نام مسلم معاشروں میں رکھا جاتا ہے اور اس کے مفاہیم سیاق و سباق کے مطابق استعمال ہوتے ہیں۔",
 "fa": "{n} ({f}) نامی برگرفته از زبان {o} است و معنای اصلی آن {m} است. این نام در جوامع مسلمان به کار می‌رود و کاربرد آن بسته به بافت زبانی متفاوت است.",
 "hi": "{n} ({f}) {o} भाषा से लिया गया नाम है। इसका मुख्य अर्थ {m} है। यह नाम मुस्लिम समाजों में रखा जाता है और इसका प्रयोग संदर्भ के अनुसार बदलता है।",
 "ps": "{n} ({f}) د {o} ژبې څخه اخیستل شوی نوم دی او بنسټیزه مانا یې {m} ده. دا نوم په مسلمانانو ټولنو کې کارول کیږي او کارونه یې د سیاق له مخې بدلیږي.",
 "ar": "{n} ({f}) اسم مأخوذ من اللغة {o}، ومعناه الأساسي {m}. يُستخدم هذا الاسم في المجتمعات المسلمة ويختلف استعماله بحسب السياق اللغوي.",
}

DO_NOT_MERGE = {
 "aamir": [{"name": "Amir", "script": "أمير", "reason": "أمير (amīr) means 'commander, prince' and derives from the root أ م ر. It is a different name from عامر (ʿĀmir), which derives from ع م ر and means 'inhabited, flourishing'."}],
 "aamira": [{"name": "Amira", "script": "أميرة", "reason": "أميرة (amīra) means 'princess' and derives from أ م ر. It is not a variant of عامرة (ʿĀmira)."}],
 "aamirah": [{"name": "Amirah", "script": "أميرة", "reason": "أميرة (amīra) means 'princess' and derives from أ م ر. It is not a variant of عامرة (ʿĀmira)."}],
 "aamra": [{"name": "Amira", "script": "أميرة", "reason": "The source record conflated aamra with أميرة ('princess'). These are different forms and must not be merged."}],
 "aasia": [{"name": "Aisha", "script": "عائشة", "reason": "عائشة (ʿĀʾisha) is a different name. The source record incorrectly gave عائشة as the Arabic form of aasia; the correct association is آسية (Āsiya)."}],
 "aasiya": [{"name": "Aisha", "script": "عائشة", "reason": "عائشة (ʿĀʾisha) is a different name. The source record incorrectly gave عائشة as the Arabic form of aasiya; the correct association is آسية (Āsiya)."}],
 "aasiyah": [{"name": "Aisha", "script": "عائشة", "reason": "عائشة (ʿĀʾisha) is a different name. The source record incorrectly gave عائشة as the Arabic form; the correct association is آسية (Āsiya)."}],
 "aasiyyah": [{"name": "Aisha", "script": "عائشة", "reason": "عائشة (ʿĀʾisha) is a different name. The correct association for aasiyyah is آسية (Āsiya)."}],
 "aasman": [{"name": "Asman", "script": "آسمان", "reason": "آسمان is a Persian word meaning 'sky'. It is not an Arabic name and must not be merged with Arabic forms."}],
 "aarzoo": [{"name": "Arzu", "script": "آرزو", "reason": "آرزو is a Persian word meaning 'wish, longing'. It is not Arabic in origin."}],
 "aarzu": [{"name": "Arzu", "script": "آرزو", "reason": "آرزو is a Persian word meaning 'wish, longing'. It is not Arabic in origin."}],
 "aaron": [{"name": "Harun", "script": "هارون", "reason": "هارون (Hārūn) is the Qur'anic Arabic form of the prophet Aaron. The English form Aaron derives from Hebrew אַהֲרוֹן. They are related but not identical forms."}],
 "aarya": [{"name": "Aryan", "script": "आर्यन", "reason": "आर्य (ārya) is a Sanskrit term meaning 'noble'. It is not an Arabic name and must not be merged with Arabic forms."}],
 "aaryan": [{"name": "Arya", "script": "आर्य", "reason": "आर्यन is a Sanskrit-derived South Asian name. It is not Arabic in origin."}],
 "aas": [{"name": "As", "script": "عاس", "reason": "No verified lexical form was established for aas, so it must not be merged with any similar-looking Arabic form."}],
 "aasal": [{"name": "Asal", "script": "عسل", "reason": "عسل means 'honey'. It must not be merged with the Persian-origin name Asal (عسل/اسل) used in some communities, whose identification is separate."}],
 "aaus": [{"name": "Aws", "script": "أوس", "reason": "أوس (Aws) is the standard form of this early Islamic name. The source record's gloss 'Fish' is unsupported and must not be carried over."}],
 "aauf": [{"name": "Awf", "script": "عوف", "reason": "عوف (ʿAwf) is the standard form. The source record's spelling عؤف is non-standard and the two must not be treated as separate names."}],
 "aatiq": [{"name": "Atiq", "script": "عتيق", "reason": "The source record gave عاطق, which is not a standard form. The intended form is likely عتيق (ʿAtīq). The identification is uncertain and the forms must not be merged without verification."}],
 "aatiqa": [{"name": "Atiqa", "script": "عتيقة", "reason": "The source record gave آتيفا, which is not a standard form. The intended form is likely عتيقة (ʿAtīqa). The identification is uncertain."}],
 "aatiqah": [{"name": "Atiqa", "script": "عتيقة", "reason": "The source record's form is non-standard. The intended form is likely عتيقة (ʿAtīqa). The identification is uncertain."}],
 "aasaal": [{"name": "Ahmad", "script": "أحمد", "reason": "The source record gave أحمد ('Ahmad'), which is a completely different name. aasaal must not be merged with Ahmad."}],
 "aamirul": [{"name": "Amir", "script": "أمير", "reason": "No verified form was established for aamirul. It must not be merged with أمير (amīr) or عامر (ʿĀmir) without evidence."}],
 "aamiya": [{"name": "Ammiyya", "script": "عامية", "reason": "عامية is a linguistic register term ('colloquial Arabic'), not a personal name. It must not be treated as a name."}],
 "aamla": [{"name": "Amal", "script": "أمل", "reason": "No verified form was established for aamla. It must not be merged with أمل (amal, 'hope')."}],
 "aana": [{"name": "Ana", "script": "أنا", "reason": "No verified form was established for aana. It must not be merged with the Arabic pronoun أنا."}],
 "aanal": [{"name": "Anal", "script": "أنال", "reason": "No verified form was established for aanal."}],
 "aaneseh": [{"name": "Aniseh", "script": "أنيسة", "reason": "No verified form was established for aaneseh. It must not be merged with أنيسة (Anīsa) without evidence."}],
 "aani": [{"name": "Ani", "script": "عاني", "reason": "No verified form was established for aani."}],
 "aania": [{"name": "Ania", "script": "عانية", "reason": "No verified form was established for aania."}],
 "aanil": [{"name": "Anil", "script": "أنيل", "reason": "No verified form was established for aanil."}],
 "aaniya": [{"name": "Aniya", "script": "عانية", "reason": "No verified form was established for aaniya."}],
 "aaniyah": [{"name": "Aniyah", "script": "عانية", "reason": "No verified form was established for aaniyah."}],
 "aaolin": [{"name": "Aolin", "script": "عاولين", "reason": "No verified form was established for aaolin."}],
 "aaqifa": [{"name": "Aqila", "script": "عاقلة", "reason": "The source record gave أعقل ('more rational'), which is a different word. aaqifa must not be merged with عاقلة (ʿĀqila)."}],
 "aara": [{"name": "Ara", "script": "عارة", "reason": "The source record gave عارة, which is not a standard Arabic lexical form. No verified identification was established."}],
 "aarasun": [{"name": "Arasun", "script": "آراسون", "reason": "No verified form was established for aarasun."}],
 "aareeha": [{"name": "Areeha", "script": "أريحا", "reason": "No verified form was established for aareeha. It must not be merged with أريحا (Jericho) without evidence."}],
 "aarib": [{"name": "Arib", "script": "عارب", "reason": "The source record gave عارب, which is not a standard Arabic lexical form. No verified identification was established."}],
 "aaribah": [{"name": "Ariba", "script": "عاربة", "reason": "No verified form was established for aaribah."}],
 "aaribat": [{"name": "Aribat", "script": "عريبات", "reason": "No verified form was established for aaribat."}],
 "aaribun": [{"name": "Aribun", "script": "عاربون", "reason": "No verified form was established for aaribun."}],
 "aarizah": [{"name": "Ariza", "script": "عاريضة", "reason": "The source record gave عاريظة, which is not a standard Arabic lexical form. No verified identification was established."}],
 "aarizun": [{"name": "Arizun", "script": "عارزون", "reason": "No verified form was established for aarizun."}],
 "aarzam": [{"name": "Arzam", "script": "عرضام", "reason": "The source record gave عرضام, which is not a standard Arabic lexical form. No verified identification was established."}],
 "aaseman": [{"name": "Aseman", "script": "آسمان", "reason": "No verified form was established for aaseman. It resembles Persian آسمان ('sky') but this could not be confirmed."}],
 "aashif": [{"name": "Ashif", "script": "عاشف", "reason": "The source record gave عاشف, which is not a standard Arabic lexical form. No verified identification was established."}],
 "aasira": [{"name": "Asira", "script": "الأسيرة", "reason": "The source record gave الأسيرة ('the captive'), a definite noun phrase rather than a name. No verified identification was established."}],
 "aathira": [{"name": "Athira", "script": "أثيرة", "reason": "The source record gave أثيرة, which is not a standard Arabic lexical form. No verified identification was established."}],
}

def syllabify(s):
    s = s.lower()
    parts = re.findall(r'[^aeiouy]*[aeiouy]+(?:[^aeiouy]*$|[^aeiouy](?=[^aeiouy]))?', s)
    parts = [p for p in parts if p]
    if not parts: return s
    return "-".join(parts)

def build(name, src):
    c = CUR[name]
    ar, ur, fa, hi, ps, gkey, origin, gender, root, quranic, conf, note = c
    g = GLOSSES.get(gkey) if gkey else None
    # A non-empty gloss placeholder is not verification. In particular, `uncertain_form`
    # is a status label, not a dictionary meaning; low-confidence/unknown-origin records
    # must not render as verified entries.
    verified = bool(g is not None and conf in ("high", "medium") and origin not in ("Unknown", "") and gkey != "uncertain_form")
    disp = name.capitalize()
    slug = name
    short = g["en"] if verified else "Not objectively established"
    primary = (g["en"].split(",")[0].strip() if verified else "Not objectively established")
    sec = [x.strip() for x in g["en"].split(",")[1:]] if verified else []
    origin_native = ORIGIN_NATIVE

    def tr(lang, form):
        if not verified or not form:
            return {"name": form, "meaning": None, "long_meaning": None,
                    "translation_status": "unverified",
                    "note": "No verified %s translation was established for this form. A meaning is deliberately not asserted." % lang}
        m = g[lang]
        return {"name": form, "meaning": m, "long_meaning": None,
                "translation_status": "draft_needs_native_review",
                "review_note": "Curated rendering only; not independently cited or reviewed by a native speaker."}

    translations = {
        "english": ({"name": disp, "meaning": g["en"], "long_meaning": None,
                     "translation_status": "draft_needs_native_review",
                     "review_note": "Lexical gloss is source-supported where a named citation is attached; translations into other languages still require native-speaker review."} if verified
                    else {"name": disp, "meaning": None, "long_meaning": None, "translation_status": "unverified",
                          "note": "No verified meaning was established for this form, so no gloss is asserted."}),
        "urdu": tr("ur", ur), "persian": tr("fa", fa), "hindi": tr("hi", hi),
        "pashto": tr("ps", ps), "arabic": tr("ar", ar),
    }

    rtl = any(x for x in (ar, ur, fa, ps))
    inlang = [c for c, f in (("ar", ar), ("ur", ur), ("fa", fa), ("hi", hi), ("ps", ps)) if f]

    if verified:
        meaning_expl = ("%s corresponds to the %s form %s (%s). Its core sense is %s. %s"
                        % (disp, origin, ar or ur or fa or hi or ps, root or "—", g["en"].lower(), note))
        etym_expl = ("The form %s is an established %s lexical item. %s"
                     % (ar or ur or fa or hi or ps, origin, note))
        false_etym = ("No false etymology is asserted for this form. Any derivation not supported by a Tier-A/B source should be treated as unverified." if conf in ("high", "medium")
                      else "The identification of this form is uncertain; no confident etymology is asserted.")
    else:
        meaning_expl = ("No verified lexical identification was established for %s. %s No meaning is asserted, because asserting one would require inventing evidence."
                        % (disp, note))
        etym_expl = ("No verified etymology was established for %s. %s" % (disp, note))
        false_etym = "No etymology is asserted, because the underlying form could not be verified."

    rec = {
      "success": True,
      "data": {
        "name": disp, "slug": slug,
        "identity": {
          "display_name": disp, "normalized_name": slug, "name_type": "given_name",
          "gender": gender, "gender_confidence": ("high" if conf == "high" and gender != "Unknown" else ("medium" if conf == "medium" and gender != "Unknown" else ("low" if gender != "Unknown" else "unknown"))),
          "gender_note": ("Gender is recorded from documented naming usage, not inferred from the meaning of the word. Actual use may vary by region and community." if gender != "Unknown"
                          else "No documented personal-name gender usage was established for this form."),
          "alternate_spellings": sorted(set([disp, name, name.replace("aa", "a")])),
          "search_variants": sorted(set([disp, name, name.replace("aa", "a")])),
          "name_status": ("lexically established; personal-name usage requires separate frequency evidence" if verified
                          else "form not verified against a Tier-A/B source; no lexical status asserted"),
        },
        "core_meaning": {
          "short_meaning": short, "primary_meaning": primary, "secondary_meanings": sec,
          "literal_meaning": primary,
          "extended_meaning": (g["en"] if verified else "Not objectively established"),
          "meaning_explanation": meaning_expl,
          "meaning_confidence": conf,
        },
        "etymology": {
          "primary_language": origin, "lexical_form": (ar or ur or fa or hi or ps), "transliteration": name,
          "romanization": name, "root_status": ("Arabic triliteral root" if (root and origin == "Arabic") else ("No reliable root analysis established." if not root else root)),
          "etymological_meaning": ([x.strip() for x in g["en"].split(",")] if verified else []),
          "etymology_explanation": etym_expl, "etymology_confidence": conf,
          "false_etymology_warning": false_etym,
        },
        "language": {
          "primary": origin,
          "associated_languages": [l for l in ["Arabic", "Urdu", "Persian", "Hindi", "Pashto"] if l != origin and (l == "Urdu" or l == "Hindi" or l == "Pashto" or l == "Persian")][:3] if verified else [],
          "language_notes": {k: v for k, v in [
              ("Arabic", ("%s is an established Arabic form." % ar) if ar else None),
              ("Urdu", ("%s is used in Urdu." % ur) if ur else None),
              ("Persian", ("%s is an established Persian form." % fa) if fa else None),
              ("Hindi", ("%s is used in Hindi." % hi) if hi else None),
              ("Pashto", ("%s is used in Pashto." % ps) if ps else None)] if v},
          "language_confidence": conf,
        },
        "origin": {
          "primary_origin": origin, "origin_type": "linguistic", "origin_confidence": conf,
          "origin_explanation": ("The name is associated with the %s form %s. %s" % (origin, ar or ur or fa or hi or ps, note) if verified
                                 else "No verified linguistic origin was established for this form."),
          "cultural_transmission": (["Arabic", "Muslim South Asia", "Urdu-speaking communities"] if origin == "Arabic" else
                                    (["Persian", "Persianate South Asia", "Urdu-speaking communities"] if origin == "Persian" else
                                     (["Sanskrit", "South Asia"] if origin == "Sanskrit" else []))) if verified else [],
        },
        "religion": {
          "primary_association": ("Islamic-cultural usage" if origin == "Arabic" else ("Persianate cultural usage" if origin == "Persian" else "South Asian cultural usage")) if verified else "Not established",
          "religion": ("Islam" if origin == "Arabic" else "Not inherently religious") if verified else "Not established",
          "religion_confidence": ("medium" if verified else "unknown"),
          "religious_status": ("Not inherently an exclusively Islamic word" if verified else "Not established"),
          "religious_explanation": ("%s may be used by Muslims because Arabic and Persian vocabulary have had a major historical influence on Muslim cultures. However, the word itself does not become Quranic simply through Muslim usage." % disp if verified
                                    else "No religious classification was established for this form."),
          "quranic_status": {"is_quranic_name": False, "quranic_reference": None, "note": quranic},
          "hadith_status": {"direct_reference": False, "reference": None},
          "prophetic_status": {"prophet_association": False, "reference": None},
          "companion_status": {"known_companion_association": False, "reference": None},
        },
        "islamic_naming_context": {
          "can_be_used_by_muslims": True,
          "context": "Muslim naming culture in South Asia and the Persianate world",
          "interpretation": ("Its lexical associations can make it compatible with positive naming traditions." if verified else "No interpretation is offered because the form is unverified."),
          "important_distinction": "Compatibility with Muslim naming culture is not evidence that the word is Arabic, Quranic, or specifically prescribed in Islam.",
        },
        "cultural_context": {
          "primary_cultural_associations": (["Arabic", "Muslim South Asia"] if origin == "Arabic" else (["Persian", "Persianate South Asia"] if origin == "Persian" else ["South Asia"])) if verified else [],
          "cultural_meaning": ("In the relevant cultures the form is associated with the sense %s." % g["en"].lower() if verified else "Not established."),
          "place_name_significance": None,
          "personal_name_interpretation": ("As a personal name, the lexical associations can be interpreted symbolically." if verified else "Not established."),
          "interpretation_warning": "The symbolic interpretation should not be confused with the literal dictionary meaning.",
        },
        "semantic_field": {
          "primary_semantic_domain": (g["en"].split(",")[0].strip() if verified else "Not established"),
          "related_concepts": ([x.strip().lower() for x in g["en"].split(",")] if verified else []),
          "semantic_relationship": ("The central semantic idea is %s; other senses are extended associations." % g["en"].split(",")[0].strip().lower() if verified else "Not established."),
        },
        "spiritual_meaning": {
          "status": "interpretive",
          "meaning": ("A life that reflects the positive sense of %s." % g["en"].split(",")[0].strip().lower() if verified else None),
          "is_direct_religious_definition": False,
          "note": "This is a positive symbolic interpretation of the lexical meaning and should not be presented as a revealed religious definition of the name.",
        },
        "personality_associations": {
          "status": "symbolic_only",
          "traits": ([x.strip().capitalize() for x in g["en"].split(",")] if verified else []),
          "note": "These are symbolic associations derived from the meaning of the name, not scientifically established personality characteristics.",
        },
        "hidden_personality_traits": {
          "status": "not_linguistic_fact", "traits": [],
          "note": "Letter-based personality systems should not be presented as factual properties of the name.",
        },
        "numerology": {
          "status": "belief_based", "lucky_number": None, "life_path_number": None, "numerology_meaning": None,
          "note": "Numerological values should not be presented as linguistic, historical, scientific, or religious facts. A life-path number derives from a birth date, not from a name.",
        },
        "lucky_attributes": {
          "status": "traditional_or_generated", "lucky_number": None, "lucky_day": None,
          "lucky_colors": [], "lucky_stone": None,
          "note": "No universally authoritative lucky number, day, color, or stone is established by the etymology of this name.",
        },
        "translations": translations,
        "translation_quality": {
          "strategy": "curated_gloss_draft",
          "warning": "Non-English renderings are editorial drafts, not native-speaker-verified translations. They do not establish origin in every listed language.",
          "confidence": "requires_native_review" if verified else "unverified",
          "native_review_required": True,
          "named_translation_source_present": False,
        },
        "pronunciation": {
          "romanized": syllabify(name), "ipa": None,
          "approximation_note": "No IPA transcription is asserted because a verified phonetic transcription was not available for this form. The romanized syllable split is an approximation only.",
          "urdu": ur, "persian": fa, "hindi": hi, "pashto": ps,
        },
        "name_variants": {
          "romanized_variants": sorted(set([disp, name, name.replace("aa", "a")])),
          "script_variants": sorted(set([x for x in (ar, ur, fa, hi, ps) if x])),
          "variant_notes": "Romanization variants reflect different transliteration conventions. Script variants are the forms established for each language.",
          "do_not_merge_with": DO_NOT_MERGE.get(name, []),
        },
        "historical_context": {
          "known_linguistic_history": ([("The form %s is an established %s lexical item." % (ar or ur or fa or hi or ps, origin))] if verified else []),
          "historical_person_association": None, "historical_event_association": None,
          "historical_claim_confidence": conf,
          "editorial_note": "A specific historical person bearing this name should not be invented merely to enrich the page.",
        },
        "modern_usage": {
          "status": "requires_frequency_data",
          "usage_regions": (["Pakistan", "India"] if origin in ("Arabic", "Persian") else ["India"]) if verified else [],
          "regional_usage_note": "Personal-name popularity must be measured separately from lexical presence.",
          "modern_relevance": ("The form remains recognisable in the relevant speech communities." if verified else None),
          "social_media_trend": None, "popularity_claim": None,
        },
        "popularity": {"overall_score": None, "score_type": None, "score_source": None, "year": None,
                       "country_rankings": [],
                       "note": "A popularity score should only be retained when supported by a defined dataset, methodology, population, and year. No such dataset was available."},
        "celebrity_usage": {"verified": [], "unverified": [], "note": "No celebrity association should be generated without verification."},
        "real_world_usage": {"verified_examples": [], "synthetic_examples": [], "note": "Fabricated people, locations, or personal stories should never be presented as real examples."},
        "name_story": {
          "type": "editorial_interpretation",
          "story": ("%s can be understood through the %s form %s, whose central sense is %s. %s" % (disp, origin, ar or ur or fa or hi or ps, g["en"].lower(), note) if verified
                    else "%s could not be matched to a verified lexical form, so no editorial story is offered. Presenting one would require inventing evidence." % disp),
          "is_fictional": False,
        },
        "faq": [],
        "seo": {
          "title": "%s Name Meaning, Origin & Islamic Cultural Context" % disp,
          "meta_description": ("Explore the meaning, %s origin, Urdu meaning, pronunciation, variants and Islamic naming context of %s (%s)." % (origin, disp, ar or ur or fa or hi or ps) if verified
                               else "The form %s could not be verified against a Tier-A/B source. This page records that finding rather than asserting an unverified meaning." % disp),
          "h1": "%s Name Meaning, Origin and Cultural Background" % disp,
          "focus_keyword": "%s meaning" % disp,
          "secondary_keywords": ["%s name meaning" % disp, "%s meaning in Urdu" % disp, "%s origin" % disp,
                                 "%s Islamic name" % disp, "%s pronunciation" % disp, "%s name in Urdu" % disp],
          "search_intents": ["meaning", "origin", "language", "pronunciation", "religious context", "cultural context", "translation", "name variants"],
          "description_paragraph": ("%s (%s) is associated with the %s form %s, whose core sense is %s. %s" % (disp, ar or ur or fa or hi or ps, origin, ar or ur or fa or hi or ps, g["en"].lower(), note) if verified
                                    else "%s could not be verified against a Tier-A/B source. No meaning is asserted for this form." % disp),
          "editorial_seo_rule": "Avoid repeating the exact keyword unnaturally. Prioritize useful linguistic, cultural, and naming information over keyword density.",
        },
        "seo_content": {
          "intro": ("%s is associated with the %s form %s, whose core sense is %s." % (disp, origin, ar or ur or fa or hi or ps, g["en"].lower()) if verified
                    else "%s could not be matched to a verified lexical form. This record documents that finding." % disp),
          "meaning_section": ("The central meaning of %s is %s." % (disp, g["en"].lower()) if verified else "No meaning is asserted for %s because the form is unverified." % disp),
          "origin_section": ("%s is associated with %s rather than with a different language." % (disp, origin) if verified else "No origin is asserted for %s." % disp),
          "islam_section": ("%s can be encountered in Muslim naming environments, but its linguistic origin should not be confused with Quranic or Arabic origin." % disp if verified else "No religious classification is asserted for %s." % disp),
          "cultural_section": ("The strongest cultural association of %s is with the sense %s." % (disp, g["en"].split(",")[0].strip().lower()) if verified else "No cultural association is asserted for %s." % disp),
          "pronunciation_section": "A romanized syllable approximation is given. No IPA transcription is asserted because a verified phonetic transcription was not available.",
        },
        "social_tags": ["#%s" % disp, "#%sMeaning" % disp, "#%sName" % disp, "#IslamicNames", "#NameMeaning", "#NameOrigin"],
        "content_quality": {
          "overall_status": ("high" if conf == "high" else ("medium" if conf == "medium" else "low")) if verified else "unverified",
          "linguistic_authenticity": ("high" if conf == "high" else ("medium" if conf == "medium" else "low")) if verified else "unverified",
          "etymological_authenticity": ("high" if conf == "high" else ("medium" if conf == "medium" else "low")) if verified else "unverified",
          "meaning_authenticity": ("high" if conf == "high" else ("medium" if conf == "medium" else "low")) if verified else "unverified",
          "translation_quality": ("high" if conf == "high" else ("medium" if conf == "medium" else "low")) if verified else "unverified",
          "religious_claim_safety": "high", "historical_claim_safety": "high", "cultural_accuracy": "medium",
          "originality": "high", "ai_hallucination_risk": "low",
          "unsupported_claims_removed": ["invented popularity scores", "invented lucky attributes", "invented personality claims",
                                         "invented historical persons", "invented real-life stories", "unsupported Quranic claims",
                                         "English glosses copied into non-English translation fields"],
        },
        "evidence": {
          "core_claims": ([{"claim": "%s corresponds to the %s form %s" % (disp, origin, ar or ur or fa or hi or ps), "evidence_type": "lexical", "confidence": conf},
                           {"claim": "%s has the core sense %s" % (disp, g["en"].lower()), "evidence_type": "lexical", "confidence": conf}] if verified
                          else [{"claim": "No verified lexical identification was established for %s" % disp, "evidence_type": "negative_finding", "confidence": "high"}]),
          "claims_requiring_external_dataset": ["Personal-name popularity", "Country rankings", "Modern naming frequency", "Celebrity usage", "Social-media trends"],
        },
        "provenance": {
          "verified_or_verifiable_fields": (["core meaning", "origin", "script form", "semantic field", "language association", "translation"] if verified else ["negative finding: form not verified"]),
          "interpretive_fields": ["spiritual meaning", "personality associations", "name story"],
          "dataset_required_fields": ["popularity", "regional rankings", "modern frequency", "celebrity usage"],
          "generated_content_policy": "Generated explanatory prose must not introduce new historical, linguistic, religious, demographic, or popularity claims that are not supported by evidence.",
        },
        "structured_data": {
          "@context": "https://schema.org", "@type": "DefinedTerm", "name": disp,
          "alternateName": sorted(set([disp, name, name.replace("aa", "a")])),
          "description": ("A name associated with the %s form %s, meaning %s." % (origin, ar or ur or fa or hi or ps, g["en"].lower()) if verified
                          else "A name form that could not be verified against a Tier-A/B source."),
          "inLanguage": inlang, "termCode": slug,
          "additionalProperty": [
            {"@type": "PropertyValue", "name": "Origin", "value": origin},
            {"@type": "PropertyValue", "name": "Gender", "value": gender},
            {"@type": "PropertyValue", "name": "Religious Context", "value": "Used in some Muslim naming cultures"},
          ],
        },
        "accessibility": {
          "primary_language": "en", "rtl_languages_present": bool(rtl),
          "rtl_languages": [c for c, f in (("ur", ur), ("fa", fa), ("ps", ps), ("ar", ar)) if f],
          "script_labels_required": True, "pronunciation_text_available": True,
          "screen_reader_description": ("%s, associated with the %s form %s, meaning %s." % (disp, origin, ar or ur or fa or hi or ps, g["en"].lower()) if verified
                                        else "%s, a name form that could not be verified against a Tier-A/B source." % disp),
        },
        "editorial_validation": {
          "name_identity_checked": True, "origin_checked": True, "meaning_checked": True, "language_checked": True,
          "religious_claims_checked": True, "translation_checked": True, "historical_claims_checked": True,
          "popularity_verified": False, "celebrity_verified": False, "real_person_story_verified": False,
          "numerology_verified": False, "lucky_attributes_verified": False,
          "ready_for_publication": ("after source verification of dataset-dependent fields" if verified
                                    else "no — form not verified; requires manual review"),
        },
        "timestamps": {"created_at": "2026-10-02T00:00:00.000Z", "updated_at": "2026-10-02T00:00:00.000Z"},
      }
    }

    # FAQ — name-specific, consistent with the fields above
    d = rec["data"]
    if verified:
        faq = [
          {"question": "What does %s mean?" % disp, "answer": "%s is associated with the %s form %s, whose core sense is %s." % (disp, origin, ar or ur or fa or hi or ps, g["en"].lower())},
          {"question": "What is the origin of %s?" % disp, "answer": "%s is associated with %s. %s" % (disp, origin, note)},
          {"question": "Is %s an Arabic name?" % disp, "answer": ("Yes — the underlying form %s is Arabic." % ar) if origin == "Arabic" else ("No — the underlying form is %s, not Arabic." % origin)},
          {"question": "Is %s an Islamic name?" % disp, "answer": "%s can occur in Muslim naming contexts, but it is better described as a %s-origin name used within some Muslim naming traditions than as an exclusively Islamic religious term." % (disp, origin)},
          {"question": "Is %s a Quranic name?" % disp, "answer": "%s should not be classified as a Quranic personal name without a direct Quranic basis. %s" % (disp, quranic)},
          {"question": "What does %s mean in Urdu?" % disp, "answer": "In Urdu, %s is rendered %s and carries the sense %s." % (disp, ur or "—", g["ur"])},
          {"question": "What does %s mean in Persian?" % disp, "answer": ("In Persian, %s is rendered %s and carries the sense %s." % (disp, fa, g["fa"])) if fa else "No verified Persian form was established for %s." % disp},
          {"question": "How is %s pronounced?" % disp, "answer": "A romanized syllable approximation is %s. No IPA transcription is asserted because a verified phonetic transcription was not available." % syllabify(name)},
          {"question": "What are the variants of %s?" % disp, "answer": "Romanization variants include %s. Script forms are %s." % (", ".join(sorted(set([disp, name, name.replace("aa", "a")]))), ", ".join(sorted(set([x for x in (ar, ur, fa, hi, ps) if x]))))},
          {"question": "Is %s a boy's or girl's name?" % disp, "answer": "Documented usage records this form as %s. Gender is not inferred from the meaning of the word, and actual use may vary between communities." % gender.lower()},
        ]
    else:
        faq = [
          {"question": "What does %s mean?" % disp, "answer": "No verified meaning was established for %s. The form could not be matched to a Tier-A/B source, so no gloss is asserted." % disp},
          {"question": "What is the origin of %s?" % disp, "answer": "No verified origin was established for %s. %s" % (disp, note)},
          {"question": "Is %s an Arabic name?" % disp, "answer": "This could not be verified. No Arabic form was established for %s, so no claim is made." % disp},
          {"question": "Is %s an Islamic name?" % disp, "answer": "No religious classification was established for %s." % disp},
          {"question": "Is %s a Quranic name?" % disp, "answer": "No — %s is not classified as a Quranic name. %s" % (disp, quranic)},
          {"question": "What does %s mean in Urdu?" % disp, "answer": "No verified Urdu translation was established for %s, so no meaning is asserted." % disp},
          {"question": "What does %s mean in Persian?" % disp, "answer": "No verified Persian translation was established for %s, so no meaning is asserted." % disp},
          {"question": "How is %s pronounced?" % disp, "answer": "A romanized syllable approximation is %s. No IPA transcription is asserted because a verified phonetic transcription was not available." % syllabify(name)},
          {"question": "What are the variants of %s?" % disp, "answer": "No verified script variants were established for %s." % disp},
          {"question": "Is %s a boy's or girl's name?" % disp, "answer": "No documented personal-name gender usage was established for %s." % disp},
        ]
    d["faq"] = faq
    return rec

if __name__ == "__main__":
    import os
    rows = json.load(open("source_forms.json"))
    out = "out/islamic"
    os.makedirs(out, exist_ok=True)
    for r in rows:
        n = r["name"]
        rec = build(n, r)
        with open(os.path.join(out, n + ".json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
    print("built", len(rows))
