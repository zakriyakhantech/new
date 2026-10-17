#!/usr/bin/env python3
"""Build the curated Qur'anic/Islamic supplement batch (October 2026).

The builder copies the repository's current super-2.0 template (aaban.json),
fills every data section from a reviewed, per-name evidence table, audits the
whole dataset for Latin and Arabic-script collisions, checks key-path parity
with the template, and only then writes the records.

Usage:
    python3 upgrading/scripts/add_quranic_names_2026_10.py            # dry run
    python3 upgrading/scripts/add_quranic_names_2026_10.py --write    # write files
    python3 upgrading/scripts/add_quranic_names_2026_10.py --check    # verify persisted files

No network access and no third-party dependencies are used.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET = REPO_ROOT / "upgrading" / "names_upgraded" / "islamic"
TEMPLATE = DATASET / "aaban.json"
MANIFEST = REPO_ROOT / "upgrading" / "name_batches" / "quranic_2026-10.json"
VERIFICATION_CSV = DATASET / "ISLAMIC_VERIFICATION_MANIFEST.csv"
PROGRESS_JSON = DATASET / "PROGRESS_QURANIC_2026-10.json"

CREATED_AT = "2026-10-17T00:00:00+00:00"
REVIEWED_AT = "2026-10-17"
BATCH_ID = "quranic-islamic-2026-10"

ARABIC_TRANSLITERATION_MAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي",
    "ی": "ي", "ے": "ي", "ئ": "ي", "ؤ": "و",
    "ة": "ه", "ہ": "ه", "ھ": "ه", "ک": "ك",
})

COLLECTION_POLICY = [
    "A name is added only if its canonical Romanized spelling and its Arabic script form are both absent from every existing record, including alternate spellings, search variants, merged aliases, localized script forms and pronunciation scripts.",
    "Qur'anic status is recorded as a textual fact about the name, never as a personal-name claim or a religious ruling.",
    "Every lexical, scriptural and biographical claim is separated from name-site glosses; no popularity figure is asserted where no source-scoped measurement exists.",
    "Numerology, lucky attributes, personality claims and invented name stories are suppressed.",
    "All non-English glosses are editorial drafts flagged for native-speaker review.",
]


def norm_latin(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).lower()
    return "".join(ch for ch in value if ch.isascii() and ch.isalnum())


def norm_script(value: str) -> str:
    value = unicodedata.normalize("NFC", value).translate(ARABIC_TRANSLITERATION_MAP)
    out: list[str] = []
    for ch in value:
        if ch == "ـ":
            continue
        cat = unicodedata.category(ch)
        if cat.startswith("M") and "ARABIC" in unicodedata.name(ch, ""):
            continue
        if ch.isalnum() or cat.startswith("M"):
            out.append(ch)
    return "".join(out)


def scalar_leaf_count(value: Any) -> int:
    if isinstance(value, dict):
        return sum(scalar_leaf_count(v) for v in value.values())
    if isinstance(value, list):
        return sum(scalar_leaf_count(v) for v in value)
    return 1


def key_paths(obj: Any, prefix: str = "") -> list[str]:
    out: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            out += key_paths(value, prefix + "." + key)
    elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
        out += key_paths(obj[0], prefix + "[]")
    else:
        out.append(prefix)
    return out


def build_record(entry: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    record = copy.deepcopy(template)
    data = record["data"]
    name = entry["name"]
    slug = entry["slug"]
    arabic = entry["ar"]
    root = entry.get("root", "")
    root_tr = entry.get("roottr", "")
    quran = entry["quran"]
    confidence = entry.get("mconf", "HIGH")
    aliases = list(dict.fromkeys(entry.get("aliases", [])))
    gender = entry["gender"]
    gender_lower = "masculine" if gender == "Male" else "feminine"

    record["schema_version"] = template["schema_version"]
    record["success"] = True
    data["name"] = name
    data["slug"] = slug
    data["content_revision"] = "v8"
    data["page_type"] = "name_meaning"

    data["identity"] = {
        "display_name": name,
        "normalized_name": slug,
        "name_type": "given_name",
        "gender": gender,
        "gender_confidence": entry.get("gconf", "HIGH"),
        "gender_note": (
            f"{name} is recorded as a {gender_lower} given name in the sources cited in this "
            "record; actual use can vary by community."
        ),
        "alternate_spellings": list(dict.fromkeys([name, *aliases])),
        "name_status": entry.get("name_status", "attested"),
    }

    data["core_meaning"] = {
        "short_meaning": entry["short"],
        "primary_meaning": entry["primary"],
        "literal_meaning": entry["literal"],
        "meaning_explanation": entry["explain"],
        "meaning_confidence": confidence,
    }

    if root:
        origin_sentence = (
            f"The recorded form {arabic} is Arabic, and its root is {root} ({root_tr})."
        )
    else:
        origin_sentence = (
            f"The recorded form {arabic} is Arabic; no productive Arabic root is asserted for "
            "this proper name."
        )

    data["etymology"] = {
        "primary_language": "Arabic",
        "lexical_form": arabic,
        "transliteration": entry["tr"],
        "root": root,
        "root_transliteration": root_tr,
        "morphology": entry["morph"],
        "feminine_form": entry.get("feminine_form"),
        "etymological_meaning": entry["literal"],
        "root_family": [],
        "etymology_explanation": entry.get("etym_explain", entry["explain"]),
        "etymology_confidence": confidence,
        "false_etymology_warning": entry.get(
            "false_warning",
            "No derivation beyond the documented lexical, scriptural or biographical evidence is "
            "asserted; unsupported name-site etymologies are not adopted.",
        ),
    }

    data["language"] = {
        "primary": "Arabic",
        "associated_languages": ["Arabic"],
        "language_notes": {
            "primary": f"Arabic is the language of the recorded form {arabic}.",
            "usage": (
                "Other scripts in this record are transliterations or localized glosses; they are "
                "not independent origins."
            ),
        },
        "language_confidence": confidence,
    }

    data["origin"] = {
        "primary_origin": "Arabic",
        "origin_type": "linguistic",
        "origin_confidence": confidence,
        "origin_explanation": (
            origin_sentence + " The evidence distinguishes linguistic origin from religious and "
            "cultural use."
        ),
        "cultural_transmission": entry.get(
            "cult_trans", ["Arabic-speaking communities", "Muslim naming communities"]
        ),
    }

    data["religion"] = {
        "primary_association": entry.get(
            "rel_assoc",
            "Qur'anic and Muslim-cultural naming usage" if quran else "Arabic and Muslim-cultural naming usage",
        ),
        "religion_confidence": entry.get("rel_conf", "MEDIUM"),
        "religious_status": entry["rel_status"],
        "religious_explanation": entry["rel_explain"],
        "quranic_status": {
            "is_quranic": quran,
            "status": entry["qstatus"],
            "note": entry["qnote"],
        },
        "hadith_status": {"status": entry["hadith"][0], "note": entry["hadith"][1]},
        "prophetic_status": {"status": entry["prophetic"][0], "note": entry["prophetic"][1]},
        "companion_status": {"status": entry["companion"][0], "note": entry["companion"][1]},
    }

    data["islamic_naming_context"] = {
        "can_be_used_by_muslims": True,
        "context": entry.get(
            "rel_assoc",
            "Qur'anic and Muslim-cultural naming usage" if quran else "Arabic and Muslim-cultural naming usage",
        ),
        "interpretation": entry.get(
            "naming_note",
            "This record describes documented usage; it is not a religious ruling on naming.",
        ),
        "important_distinction": (
            "This descriptive record is not a religious ruling. Muslim cultural use, linguistic "
            "origin, and direct Qur'anic attestation are separate claims."
        ),
    }

    data["cultural_context"] = {
        "primary_cultural_associations": entry.get(
            "cult_assoc", ["Arabic", "Muslim naming communities"]
        ),
        "cultural_meaning": entry["cult_note"],
        "personal_name_interpretation": entry["cult_interp"],
        "interpretation_warning": (
            "A symbolic naming preference is distinct from dictionary meaning and is not a claim "
            "about a bearer's personality or future."
        ),
    }

    data["semantic_field"] = {
        "primary_semantic_domain": entry["sem"],
        "related_concepts": list(entry["concepts"]),
    }

    data["spiritual_meaning"] = {
        "status": "not_asserted",
        "render": False,
        "meaning": None,
        "basis": None,
        "is_direct_religious_definition": False,
    }
    data["personality_associations"] = {
        "status": "not_verified",
        "render": False,
        "note": "No verified basis links this name to specific personality traits.",
    }
    data["hidden_personality_traits"] = {
        "status": "not_verified",
        "render": False,
        "note": "No evidence-based hidden personality traits are asserted.",
    }
    data["numerology"] = {
        "status": "not_verified",
        "render": False,
        "lucky_number": None,
        "life_path_number": None,
        "ruling_planet": None,
        "lucky_day": None,
        "lucky_colors": [],
        "lucky_stone": None,
        "meaning": None,
        "note": "Numerology is not evidence-based and is not supplied in this batch.",
    }
    data["lucky_attributes"] = {
        "status": "not_verified",
        "render": False,
        "lucky_number": None,
        "lucky_day": None,
        "lucky_colors": [],
        "lucky_stone": None,
        "ruling_planet": None,
        "note": "Lucky attributes are not evidence-based and are not supplied in this batch.",
    }

    long_templates = {
        "urdu": (
            "{name} کے لغوی معنی «{meaning}» ہیں۔ یہ اندراج دینی حوالے اور نام کے استعمال کو "
            "الگ الگ بیان کرتا ہے؛ یہ ترجمہ ابتدائی مسودہ ہے اور مقامی جائزے کا محتاج ہے۔"
        ),
        "persian": (
            "معنای لغوی {name} در این مدخل «{meaning}» است. این مدخل مرجع دینی و کاربرد نام را "
            "جداگانه بیان می‌کند؛ این برگردان پیش‌نویس است و به بازبینی بومی نیاز دارد."
        ),
        "hindi": (
            "{name} का शब्दार्थ «{meaning}» दिया गया है। यह प्रविष्टि धार्मिक संदर्भ और "
            "नाम-प्रयोग को अलग-अलग बताती है; यह अनुवाद प्रारूप है और स्थानीय भाषायी समीक्षा आवश्यक है।"
        ),
        "pashto": (
            "د {name} لغوي مانا «{meaning}» دی. دا اندراج دیني حواله او د نوم کارونه بېل بېل "
            "بیانوي؛ دا ژباړه مسوده ده او د اصلي ژبې ویونکو بیاکتنې ته اړتیا لري."
        ),
        "arabic": (
            "المعنى اللغوي لاسم {name} في هذا السجل هو «{meaning}»؛ ويفصل السجل بين المرجع الديني "
            "واستعمال الاسم، وهذه صياغة أولية تحتاج إلى مراجعة لغوية."
        ),
    }
    translations: dict[str, Any] = {
        "english": {
            "name": name,
            "script": arabic,
            "meaning": entry["short"],
            "long_meaning": entry["primary"],
        }
    }
    for locale in ("urdu", "persian", "hindi", "pashto", "arabic"):
        script, meaning = entry["trs"][locale]
        item: dict[str, Any] = {
            "name": script,
            "script": script,
            "meaning": meaning,
            "long_meaning": long_templates[locale].format(name=script, meaning=meaning),
        }
        if locale in {"pashto", "arabic"}:
            item["native_review_required"] = True
        translations[locale] = item
    data["translations"] = translations

    data["translation_quality"] = {
        "strategy": "source_language_gloss_with_localized_draft",
        "confidence": "MEDIUM",
        "native_review_required": True,
        "note": (
            "The Arabic core gloss is evidence-backed. All non-English localized meanings and "
            "script renderings are editorial drafts requiring native-speaker review; "
            "transliteration does not establish a separate origin."
        ),
    }

    data["pronunciation"] = {
        "romanized": entry["pron"],
        "ipa": None,
        "approximation_note": entry.get(
            "pron_note",
            "Romanized pronunciation guide only; no IPA transcription is asserted.",
        ),
        "common_mispronunciation": entry.get("mispron"),
        "scripts": {"arabic": arabic},
    }

    script_forms = [arabic]
    hindi_form = entry["trs"]["hindi"][0]
    if hindi_form not in script_forms:
        script_forms.append(hindi_form)
    data["name_variants"] = {
        "romanized_variants": aliases,
        "script_forms": script_forms,
        "variant_notes": (
            "Spelling variants reflect transliteration conventions, not different names."
        ),
        "do_not_merge_with": list(entry.get("dnmerge", [])),
    }

    data["related_names"] = list(entry.get("related", []))
    data["historical_context"] = {
        "status": entry.get("hist_status", "documented_in_classical_sources"),
        "note": entry["hist_note"],
    }
    data["modern_usage"] = {
        "status": "requires_frequency_data",
        "note": entry.get(
            "usage_note",
            "Usage is attested as a Muslim given name, but no registration or frequency data is "
            "measured in this batch.",
        ),
    }
    data["popularity"] = {
        "status": "not_measured",
        "render": False,
        "score": None,
        "by_region": [],
        "note": (
            "No verified popularity or registration data is measured in this batch; no estimate "
            "is asserted."
        ),
    }
    data["celebrity_usage"] = {
        "status": "not_verified",
        "render": False,
        "items": [],
        "note": "No verified celebrity usage is included.",
    }
    data["real_world_usage"] = {
        "status": "not_verified",
        "render": False,
        "note": "No individual bearer story is included without a verified source.",
    }
    data["name_story"] = {"status": "none", "render": False, "story": ""}

    gender_answer = (
        f"The sources cited record {name} as a {gender_lower} given name; actual use can vary by "
        "language and community."
    )
    root_answer = (
        f"The recorded Arabic root is {root} ({root_tr})."
        if root
        else "No triliteral Arabic root is asserted for this proper name."
    )
    faq = [
        {"q": f"What does {name} mean?", "a": entry["primary"]},
        {
            "q": f"What is the origin of {name}?",
            "a": entry["explain"],
        },
        {
            "q": f"Is {name} an Arabic name?",
            "a": f"Yes. The recorded form is {arabic}; the name is associated with Arabic.",
        },
        {"q": f"How is {name} written in Arabic?", "a": arabic},
        {"q": f"Is {name} a Quranic name?", "a": entry["qnote"]},
        {
            "q": f"Is {name} an Islamic name?",
            "a": f"{entry['rel_status']} {entry['rel_explain']}",
        },
        {
            "q": f"How is {name} pronounced?",
            "a": (
                f"An approximate romanized guide is {entry['pron']}. "
                + entry.get(
                    "pron_note",
                    "Romanized pronunciation guide only; no IPA transcription is asserted.",
                )
            ),
        },
        {"q": f"Is {name} a boy's or girl's name?", "a": gender_answer},
        {"q": f"What is the root of {name}?", "a": root_answer},
        {
            "q": f"What should be checked before relying on this entry?",
            "a": (
                "The cited sources are listed with their scope and limitations but have not been "
                "independently rechecked in this pass. Non-English renderings are drafts pending "
                "native review, and no popularity figure is asserted."
            ),
        },
    ]
    data["faq"] = faq

    keywords = [
        f"{name} meaning",
        f"{name} name meaning",
        f"{name} Arabic name",
        f"{name} origin",
        f"{name} pronunciation",
        f"{name} Islamic name",
        f"{name} meaning in Urdu",
    ]
    canonical = f"https://nameverse.site/names/islamic/{slug}"
    data["seo"] = {
        "title": f"{name} Name Meaning, Origin & Islamic Context",
        "meta_description": (
            f"{name} name meaning, Arabic origin, pronunciation and sourced Qur'anic-status notes."
        ),
        "meta_keywords": ", ".join(keywords),
        "description_paragraph": entry["primary"],
        "keywords": keywords,
        "focus_keyword": f"{name} meaning",
        "secondary_keywords": keywords[1:],
        "canonical_url": canonical,
        "seo_score": None,
        "seo_score_basis": (
            "Not numerically scored in this focused review; factual clarity prioritized over an "
            "unsupported score."
        ),
    }
    data["seo_content"] = {
        "intro_paragraph": (
            f"{name} is an Arabic given name. This entry separates its documented meaning, "
            "linguistic origin, religious or scriptural status, and modern usage."
        ),
        "body_summary": entry["primary"],
    }
    plain_name = name.replace(" ", "")
    data["social_tags"] = [
        f"#{plain_name}",
        f"#{plain_name}Meaning",
        "#NameMeaning",
        "#ArabicNames",
        "#IslamicNames",
    ]

    flags = list(entry.get("flags", []))
    flags.append("localized_translations_require_native_review")
    flags.append("popularity_not_measured_in_this_batch")
    data["content_quality"] = {
        "tier1_verified": False,
        "authenticity_flags": flags,
        "fabricated_content_removed": True,
        "fields_total": 0,
        "quality_score": None,
        "quality_score_basis": (
            "No composite quality score is asserted; source support, limitations, scriptural "
            "status and review flags are explicit. Tier-1 verification is false because the "
            "listed sources were not independently rechecked in this pass."
        ),
        "tier1_verified_scope": (
            "Core meaning and associated claims were matched to the listed sources in this pass; "
            "independent re-verification, native translation review and usage-frequency evidence "
            "remain separate outstanding tasks, so tier1_verified is false."
        ),
    }

    sources = []
    for title, url, supports, limitation in entry["evidence"]:
        if url:
            text = f"{url} — {title}: {supports}"
        else:
            text = f"{title}: {supports}"
        text += f" Limitation: {limitation}"
        sources.append(text)
    data["evidence"] = {
        "sources": sources,
        "verification_method": (
            "The lexical, scriptural or biographical claim was separated from name-site glosses "
            "and matched to a cited primary text, classical lexicon or biographical reference; "
            "the cited sources were not independently rechecked in this pass. Latin and Arabic-script "
            "forms were audited against every existing record "
            "before writing. No popularity figure is asserted without a source-scoped "
            "measurement."
        ),
        "claim_evidence": [
            {"claim": claim, "source": source, "status": status}
            for claim, source, status in entry["claims"]
        ],
        "claim_evidence_status": "SOURCE_URLS_LISTED_NOT_INDEPENDENTLY_RECHECKED_IN_THIS_PASS",
    }

    data["provenance"] = {
        "pipeline": "NameVerse super-2.0 curated Qur'anic/Islamic supplement",
        "methodology": (
            "Curated evidence manifest -> template-parity build -> Latin and Arabic-script "
            "collision audit -> schema and key-path validation"
        ),
        "upgraded_from": (
            "New record generated from the current super-2.0 architecture; not converted from a "
            "legacy record."
        ),
        "processed_at": CREATED_AT,
    }

    faq_nodes = [
        {
            "@type": "Question",
            "name": item["q"],
            "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
        }
        for item in faq
    ]
    data["structured_data"] = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "DefinedTerm",
                "name": name,
                "description": f"{name} ({arabic}) — {entry['short']}",
                "inDefinedTermSet": {"@type": "DefinedTermSet", "name": "NameVerse Islamic Names"},
            },
            {"@type": "FAQPage", "mainEntity": faq_nodes},
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://nameverse.site/"},
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Islamic Names",
                        "item": "https://nameverse.site/names/islamic",
                    },
                    {"@type": "ListItem", "position": 3, "name": name, "item": canonical},
                ],
            },
        ],
    }

    data["editorial_validation"] = {
        "needs_manual_verification": True,
        "flags": flags,
        "confidence": confidence,
        "reviewed_by": (
            "Automated source-aware build and collision audit; not a human or native-speaker review"
        ),
        "reviewed_at": REVIEWED_AT,
    }
    data["render_policy"] = {
        "render_verified": True,
        "render_interpretive": False,
        "hide_unverified": True,
        "single_definition_source": "core_meaning.primary_meaning",
        "non_rendered_definition_fields": [
            "core_meaning.short_meaning",
            "core_meaning.literal_meaning",
            "semantic_field",
            "etymology.etymological_meaning",
        ],
        "hidden_sections": [
            "personality_associations",
            "hidden_personality_traits",
            "popularity",
            "celebrity_usage",
            "real_world_usage",
            "spiritual_meaning",
            "name_story",
        ],
    }

    data["content_quality"]["fields_total"] = scalar_leaf_count(data)
    return record


DATA: list[dict[str, Any]] = []

DATA += [
    {
        "name": "Dhul-Qarnayn",
        "slug": "dhulqarnayn",
        "gender": "Male",
        "gconf": "MEDIUM",
        "aliases": ["Dhul Qarnayn", "Zulqarnain", "Zulqarnayn", "Dhulqarnain"],
        "ar": "ذُو الْقَرْنَيْن",
        "tr": "dhū al-qarnayn",
        "root": "ق ر ن",
        "roottr": "q-r-n",
        "morph": "Construct phrase: ذو (possessor of) + القرنين (the two horns); used in the Qur'an as a title.",
        "short": "Qur'anic title meaning “the possessor of the two horns”",
        "primary": (
            "Dhul-Qarnayn (ذو القرنين, “the possessor of the two horns”) is the title by which the "
            "Qur'an refers to a righteous monarch whose story is told in Surah al-Kahf (18:83–98). "
            "The Qur'an gives a title rather than a personal name, and the historical identification "
            "of the figure is disputed among exegetes and historians. As a given name it is rare and "
            "usually commemorative."
        ),
        "literal": "Possessor of the two horns",
        "explain": (
            "The expression is a construct (iḍāfa) of ذو “possessor of” and القرنين “the two horns”. "
            "The Qur'an uses it as a title, not as a personal name, and does not explain the epithet. "
            "Classical explanations include two locks of hair, two horns, two eras, or rule over east "
            "and west; this record reports the disagreement without adopting a speculative "
            "identification."
        ),
        "mconf": "MEDIUM",
        "sem": "Qur'anic narrative and just rule",
        "concepts": ["Surah al-Kahf", "just ruler", "Yajuj and Majuj"],
        "quran": True,
        "qstatus": "title_attested_in_quran",
        "qnote": (
            "The title appears in Qur'an 18:83–98, where the narrative of Dhul-Qarnayn is related; "
            "the Qur'an does not give a personal name or a definitive historical identification."
        ),
        "rel_assoc": "Qur'anic narrative",
        "rel_conf": "MEDIUM",
        "rel_status": "A Qur'anic title, not a divine name or a prophetic name established by the Qur'an.",
        "rel_explain": (
            "The Qur'an presents Dhul-Qarnayn as a righteous ruler in the al-Kahf narrative. "
            "Classical scholars debated his identity and whether he was a prophet; this record "
            "asserts neither."
        ),
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("disputed", "Some classical reports describe him as a prophet or a righteous king; the Qur'an does not state this, so the record leaves the question open."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "naming_note": "Muslim families may use it as a commemorative Qur'anic title-name; this record describes usage and does not issue a naming ruling.",
        "cult_note": "The name is associated with the Qur'anic story of a just ruler who builds a barrier against Yajuj and Majuj (18:83–98).",
        "cult_interp": "Choosing the name may express admiration for justice and protection, but that is a personal naming preference, not a claim about the bearer.",
        "hist_status": "documented_in_Quran_and_classical_exegesis",
        "hist_note": "The narrative is given in Qur'an 18:83–98. Al-Ṭabarī and Ibn Kathīr record competing historical identifications; none is treated as settled.",
        "usage_note": "Usage is attested as a Muslim given name, but no registration or frequency data is measured here.",
        "trs": {
            "urdu": ("ذوالقرنین", "قرآن میں مذکور ایک نیک بادشاہ کا لقب، 'دو سینگوں والا'"),
            "persian": ("ذوالقرنین", "لقب پادشاه نیکوکاری که در قرآن آمده است، «صاحب دو شاخ»"),
            "hindi": ("ज़ुलक़र्नैन", "क़ुरआन में वर्णित एक नेक बादशाह का उपनाम, 'दो सींगों वाला'"),
            "pashto": ("ذوالقرنین", "د قرآن په ذکر شوي نیک پاچا لقب، 'دوه ښکرونه لرونکی'"),
            "arabic": ("ذو القرنين", "لقب ملك صالح ذُكر في القرآن، ومعناه صاحب القرنين"),
        },
        "pron": "dhul-qar-NAYN",
        "mispron": "zul-karnain (common South Asian spelling pronunciation)",
        "pron_note": "Romanized guide only; the Arabic ḏ/ḍ sounds have no exact English equivalent.",
        "evidence": [
            ("Qur'an 18:83–98", "https://quran.com/18/83", "The Qur'anic narrative of Dhul-Qarnayn and the title used for him.", "Scripture gives a title and narrative, not a personal name or a settled historical identification."),
            ("al-Ṭabarī, Jāmiʿ al-Bayān ʿan Taʾwīl al-Qurʾān", "", "Classical exegesis reporting competing identifications of Dhul-Qarnayn.", "Reports differ; not independently rechecked in this pass."),
        ],
        "claims": [
            ("Dhul-Qarnayn is a Qur'anic title for the righteous ruler in Surah al-Kahf", "https://quran.com/18/83", "primary_text_cited_not_rechecked_in_this_pass"),
            ("The historical identity of Dhul-Qarnayn is disputed", "al-Ṭabarī, Jāmiʿ al-Bayān", "classical_source_listed_not_rechecked"),
        ],
        "flags": ["Quranic_title_not_a_personal_name", "historical_identification_disputed"],
        "selection": "Included because the Qur'anic title is absent from the dataset but is used as a Muslim given name; the entry distinguishes title from personal name.",
    },
    {
        "name": "Uzair",
        "slug": "uzair",
        "gender": "Male",
        "gconf": "MEDIUM",
        "aliases": ["Uzayr", "Oozair"],
        "ar": "عُزَيْر",
        "tr": "ʿuzayr",
        "root": "",
        "roottr": "",
        "morph": "Proper name of non-Arabic origin, transmitted into Arabic.",
        "short": "Qur'anic figure identified in Islamic tradition with Ezra",
        "primary": (
            "Uzair (عزير) is the Arabic form of the name Ezra, mentioned once in the Qur'an (9:30). "
            "The verse reports and rejects a claim attributed to some Jews; the Qur'an does not "
            "present Uzair as a prophet, and later Islamic tradition differs about his status. The "
            "name is used, though rarely, as a male given name."
        ),
        "literal": "Ezra",
        "explain": (
            "The Qur'an mentions Uzair only in 9:30, in a polemical context. Arabic lexicography "
            "treats the form as a proper name transmitted from Hebrew ʿEzrā; no Arabic root meaning "
            "should be invented. The verse's rhetorical context is not evidence that the name is "
            "recommended or prohibited."
        ),
        "mconf": "MEDIUM",
        "sem": "Qur'anic mention and later tradition",
        "concepts": ["Ezra", "Qur'an 9:30", "polemical context"],
        "quran": True,
        "qstatus": "mentioned_in_quran",
        "qnote": "Uzair is mentioned in Qur'an 9:30; the verse reports and rejects a claim attributed to some Jews and does not present him as a prophet.",
        "rel_assoc": "Qur'anic mention",
        "rel_conf": "MEDIUM",
        "rel_status": "A Qur'anic proper name mentioned in a polemical verse; not a divine name or an established prophetic name.",
        "rel_explain": "The Qur'an mentions Uzair once (9:30). Classical tafsīr discusses his identity and status, and most scholars do not count him among the prophets; the record reports this without asserting a ruling.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Most classical scholars do not count Uzair as a prophet; the Qur'an does not present him as one."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "naming_note": "The name is used in some Muslim communities; this record describes the textual evidence and does not issue a naming ruling.",
        "cult_note": "The name is associated with the Qur'anic mention of Ezra and with later discussions of his status.",
        "cult_interp": "Use of the name may be commemorative or family-based; the record does not infer character from it.",
        "hist_status": "documented_in_Quran_and_classical_exegesis",
        "hist_note": "Qur'an 9:30 is the only Qur'anic mention. Al-Ṭabarī and Ibn Kathīr discuss reports about Uzair; details beyond the verse are not treated as established.",
        "usage_note": "Rare as a contemporary given name; no frequency data is measured here.",
        "trs": {
            "urdu": ("عزیر", "عزیر کا نام، جس کا ذکر قرآن میں ایک آیت میں آیا ہے"),
            "persian": ("عزیر", "نام عزیر که در یک آیه قرآن یاد شده است"),
            "hindi": ("उज़ैर", "उज़ैर का नाम, जिसका उल्लेख क़ुरआन में एक आयत में है"),
            "pashto": ("عزیر", "د عزیر نوم چې په قرآن کې په یوه آیت ذکر شوی"),
            "arabic": ("عزير", "اسم عزير المذكور في القرآن"),
        },
        "pron": "oo-ZAIR",
        "mispron": "uz-ZAIR",
        "evidence": [
            ("Qur'an 9:30", "https://quran.com/9/30", "The single Qur'anic mention of Uzair.", "The verse is polemical and does not present him as a prophet or provide a biography."),
            ("al-Ṭabarī, Jāmiʿ al-Bayān", "", "Classical exegesis on Qur'an 9:30 and reports about Uzair.", "Reports beyond the verse are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Uzair is mentioned in Qur'an 9:30", "https://quran.com/9/30", "primary_text_cited_not_rechecked_in_this_pass"),
            ("Most classical scholars do not count Uzair as a prophet", "al-Ṭabarī, Jāmiʿ al-Bayān", "classical_source_listed_not_rechecked"),
        ],
        "flags": ["single_polemical_Quranic_mention", "prophethood_not_asserted"],
        "selection": "Included because a Qur'anic proper name is absent from the dataset; the record avoids turning a polemical mention into a prophetic or virtue claim.",
    },
    {
        "name": "Wakil",
        "slug": "wakil",
        "gender": "Male",
        "aliases": ["Vakil", "Wakel"],
        "ar": "وَكِيل",
        "tr": "wakīl",
        "root": "و ك ل",
        "roottr": "w-k-l",
        "morph": "Arabic noun/adjective (faʿīl pattern) used as a divine name and as a personal name.",
        "short": "Trustee or disposer of affairs; a divine name in the Qur'an",
        "primary": (
            "Wakil (الوكيل) is a divine name meaning “the Trustee” or “the One who disposes of "
            "affairs”. It occurs in the Qur'an in verses such as 3:173, 4:81, 28:28, 33:3, 39:62 and "
            "73:9. In ordinary Arabic, wakīl also means a representative or attorney, and the word is "
            "used as a male given name."
        ),
        "literal": "Trustee, representative, or disposer of affairs",
        "explain": (
            "Arabic lexicography records wakīl as the person to whom a matter is entrusted, from the "
            "root و ك ل. The Qur'anic divine name الوكيل expresses God's sufficiency and disposal of "
            "affairs. Using it as a personal name is a Muslim naming convention; it does not "
            "attribute divinity to the bearer."
        ),
        "sem": "Trust, delegation and divine sufficiency",
        "concepts": ["trust", "delegation", "divine sufficiency"],
        "quran": True,
        "qstatus": "divine_name_attested",
        "qnote": "الوكيل occurs as a divine name in the Qur'an, including 3:173, 4:81, 33:3, 39:62 and 73:9; it is not used there as a person's name.",
        "rel_assoc": "Islamic monotheism; divine attribute (ṣifah)",
        "rel_status": "A divine name used as a personal name in Muslim communities.",
        "rel_explain": "The word is a Qur'anic divine name. Its use for a person is a naming convention and does not attribute divinity to the bearer.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "No verified source establishes Wakil as the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is understood through the Qur'anic theme of placing one's trust in God (tawakkul).",
        "cult_interp": "Families may value the sense of trust and reliance; this is a naming preference, not a prediction about the bearer.",
        "hist_status": "documented_in_Quran_and_classical_lexicography",
        "hist_note": "The divine name is attested in several Qur'anic verses; ordinary wakīl usage is pre-Islamic and continues in modern Arabic.",
        "trs": {
            "urdu": ("وکیل", "کارساز اور بھروسے والا؛ اللہ کا صفاتی نام"),
            "persian": ("وکیل", "کارساز و امین؛ نام صفتی خداوند"),
            "hindi": ("वकील", "कार्यसाधक और भरोसेमंद; ईश्वर का गुणवाचक नाम"),
            "pashto": ("وکیل", "د کار سمبالوونکی او باوري؛ د الله صفتي نوم"),
            "arabic": ("وَكِيل", "المتوكل بأمور خلقه، اسم من أسماء الله"),
        },
        "pron": "wa-KEEL",
        "mispron": "wa-kill",
        "evidence": [
            ("Qur'an 3:173 and 39:62", "https://quran.com/39/62", "The divine name al-Wakīl in Qur'anic context.", "The verses use the name for God, not as a human personal name."),
            ("Lane, An Arabic-English Lexicon (1863), root و ك ل", "", "Lexical senses of wakīl: trustee, representative, one entrusted with affairs.", "Classical dictionary senses are broader than the conventional name gloss."),
        ],
        "claims": [
            ("Al-Wakil is a Qur'anic divine name", "https://quran.com/39/62", "primary_text_cited_not_rechecked_in_this_pass"),
            ("Wakil is used as a male given name", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["divine_attribute_used_as_personal_name", "not_a_Quranic_person_name"],
        "selection": "Included because a Qur'anic divine name in common Muslim use is absent from the dataset.",
    },
    {
        "name": "Tawwab",
        "slug": "tawwab",
        "gender": "Male",
        "aliases": ["Tawab", "Tawaab"],
        "ar": "تَوَّاب",
        "tr": "tawwāb",
        "root": "ت و ب",
        "roottr": "t-w-b",
        "morph": "Intensive adjective (faʿʿāl pattern) from the root ت و ب, used as a divine name and a personal name.",
        "short": "The ever-accepting of repentance; a divine name in the Qur'an",
        "primary": (
            "Tawwab (التواب) is a divine name meaning “the One who repeatedly accepts repentance”. "
            "It occurs in the Qur'an in verses including 2:37, 2:54, 2:128, 2:160, 9:104, 9:118, "
            "49:12 and 110:3. The related noun tawbah means repentance, and Tawwab is used as a male "
            "given name."
        ),
        "literal": "Ever-accepting of repentance",
        "explain": (
            "The root ت و ب carries the sense of returning and repenting. The intensive form تواب is "
            "used for God as the frequent acceptor of repentance. As a personal name it is an "
            "attribute-name; the record does not claim the bearer possesses the divine attribute."
        ),
        "sem": "Repentance and divine acceptance",
        "concepts": ["repentance", "tawbah", "divine mercy"],
        "quran": True,
        "qstatus": "divine_name_attested",
        "qnote": "التواب occurs as a divine name in several Qur'anic verses, including 2:37, 9:104 and 110:3.",
        "rel_assoc": "Islamic monotheism; divine attribute (ṣifah)",
        "rel_status": "A divine name used as a personal name in Muslim communities.",
        "rel_explain": "The Qur'an uses التواب for God as the acceptor of repentance. The personal name is an attribute-name and does not attribute divinity to the bearer.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "No verified source establishes Tawwab as the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with the Qur'anic theme of repentance and God's acceptance of it.",
        "cult_interp": "Families may value the theme of repentance and mercy; this is a naming preference, not a claim about the bearer.",
        "hist_status": "documented_in_Quran_and_classical_lexicography",
        "hist_note": "The divine name is attested across the Qur'an; the root ت و ب is treated in the classical Arabic lexicons.",
        "trs": {
            "urdu": ("تواب", "توبہ قبول کرنے والا؛ اللہ کا صفاتی نام"),
            "persian": ("تواب", "توبه‌پذیر؛ نام صفتی خداوند"),
            "hindi": ("तव्वाब", "पश्चात्ताप स्वीकार करने वाला; ईश्वर का गुणवाचक नाम"),
            "pashto": ("تواب", "د توبې قبلوونکی؛ د الله صفتي نوم"),
            "arabic": ("تَوَّاب", "الذي يقبل توبة عباده، اسم من أسماء الله"),
        },
        "pron": "taw-WAB",
        "mispron": "TAW-wab",
        "evidence": [
            ("Qur'an 2:37 and 9:104", "https://quran.com/2/37", "The divine name al-Tawwāb in Qur'anic context.", "The verses use the name for God, not as a human personal name."),
            ("Lane, An Arabic-English Lexicon (1863), root ت و ب", "", "Lexical senses of tawbah and tawwāb.", "Classical dictionary senses are broader than the conventional name gloss."),
        ],
        "claims": [
            ("Al-Tawwab is a Qur'anic divine name", "https://quran.com/2/37", "primary_text_cited_not_rechecked_in_this_pass"),
            ("Tawwab is used as a male given name", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["divine_attribute_used_as_personal_name", "not_a_Quranic_person_name"],
        "selection": "Included because a Qur'anic divine name in common Muslim use is absent from the dataset.",
    },
    {
        "name": "Warith",
        "slug": "warith",
        "gender": "Male",
        "aliases": ["Waris", "Wareth"],
        "ar": "وَارِث",
        "tr": "wārith",
        "root": "و ر ث",
        "roottr": "w-r-th",
        "morph": "Active participle of waritha (“to inherit”), used as a divine name and a personal name.",
        "short": "Heir; the Inheritor — a divine name in the Qur'an",
        "primary": (
            "Warith (الوارث) is a divine name meaning “the Inheritor”, the One who remains after "
            "creation and inherits all things. It occurs in Qur'an 15:23 (“and We are the "
            "inheritors”) and in the phrase “the best of inheritors” in 21:89. In ordinary Arabic "
            "wārith means an heir, and the name is used for boys."
        ),
        "literal": "Heir; inheritor",
        "explain": (
            "The root و ر ث gives the verb waritha (“to inherit”) and the active participle wārith "
            "(“heir”). The divine name الوارث is interpreted as God's permanence after the passing "
            "of creation. The personal name is an attribute-name and does not describe the bearer "
            "literally."
        ),
        "sem": "Inheritance and divine permanence",
        "concepts": ["heir", "inheritance", "divine permanence"],
        "quran": True,
        "qstatus": "divine_name_attested",
        "qnote": "الوارث occurs as a divine name in Qur'an 15:23 and in the phrase “the best of inheritors” in 21:89.",
        "rel_assoc": "Islamic monotheism; divine attribute (ṣifah)",
        "rel_status": "A divine name used as a personal name in Muslim communities.",
        "rel_explain": "The Qur'an uses الوارث for God as the One who remains and inherits all things. The personal name does not attribute divinity to the bearer.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "No verified source establishes Warith as the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with the Qur'anic theme of God's permanence and ultimate inheritance of all things.",
        "cult_interp": "Families may value the theme of enduring legacy; this is a naming preference, not a claim about the bearer.",
        "hist_status": "documented_in_Quran_and_classical_lexicography",
        "hist_note": "The divine name is attested in Qur'an 15:23 and 21:89; the root is treated in the classical lexicons.",
        "trs": {
            "urdu": ("وارث", "وارث؛ ہر چیز کا باقی رہنے والا مالک، اللہ کا صفاتی نام"),
            "persian": ("وارث", "وارث؛ باقی‌مانده مالک همه چیز، نام صفتی خداوند"),
            "hindi": ("वारिस", "उत्तराधिकारी; सबका शेष रहने वाला स्वामी, ईश्वर का गुणवाचक नाम"),
            "pashto": ("وارث", "وارث؛ د هر څه پاتې کیدونکی مالک، د الله صفتي نوم"),
            "arabic": ("وَارِث", "الباقي بعد فناء الخلق، اسم من أسماء الله"),
        },
        "pron": "WA-rith",
        "mispron": "wa-REETH",
        "evidence": [
            ("Qur'an 15:23 and 21:89", "https://quran.com/15/23", "The divine name al-Wārith in Qur'anic context.", "The verses use the name for God, not as a human personal name."),
            ("Lane, An Arabic-English Lexicon (1863), root و ر ث", "", "Lexical senses of wārith and wirātha.", "Classical dictionary senses are broader than the conventional name gloss."),
        ],
        "claims": [
            ("Al-Warith is a Qur'anic divine name", "https://quran.com/15/23", "primary_text_cited_not_rechecked_in_this_pass"),
            ("Warith is used as a male given name", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["divine_attribute_used_as_personal_name", "not_a_Quranic_person_name"],
        "selection": "Included because a Qur'anic divine name in Muslim use is absent from the dataset.",
    },
    {
        "name": "Wadud",
        "slug": "wadud",
        "gender": "Male",
        "aliases": ["Wadood", "Wadoud"],
        "ar": "وَدُود",
        "tr": "wadūd",
        "root": "و د د",
        "roottr": "w-d-d",
        "morph": "Intensive adjective (faʿūl pattern) from the root و د د, used as a divine name and a personal name.",
        "short": "Loving, affectionate; a divine name in the Qur'an",
        "primary": (
            "Wadud (الودود) is a divine name meaning “the Loving” or “the Affectionate”. It occurs "
            "in Qur'an 11:90 and 85:14. The root و د د carries the sense of love, and the name is "
            "used for boys; the feminine form Waduda is also attested as a given name."
        ),
        "literal": "Loving, affectionate",
        "explain": (
            "Arabic lexicography records wadd (“love”) and wadūd (“loving”). The Qur'anic divine "
            "name الودود describes God's love for the righteous. The name is an attribute-name; the "
            "record does not claim that a bearer embodies the divine attribute."
        ),
        "sem": "Love and divine affection",
        "concepts": ["love", "affection", "divine love"],
        "quran": True,
        "qstatus": "divine_name_attested",
        "qnote": "الودود occurs as a divine name in Qur'an 11:90 and 85:14.",
        "rel_assoc": "Islamic monotheism; divine attribute (ṣifah)",
        "rel_status": "A divine name used as a personal name in Muslim communities.",
        "rel_explain": "The Qur'an uses الودود for God as the Loving. The personal name is an attribute-name and does not attribute divinity to the bearer.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "No verified source establishes Wadud as the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with the Qur'anic description of God as loving and affectionate toward the righteous.",
        "cult_interp": "Families may value the theme of love and mercy; this is a naming preference, not a claim about the bearer.",
        "hist_status": "documented_in_Quran_and_classical_lexicography",
        "hist_note": "The divine name is attested in Qur'an 11:90 and 85:14; the root is treated in the classical lexicons.",
        "trs": {
            "urdu": ("ودود", "محبت کرنے والا؛ اللہ کا صفاتی نام"),
            "persian": ("ودود", "دوست‌دار و محبت‌کننده؛ نام صفتی خداوند"),
            "hindi": ("वदूद", "प्रेम करने वाला; ईश्वर का गुणवाचक नाम"),
            "pashto": ("ودود", "مینه کوونکی؛ د الله صفتي نوم"),
            "arabic": ("وَدُود", "المحب لعباده، اسم من أسماء الله"),
        },
        "pron": "wa-DOOD",
        "mispron": "WA-dud",
        "evidence": [
            ("Qur'an 11:90 and 85:14", "https://quran.com/11/90", "The divine name al-Wadūd in Qur'anic context.", "The verses use the name for God, not as a human personal name."),
            ("Lane, An Arabic-English Lexicon (1863), root و د د", "", "Lexical senses of wadd and wadūd.", "Classical dictionary senses are broader than the conventional name gloss."),
        ],
        "claims": [
            ("Al-Wadud is a Qur'anic divine name", "https://quran.com/11/90", "primary_text_cited_not_rechecked_in_this_pass"),
            ("Wadud is used as a male given name", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["divine_attribute_used_as_personal_name", "not_a_Quranic_person_name"],
        "selection": "Included because a Qur'anic divine name in Muslim use is absent from the dataset.",
    },
    {
        "name": "Afuw",
        "slug": "afuw",
        "gender": "Male",
        "aliases": ["Afu", "Afoow"],
        "ar": "عَفُوّ",
        "tr": "ʿafuww",
        "root": "ع ف و",
        "roottr": "ʿ-f-w",
        "morph": "Intensive adjective (faʿūl pattern) from the root ع ف و, used as a divine name and a personal name.",
        "short": "Pardoning, forgiving; a divine name in the Qur'an",
        "primary": (
            "Afuw (العفو) is a divine name meaning “the Pardoner” or “the One who effaces faults”. "
            "It occurs in the Qur'an in verses including 4:99 and 4:149. The root ع ف و carries "
            "senses of pardon, effacement and abundance; the name is used, though less commonly, as "
            "a male given name."
        ),
        "literal": "Pardoning; one who effaces faults",
        "explain": (
            "Classical lexicography records ʿafw as pardon and the effacing of a fault. The divine "
            "name العفو is distinct from the more general غفور (“forgiving”). The record treats "
            "Afuw as an attribute-name and does not assert a separate “spiritual” meaning."
        ),
        "sem": "Pardon and forgiveness",
        "concepts": ["pardon", "forgiveness", "effacement of faults"],
        "quran": True,
        "qstatus": "divine_name_attested",
        "qnote": "العفو occurs as a divine name in Qur'an 4:99 and 4:149.",
        "rel_assoc": "Islamic monotheism; divine attribute (ṣifah)",
        "rel_status": "A divine name used, less commonly, as a personal name in Muslim communities.",
        "rel_explain": "The Qur'an uses العفو for God as the Pardoner. The personal name is an attribute-name and does not attribute divinity to the bearer.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "No verified source establishes Afuw as the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with the Qur'anic theme of God's pardon and the effacement of faults.",
        "cult_interp": "Families may value the theme of forgiveness; this is a naming preference, not a claim about the bearer.",
        "hist_status": "documented_in_Quran_and_classical_lexicography",
        "hist_note": "The divine name is attested in Qur'an 4:99 and 4:149; the root is treated in the classical lexicons.",
        "trs": {
            "urdu": ("عفو", "معاف کرنے والا؛ اللہ کا صفاتی نام"),
            "persian": ("عفو", "بخشنده و درگذرنده؛ نام صفتی خداوند"),
            "hindi": ("अफ़ू", "क्षमा करने वाला; ईश्वर का गुणवाचक नाम"),
            "pashto": ("عفو", "بخښونکی؛ د الله صفتي نوم"),
            "arabic": ("عَفُوّ", "الكثير العفو عن عباده، اسم من أسماء الله"),
        },
        "pron": "a-FOOW",
        "mispron": "AF-oo",
        "evidence": [
            ("Qur'an 4:99 and 4:149", "https://quran.com/4/99", "The divine name al-ʿAfuww in Qur'anic context.", "The verses use the name for God, not as a human personal name."),
            ("Lane, An Arabic-English Lexicon (1863), root ع ف و", "", "Lexical senses of ʿafw and ʿafuww.", "Classical dictionary senses are broader than the conventional name gloss."),
        ],
        "claims": [
            ("Al-Afuw is a Qur'anic divine name", "https://quran.com/4/99", "primary_text_cited_not_rechecked_in_this_pass"),
            ("Afuw is used as a male given name", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["divine_attribute_used_as_personal_name", "not_a_Quranic_person_name"],
        "selection": "Included because a Qur'anic divine name is absent from the dataset, with a note that personal-name use is less common.",
    },
    {
        "name": "Subhan",
        "slug": "subhan",
        "gender": "Male",
        "aliases": ["Subhaan"],
        "ar": "سُبْحَان",
        "tr": "subḥān",
        "root": "س ب ح",
        "roottr": "s-b-ḥ",
        "morph": "Verbal noun from the root س ب ح, used in the formula subḥāna Allāh and as a personal name.",
        "short": "Glory or exaltation, from the formula subḥān Allāh",
        "primary": (
            "Subhan is the Arabic word for glory, praise or exaltation, best known from the formula "
            "subḥāna Allāh (“Glory be to God”). The form occurs frequently in the Qur'an, for "
            "example in 2:116, 17:1 and 36:36. It is widely used as a male given name in South and "
            "Central Asia, although the Qur'an does not use it as a person's name."
        ),
        "literal": "Glory, praise, exaltation",
        "explain": (
            "The word is a verbal noun from the root س ب ح in the sense of declaring God free of "
            "imperfections. Qur'anic usage is liturgical and doxological, not onomastic. The "
            "personal name is a South Asian Muslim convention derived from the formula."
        ),
        "sem": "Glorification and divine transcendence",
        "concepts": ["tasbih", "glorification", "divine transcendence"],
        "quran": False,
        "qstatus": "lexical_occurrence_only",
        "qnote": "The word سبحان occurs repeatedly in the Qur'an (e.g., 2:116, 17:1, 36:36), but it is a formula of glorification, not a Qur'anic personal name.",
        "rel_assoc": "Islamic devotional language",
        "rel_status": "A devotional formula word used as a personal name; not a divine name in the strict list.",
        "rel_explain": "Subhan belongs to the vocabulary of tasbīḥ (glorification). Its use as a name is a cultural convention; the Qur'an does not use it as a person's name.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "No verified source establishes Subhan as the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with the daily formula subḥāna Allāh and the wider practice of tasbīḥ.",
        "cult_interp": "Families may value the theme of glorifying God; this is a naming preference, not a claim about the bearer.",
        "hist_status": "documented_in_Quran_and_classical_lexicography",
        "hist_note": "The word occurs throughout the Qur'an as a formula of glorification; its use as a personal name is a later cultural development.",
        "trs": {
            "urdu": ("سبحان", "پاکی اور تسبیح؛ 'سبحان اللہ' کا لفظ"),
            "persian": ("سبحان", "پاکی و تنزیه؛ واژه «سبحان الله»"),
            "hindi": ("सुभान", "पवित्रता और महिमा; 'सुभान अल्लाह' का शब्द"),
            "pashto": ("سبحان", "پاکوالی او تسبیح؛ د 'سبحان الله' کلمه"),
            "arabic": ("سبحان", "كلمة تنزيه وتسبيح، وليست اسم علم في القرآن"),
        },
        "pron": "sub-HAAN",
        "mispron": "SUB-han",
        "evidence": [
            ("Qur'an 17:1 and 2:116", "https://quran.com/17/1", "Qur'anic usage of subḥān in the formula of glorification.", "The Qur'an uses the word liturgically, not as a person's name."),
            ("Lane, An Arabic-English Lexicon (1863), root س ب ح", "", "Lexical senses of sabḥ and subḥān.", "Classical dictionary senses are broader than the conventional name gloss."),
        ],
        "claims": [
            ("Subhan occurs in the Qur'an as a formula of glorification", "https://quran.com/17/1", "primary_text_cited_not_rechecked_in_this_pass"),
            ("Subhan is used as a male given name in South and Central Asia", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["liturgical_formula_not_personal_name", "not_a_Quranic_person_name"],
        "selection": "Included because the widely used name is absent from the dataset, while the record makes clear that the Qur'anic usage is liturgical rather than onomastic.",
    },
    {
        "name": "Sattar",
        "slug": "sattar",
        "gender": "Male",
        "aliases": ["Sattaar", "Satar"],
        "ar": "سَتَّار",
        "tr": "sattār",
        "root": "س ت ر",
        "roottr": "s-t-r",
        "morph": "Intensive adjective (faʿʿāl pattern) from the root س ت ر, used as a traditional divine name and a personal name.",
        "short": "Concealer of faults; a divine name in traditional Islamic lists",
        "primary": (
            "Sattar (الستار) is a divine name understood as “the Concealer” or “the One who covers "
            "faults”. It is transmitted in traditional lists of God's names rather than as a "
            "verbatim Qur'anic form. The root س ت ر means to cover or conceal, and Sattar and the "
            "compound Abd al-Sattar are common male names in South Asia and the Middle East."
        ),
        "literal": "Concealer; one who covers faults",
        "explain": (
            "The root س ت ر gives satara (“to cover”) and sitr (“covering, concealment”). Traditional "
            "lists of the divine names include الستار, and a well-known report says that God is "
            "“Sattīr” (concealing). Because the form is not verbatim in the Qur'an, the record labels "
            "it as a traditional divine name rather than a Qur'anic one."
        ),
        "mconf": "MEDIUM",
        "sem": "Concealment and protection of faults",
        "concepts": ["concealment", "covering faults", "privacy"],
        "quran": False,
        "qstatus": "traditional_divine_name_not_verbatim_in_Quran",
        "qnote": "The divine name الستار is transmitted in traditional lists and reports; it is not attested verbatim in the Qur'an.",
        "rel_assoc": "Islamic monotheism; traditional divine name",
        "rel_status": "A traditional divine name used as a personal name.",
        "rel_explain": "The concept of God concealing faults is established in reports; the specific name form is traditional rather than Qur'anic. Using it as a personal name does not attribute divinity to the bearer.",
        "hadith": ("listed_only", "A report in the Sunan tradition describes God as “Sattīr” (concealing); the specific wording and grading are not independently rechecked in this pass."),
        "prophetic": ("not_verified", "No verified source establishes Sattar as the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with the Islamic value of concealing people's faults rather than publicizing them.",
        "cult_interp": "Families may value the theme of discretion and protection; this is a naming preference, not a claim about the bearer.",
        "hist_status": "documented_in_classical_lexicography_and_traditional_name_lists",
        "hist_note": "The root is treated in the classical lexicons, and the name appears in traditional lists of divine names and in reports about God concealing faults.",
        "trs": {
            "urdu": ("ستار", "پردہ پوش؛ عیبوں کو چھپانے والا، روایتی صفاتی نام"),
            "persian": ("ستار", "پوشنده؛ پرده‌پوش عیوب، نام صفتی در فهرست‌های سنتی"),
            "hindi": ("सत्तार", "पर्दा करने वाला; दोष छिपाने वाला, पारंपरिक गुणवाचक नाम"),
            "pashto": ("ستار", "ستر کوونکی؛ د عیبونو پټوونکی، په روایتي لړلیکو کې صفتي نوم"),
            "arabic": ("سَتَّار", "الذي يستر عيوب عباده، اسم في قوائم الأسماء الحسنى التقليدية"),
        },
        "pron": "sat-TAAR",
        "mispron": "SAT-ar",
        "evidence": [
            ("Sunan Abī Dāwūd, Kitāb al-Adab", "https://sunnah.com/abudawud", "Report describing God as “Sattīr” (concealing).", "The specific wording and grading are not independently rechecked in this pass."),
            ("Lane, An Arabic-English Lexicon (1863), root س ت ر", "", "Lexical senses of satara and sitr: covering and concealment.", "Classical dictionary senses do not by themselves establish the name's use."),
        ],
        "claims": [
            ("Al-Sattar is transmitted as a divine name in traditional lists", "Sunan Abī Dāwūd", "traditional_source_listed_not_rechecked"),
            ("The root س ت ر means to cover or conceal", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["divine_attribute_used_as_personal_name", "not_verbatim_Quranic", "hadith_grading_not_rechecked"],
        "selection": "Included because a widely used divine name is absent from the dataset, with an explicit note that it is traditional rather than verbatim Qur'anic.",
    },
]

DATA += [
    {
        "name": "Shuja",
        "slug": "shuja",
        "gender": "Male",
        "aliases": ["Shujaa", "Shujah"],
        "ar": "شُجَاع",
        "tr": "shujāʿ",
        "root": "ش ج ع",
        "roottr": "sh-j-ʿ",
        "morph": "Arabic adjective/noun (faʿāl pattern); used descriptively as a personal name.",
        "short": "Brave or courageous",
        "primary": (
            "Shuja (شجاع) is an Arabic adjective and noun meaning “brave” or “courageous”. It is "
            "used as a male given name and is borne by early Islamic figures, including Shuja' ibn "
            "Wahb, a companion of the Prophet."
        ),
        "literal": "Brave, courageous",
        "explain": (
            "The root ش ج ع gives shujāʿah (“courage”) and shujāʿ (“brave”). The name is a "
            "descriptive adjective used onomastically; it is not a Qur'anic term or a divine name."
        ),
        "sem": "Courage and bravery",
        "concepts": ["courage", "bravery", "steadfastness"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Shuja is not attested in the Qur'an as a personal name or as a Qur'anic term.",
        "rel_assoc": "Arabic and Muslim-cultural naming usage",
        "rel_status": "A descriptive Arabic name, not a divine name or a Qur'anic term.",
        "rel_explain": "The name is an ordinary Arabic adjective used for a person. Its religious association comes only from Muslim bearers such as Shuja' ibn Wahb, not from scripture.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "No verified source establishes Shuja as the name of a prophet."),
        "companion": ("verified", "Shuja' ibn Wahb is recorded among the Companions in classical biographical literature."),
        "cult_note": "The name is associated with courage and with early Muslim figures who bore it.",
        "cult_interp": "Families may value the quality of courage; this is a naming preference, not a prediction about the bearer.",
        "hist_note": "Classical biographical works record Shuja' ibn Wahb among the Companions; the lexical sense is treated in the Arabic dictionaries.",
        "trs": {
            "urdu": ("شجاع", "بہادر، دلیر"),
            "persian": ("شجاع", "دلیر و شجاع"),
            "hindi": ("शुजा", "बहादुर, साहसी"),
            "pashto": ("شجاع", "زړور، ننګیالی"),
            "arabic": ("شجاع", "الجريء المقدام"),
        },
        "pron": "shu-JAA",
        "mispron": "SHOO-ja",
        "evidence": [
            ("Ibn Ḥajar, al-Iṣābah fī Tamyīz al-Ṣaḥābah", "", "Biographical entry for Shuja' ibn Wahb among the Companions.", "Classical biographical reports are not independently rechecked in this pass."),
            ("Lane, An Arabic-English Lexicon (1863), root ش ج ع", "", "Lexical senses of shujāʿ and shujāʿah.", "Classical dictionary senses are broader than the conventional name gloss."),
        ],
        "claims": [
            ("Shuja' means brave or courageous in Arabic", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
            ("Shuja' ibn Wahb is recorded among the Companions", "Ibn Ḥajar, al-Iṣābah", "classical_source_listed_not_rechecked"),
        ],
        "flags": ["descriptive_name_not_Quranic"],
        "selection": "Included because a common Arabic virtue name with a Companion bearer is absent from the dataset.",
    },
    {
        "name": "Thuwayba",
        "slug": "thuwayba",
        "gender": "Female",
        "gconf": "MEDIUM",
        "aliases": ["Thuwaiba", "Suwayba", "Suwaiba", "Thuwaybah"],
        "ar": "ثُوَيْبَة",
        "tr": "thuwaybah",
        "root": "ث و ب",
        "roottr": "th-w-b",
        "morph": "Feminine diminutive proper name; classical lexicography connects the pattern with the root ث و ب, but the name is transmitted as a proper name.",
        "short": "Name of Thuwayba al-Aslamiyya, the Prophet's first wet nurse",
        "primary": (
            "Thuwayba (ثويبة) is a feminine personal name borne by Thuwayba al-Aslamiyya, who nursed "
            "the Prophet Muhammad in infancy before Halima al-Sa'idiyya. She was a freed enslaved "
            "woman of Abu Lahab. The name is a proper feminine name with a diminutive pattern; it is "
            "not a Qur'anic term."
        ),
        "literal": "A feminine proper name; no independent lexical gloss is asserted",
        "explain": (
            "Classical biographical sources record Thuwayba's nursing of the Prophet and her "
            "manumission. The name's morphology is a feminine diminutive, but the record does not "
            "assert a lexical meaning beyond its use as a proper name."
        ),
        "mconf": "MEDIUM",
        "sem": "Early Islamic biography",
        "concepts": ["Prophet's wet nurse", "early Madinan history", "manumission"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Thuwayba is not a Qur'anic name; she is recorded in the Sirah and hadith literature.",
        "rel_assoc": "Prophetic biography",
        "rel_status": "A historical female name from the Prophet's early life; not a Qur'anic or divine name.",
        "rel_explain": "Thuwayba is remembered as the Prophet's first wet nurse. The name's significance is biographical, not scriptural.",
        "hadith": ("listed_only", "Reports in the hadith collections mention Thuwayba's nursing of the Prophet; the specific wording and grading are not independently rechecked in this pass."),
        "prophetic": ("not_verified", "Thuwayba is not the name of a prophet."),
        "companion": ("verified", "Thuwayba al-Aslamiyya is recorded in the Sirah and hadith literature as the Prophet's first wet nurse."),
        "cult_note": "The name is associated with the Prophet's infancy and with the early Muslim community in Makkah.",
        "cult_interp": "Use of the name is commemorative; the record does not infer character from it.",
        "hist_note": "Ibn Hisham's Sirah and Ibn Sa'd's Tabaqat record her nursing the Prophet and her status.",
        "trs": {
            "urdu": ("ثویبہ", "نبی ﷺ کی پہلی رضاعی ماں ثویبہ اسلمیہ کا نام"),
            "persian": ("ثویبه", "نام ثویبه اسلمیه، نخستین دایه پیامبر"),
            "hindi": ("सुवैबा", "पैग़ंबर की पहली धाय माँ सुवैबा असलमिया का नाम"),
            "pashto": ("ثویبه", "د پیغمبر لومړنۍ شیدې ورکوونکې مور ثویبه اسلمیه"),
            "arabic": ("ثويبة", "اسم ثويبة الأسلمية، أول من أرضعت النبي صلى الله عليه وسلم"),
        },
        "pron": "thu-WAY-ba",
        "mispron": "su-WAY-ba",
        "evidence": [
            ("Ibn Hishām, al-Sīrah al-Nabawiyyah", "", "Account of Thuwayba al-Aslamiyya as the Prophet's first wet nurse.", "Classical reports are not independently rechecked in this pass."),
            ("Ṣaḥīḥ al-Bukhārī", "https://sunnah.com/bukhari", "Reports referring to Thuwayba's nursing of the Prophet.", "Collection-level citation; the specific report and grading are not rechecked here."),
        ],
        "claims": [
            ("Thuwayba al-Aslamiyya nursed the Prophet in infancy", "Ibn Hishām, al-Sīrah al-Nabawiyyah", "classical_source_listed_not_rechecked"),
            ("Thuwayba is not a Qur'anic name", "https://quran.com", "negative_claim_based_on_text_search"),
        ],
        "flags": ["historical_female_name_not_Quranic"],
        "selection": "Included because a well-documented female name from the Prophet's biography is absent from the dataset.",
    },
    {
        "name": "Sawda",
        "slug": "sawda",
        "gender": "Female",
        "aliases": ["Sawdah", "Sauda", "Saudah"],
        "ar": "سَوْدَة",
        "tr": "sawdah",
        "root": "س و د",
        "roottr": "s-w-d",
        "morph": "Feminine form of the colour adjective aswad (“black”), used as a proper name.",
        "short": "Name of Sawda bint Zam'a, a wife of the Prophet",
        "primary": (
            "Sawda (سودة) is a feminine personal name derived from the Arabic colour term aswad "
            "(“black”), with the feminine ending. It is best known as the name of Sawda bint Zam'a, "
            "whom the Prophet Muhammad married after Khadija's death. The name is pre-Islamic in use "
            "and is not a Qur'anic term."
        ),
        "literal": "Feminine form of aswad (“black”)",
        "explain": (
            "The root س و د gives aswad (“black”) and sawdāʾ (feminine). The name is a colour-derived "
            "proper name; its use does not imply a literal description of the bearer. Classical "
            "sources record Sawda bint Zam'a among the Mothers of the Believers."
        ),
        "sem": "Early Islamic biography and colour-derived naming",
        "concepts": ["Mothers of the Believers", "early Islam", "colour-derived names"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Sawda is not a Qur'anic name; Sawda bint Zam'a is recorded in the Sirah and hadith literature.",
        "rel_assoc": "Prophetic biography",
        "rel_status": "A historical female name from the Prophet's household; not a Qur'anic or divine name.",
        "rel_explain": "Sawda bint Zam'a is remembered as a wife of the Prophet. The name's significance is biographical, not scriptural.",
        "hadith": ("listed_only", "Reports in the hadith collections mention Sawda bint Zam'a; the specific wording and grading are not independently rechecked in this pass."),
        "prophetic": ("not_verified", "Sawda is not the name of a prophet."),
        "companion": ("verified", "Sawda bint Zam'a is recorded among the wives of the Prophet in the Sirah and hadith literature."),
        "cult_note": "The name is associated with the Prophet's household and the early Muslim community.",
        "cult_interp": "Use of the name is commemorative; the record does not infer character from it.",
        "hist_note": "Ibn Hisham's Sirah and Ibn Sa'd's Tabaqat record Sawda bint Zam'a among the Mothers of the Believers.",
        "trs": {
            "urdu": ("سودہ", "نبی ﷺ کی زوجہ سودہ بنت زمعہ کا نام؛ سیاہی سے ماخوذ"),
            "persian": ("سوده", "نام سوده دختر زمعه، همسر پیامبر؛ برگرفته از سیاهی"),
            "hindi": ("सौदा", "पैग़ंबर की पत्नी सौदा बिन्त ज़म'आ का नाम; श्यामता से व्युत्पन्न"),
            "pashto": ("سوده", "د پیغمبر مېرمن سوده بنت زمعه نوم؛ د تور رنګ له معنا"),
            "arabic": ("سودة", "اسم سودة بنت زمعة، زوجة النبي صلى الله عليه وسلم"),
        },
        "pron": "SAW-da",
        "mispron": "sow-da",
        "evidence": [
            ("Ibn Hishām, al-Sīrah al-Nabawiyyah", "", "Account of Sawda bint Zam'a among the Prophet's wives.", "Classical reports are not independently rechecked in this pass."),
            ("Ṣaḥīḥ al-Bukhārī", "https://sunnah.com/bukhari", "Reports referring to Sawda bint Zam'a.", "Collection-level citation; the specific report and grading are not rechecked here."),
        ],
        "claims": [
            ("Sawda bint Zam'a was a wife of the Prophet", "Ibn Hishām, al-Sīrah al-Nabawiyyah", "classical_source_listed_not_rechecked"),
            ("The name derives from the colour term aswad", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["historical_female_name_not_Quranic", "colour_derived_name"],
        "selection": "Included because a well-documented female name from the Prophet's household is absent from the dataset.",
    },
    {
        "name": "Sukayna",
        "slug": "sukayna",
        "gender": "Female",
        "aliases": ["Sukaina", "Sakina", "Sakinah"],
        "ar": "سُكَيْنَة",
        "tr": "sukaynah",
        "root": "س ك ن",
        "roottr": "s-k-n",
        "morph": "Feminine diminutive form related to sakīnah (“tranquility”), used as a personal name.",
        "short": "Tranquility; name of Sukayna bint al-Husayn",
        "primary": (
            "Sukayna (سكينة) is a feminine name meaning “tranquility” or “calm”, from the root س ك ن. "
            "The related Qur'anic word sakīnah denotes the tranquility God sends down upon believers "
            "(9:26, 48:4). The personal name is associated with Sukayna bint al-Husayn, a "
            "granddaughter of the Prophet."
        ),
        "literal": "Tranquility, calm",
        "explain": (
            "The root س ك ن gives sakana (“to be still, dwell”) and sakīnah (“tranquility”). The "
            "Qur'an uses sakīnah for the calm sent down upon believers. Sukayna is a feminine "
            "diminutive personal name; the record distinguishes the Qur'anic word from the later "
            "personal name."
        ),
        "sem": "Tranquility and early Islamic biography",
        "concepts": ["tranquility", "sakinah", "Prophet's family"],
        "quran": False,
        "qstatus": "related_word_attested",
        "qnote": "The word sakīnah occurs in Qur'an 9:26, 9:40, 48:4, 48:18 and 48:26; the personal name Sukayna is not used in the Qur'an.",
        "rel_assoc": "Qur'anic vocabulary and Prophetic family history",
        "rel_status": "A personal name related to a Qur'anic word; not a Qur'anic personal name or a divine name.",
        "rel_explain": "The Qur'anic word sakīnah denotes tranquility sent by God. The personal name Sukayna is associated with Sukayna bint al-Husayn and is not itself a Qur'anic name.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Sukayna is not the name of a prophet."),
        "companion": ("not_verified", "Sukayna bint al-Husayn belongs to a later generation and is not a Companion."),
        "cult_note": "The name is associated with tranquility and with Sukayna bint al-Husayn, a figure of the Prophet's family.",
        "cult_interp": "Families may value the sense of calm and dignity; this is a naming preference, not a claim about the bearer.",
        "hist_note": "Classical biographical literature records Sukayna bint al-Husayn; reports about her life vary in detail.",
        "trs": {
            "urdu": ("سکینہ", "سکون اور اطمینان؛ حسین بن علی کی بیٹی کا نام"),
            "persian": ("سکینه", "آرامش و طمأنینه؛ نام دختر حسین بن علی"),
            "hindi": ("सुकैना", "शांति और सुकून; हुसैन बिन अली की बेटी का नाम"),
            "pashto": ("سکینه", "ارام او ډاډ؛ د حسین بن علي لور نوم"),
            "arabic": ("سكينة", "الطمأنينة والسكون، واسم بنت الحسين"),
        },
        "pron": "su-KAY-na",
        "mispron": "soo-KAY-na",
        "evidence": [
            ("Qur'an 48:4 and 9:26", "https://quran.com/48/4", "Qur'anic usage of sakīnah (“tranquility”).", "The Qur'an uses the word, not the later personal name."),
            ("al-Dhahabī, Siyar Aʿlām al-Nubalāʾ", "", "Biographical reports about Sukayna bint al-Husayn.", "Classical reports vary in detail and are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Sakīnah is a Qur'anic word meaning tranquility", "https://quran.com/48/4", "primary_text_cited_not_rechecked_in_this_pass"),
            ("Sukayna is associated with Sukayna bint al-Husayn", "al-Dhahabī, Siyar Aʿlām al-Nubalāʾ", "classical_source_listed_not_rechecked"),
        ],
        "flags": ["Quranic_word_not_Quranic_person_name", "historical_female_name"],
        "selection": "Included because a well-known female name with a Qur'anic lexical root is absent from the dataset.",
    },
    {
        "name": "Umm Sulaym",
        "slug": "ummsulaym",
        "gender": "Female",
        "gconf": "MEDIUM",
        "aliases": ["Umm-Sulaym", "Ummsulaym"],
        "ar": "أُمُّ سُلَيْم",
        "tr": "umm sulaym",
        "root": "س ل م",
        "roottr": "s-l-m",
        "morph": "Kunya: أم (“mother of”) + سليم (a proper name); an honorific form rather than a birth name.",
        "short": "Kunya of Rumaysa bint Milhan, mother of Anas ibn Malik",
        "primary": (
            "Umm Sulaym (أم سليم) is the kunya by which Rumaysa bint Milhan, a Companion and the "
            "mother of Anas ibn Malik, is best known. She was among the early Muslim women of "
            "Madinah and is remembered in the hadith literature. The form is a kunya (“mother of "
            "Sulaym”) rather than a birth name."
        ),
        "literal": "Mother of Sulaym (a kunya)",
        "explain": (
            "A kunya is an honorific name of the form “mother of X”. Classical biographical sources "
            "record her early conversion, her marriage to Abu Talha, and her role in the household "
            "of Anas ibn Malik. The record does not treat the kunya as a Qur'anic name."
        ),
        "mconf": "MEDIUM",
        "sem": "Companions and early Madinan history",
        "concepts": ["Companions", "Anas ibn Malik", "early Madinah"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Umm Sulaym is not a Qur'anic name; she is recorded in the hadith and biographical literature.",
        "rel_assoc": "Prophetic biography and Companions",
        "rel_status": "A companion's kunya used as a personal name; not a Qur'anic or divine name.",
        "rel_explain": "The name's significance is biographical. Umm Sulaym is remembered as the mother of Anas ibn Malik and as an early Muslim woman of Madinah.",
        "hadith": ("listed_only", "Reports in the hadith collections mention Umm Sulaym; the specific wording and grading are not independently rechecked in this pass."),
        "prophetic": ("not_verified", "Umm Sulaym is not the name of a prophet."),
        "companion": ("verified", "Umm Sulaym, mother of Anas ibn Malik, is recorded among the Companions in the hadith and biographical literature."),
        "cult_note": "The name is associated with the household of the Prophet and with the early Muslim community of Madinah.",
        "cult_interp": "Use of the name is commemorative; the record does not infer character from it.",
        "hist_note": "Al-Isabah, al-Isti'ab and Siyar A'lam al-Nubala' record her biography and her connection to Anas ibn Malik.",
        "trs": {
            "urdu": ("ام سلیم", "صحابیہ ام سلیم، انس بن مالک کی والدہ کی کنیت"),
            "persian": ("ام سلیم", "کنیه ام سلیم، مادر انس بن مالک"),
            "hindi": ("उम्म सुलैम", "सहाबिया उम्म सुलैम, अनस बिन मालिक की माँ की कुन्यत"),
            "pashto": ("ام سلیم", "د صحابیې ام سلیم، د انس بن مالک مور کنیت"),
            "arabic": ("أم سليم", "كنية أم سليم، والدة أنس بن مالك"),
        },
        "pron": "oom su-LAYM",
        "mispron": "um SOO-laym",
        "evidence": [
            ("Ibn Ḥajar, al-Iṣābah fī Tamyīz al-Ṣaḥābah", "", "Biographical entry for Umm Sulaym, mother of Anas ibn Malik.", "Classical reports are not independently rechecked in this pass."),
            ("Ṣaḥīḥ Muslim", "https://sunnah.com/muslim", "Reports mentioning Umm Sulaym and her household.", "Collection-level citation; specific reports and grading are not rechecked here."),
        ],
        "claims": [
            ("Umm Sulaym was the mother of Anas ibn Malik", "Ibn Ḥajar, al-Iṣābah", "classical_source_listed_not_rechecked"),
            ("Umm Sulaym is a kunya rather than a birth name", "Ibn Ḥajar, al-Iṣābah", "classical_source_listed_not_rechecked"),
        ],
        "flags": ["kunya_not_birth_name", "companion_name_not_Quranic"],
        "selection": "Included because a famous female Companion's kunya is absent from the dataset, replacing an Ajwa candidate that collided with the existing Ajva record.",
    },
    {
        "name": "Zamzam",
        "slug": "zamzam",
        "gender": "Female",
        "gconf": "MEDIUM",
        "aliases": ["Zam Zam"],
        "ar": "زَمْزَم",
        "tr": "zamzam",
        "root": "",
        "roottr": "",
        "morph": "Proper name of the well; a reduplicative form (z-m-z-m) rather than a triliteral Arabic root.",
        "short": "The name of the well at Makkah, used as a given name",
        "primary": (
            "Zamzam is the name of the well near the Ka'bah in Makkah, associated in Islamic "
            "tradition with Hajar and Isma'il. The name is used as a feminine given name, especially "
            "in South Asia and the Arab world. It is a well name rather than a Qur'anic personal "
            "name."
        ),
        "literal": "The name of the well at Makkah",
        "explain": (
            "The word is a proper name of the well and is traditionally treated as reduplicative "
            "(z-m-z-m) rather than as a triliteral Arabic root. The well's history is recorded in "
            "the Sirah and hadith literature; the Qur'an does not name it explicitly."
        ),
        "mconf": "MEDIUM",
        "sem": "Makkan sacred geography",
        "concepts": ["Zamzam well", "Makkah", "Hajar and Isma'il"],
        "quran": False,
        "qstatus": "not_named_in_Quran",
        "qnote": "The Zamzam well is not named explicitly in the Qur'an; its history is recorded in the Sirah and hadith literature.",
        "rel_assoc": "Islamic sacred geography and pilgrimage",
        "rel_status": "A well name used as a personal name; not a Qur'anic or divine name.",
        "rel_explain": "Zamzam is the name of the well in Makkah and is associated with pilgrimage. Its religious significance is historical and ritual, not scriptural onomastics.",
        "hadith": ("listed_only", "Reports in the hadith collections mention Zamzam water and drinking from the well; grading is not independently rechecked in this pass."),
        "prophetic": ("not_verified", "Zamzam is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with the well of Zamzam, the pilgrimage, and the story of Hajar and Isma'il.",
        "cult_interp": "Families may value the connection to Makkah and pilgrimage; this is a naming preference, not a claim about the bearer.",
        "hist_note": "The Sirah and hadith literature record the well's history and its connection with Hajar and Isma'il.",
        "trs": {
            "urdu": ("زمزم", "مکہ کا مشہور کنواں؛ نام کے طور پر بھی مستعمل"),
            "persian": ("زمزم", "چاه مشهور مکه؛ به‌عنوان نام نیز به کار می‌رود"),
            "hindi": ("ज़मज़म", "मक्का का प्रसिद्ध कुआँ; नाम के रूप में भी प्रयुक्त"),
            "pashto": ("زمزم", "د مکې مشهور څاه؛ د نوم په توګه هم کارول کیږي"),
            "arabic": ("زمزم", "بئر مكة المشهورة، وتُستخدم اسماً شخصياً"),
        },
        "pron": "ZAM-zam",
        "mispron": "zam-ZAM",
        "evidence": [
            ("Ṣaḥīḥ al-Bukhārī, Kitāb al-Ḥajj", "https://sunnah.com/bukhari", "Reports about Zamzam water and the well in Makkah.", "Collection-level citation; the specific reports and grading are not rechecked here."),
            ("Ibn Hishām, al-Sīrah al-Nabawiyyah", "", "Account of Hajar, Isma'il and the Zamzam well.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Zamzam is the name of the well at Makkah", "Ibn Hishām, al-Sīrah al-Nabawiyyah", "classical_source_listed_not_rechecked"),
            ("Zamzam is not named explicitly in the Qur'an", "https://quran.com", "negative_claim_based_on_text_search"),
        ],
        "flags": ["well_name_not_Quranic_person_name"],
        "selection": "Included because a common female name tied to Makkah is absent from the dataset.",
    },
    {
        "name": "Abu Dharr",
        "slug": "abudharr",
        "gender": "Male",
        "gconf": "MEDIUM",
        "aliases": ["Abu-Dharr", "Abudharr"],
        "ar": "أَبُو ذَرّ",
        "tr": "abū dharr",
        "root": "",
        "roottr": "",
        "morph": "Kunya: أبو (“father of”) + ذر (proper name); an honorific form rather than a birth name.",
        "short": "Kunya of the companion Abu Dharr al-Ghifari",
        "primary": (
            "Abu Dharr (أبو ذر) is the kunya by which the companion Jundub ibn Junada al-Ghifari is "
            "best known. He was an early convert renowned for asceticism and for his frank speech. "
            "The form is a kunya (“father of Dharr”) rather than a birth name, and the element Dharr "
            "is a proper name."
        ),
        "literal": "Father of Dharr (a kunya)",
        "explain": (
            "A kunya is an honorific name of the form “father of X”. Classical biographical sources "
            "record Abu Dharr's early conversion, his emigration, and his piety. The record does not "
            "treat the kunya as a Qur'anic name or a divine attribute."
        ),
        "mconf": "MEDIUM",
        "sem": "Companions and early asceticism",
        "concepts": ["Companions", "asceticism", "early Islam"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Abu Dharr is not a Qur'anic name; the companion is recorded in the hadith and biographical literature.",
        "rel_assoc": "Prophetic biography and Companions",
        "rel_status": "A companion's kunya used as a personal name; not a Qur'anic or divine name.",
        "rel_explain": "The name's significance is biographical. Abu Dharr is remembered for his early conversion and asceticism, not because the Qur'an names him.",
        "hadith": ("listed_only", "Reports in the hadith collections mention Abu Dharr's conversion, piety and speech; grading is not independently rechecked in this pass."),
        "prophetic": ("not_verified", "Abu Dharr is not the name of a prophet."),
        "companion": ("verified", "Abu Dharr al-Ghifari is recorded among the Companions in the Sirah, hadith and biographical literature."),
        "cult_note": "The name is associated with one of the earliest Companions and with the value of asceticism.",
        "cult_interp": "Use of the name is commemorative; the record does not infer character from it.",
        "hist_note": "Al-Isabah, al-Isti'ab and Siyar A'lam al-Nubala' record his biography and reports about his asceticism.",
        "trs": {
            "urdu": ("ابو ذر", "صحابی ابو ذر غفاری کی کنیت"),
            "persian": ("ابوذر", "کنیه ابوذر غفاری، صحابی پیامبر"),
            "hindi": ("अबू ज़र", "सहाबी अबू ज़र ग़िफ़ारी की कुन्यत"),
            "pashto": ("ابو ذر", "د صحابي ابو ذر غفاري کنیت"),
            "arabic": ("أبو ذر", "كنية الصحابي جندب بن جنادة الغفاري"),
        },
        "pron": "a-boo DHARR",
        "mispron": "aboo ZAR",
        "evidence": [
            ("Ibn Ḥajar, al-Iṣābah fī Tamyīz al-Ṣaḥābah", "", "Biographical entry for Abu Dharr al-Ghifari.", "Classical reports are not independently rechecked in this pass."),
            ("Ṣaḥīḥ Muslim", "https://sunnah.com/muslim", "Reports about Abu Dharr's conversion and conduct.", "Collection-level citation; specific reports and grading are not rechecked here."),
        ],
        "claims": [
            ("Abu Dharr al-Ghifari is recorded among the Companions", "Ibn Ḥajar, al-Iṣābah", "classical_source_listed_not_rechecked"),
            ("Abu Dharr is a kunya rather than a birth name", "Ibn Ḥajar, al-Iṣābah", "classical_source_listed_not_rechecked"),
        ],
        "flags": ["kunya_not_birth_name", "companion_name_not_Quranic"],
        "selection": "Included because a famous Companion's kunya is absent from the dataset, with a note that it is not a birth name.",
    },
    {
        "name": "Hanbal",
        "slug": "hanbal",
        "gender": "Male",
        "gconf": "MEDIUM",
        "aliases": ["Hanbel"],
        "ar": "حَنْبَل",
        "tr": "ḥanbal",
        "root": "",
        "roottr": "",
        "morph": "Arabic proper name; no productive root derivation is asserted.",
        "short": "Name of the grandfather of Imam Ahmad ibn Hanbal",
        "primary": (
            "Hanbal (حنبل) is an Arabic personal name best known as the name of Hanbal ibn Hilal, "
            "the grandfather of Imam Ahmad ibn Hanbal, the eponym of the Hanbali school of law. The name "
            "is used, though uncommonly, as a male given name. It is not a Qur'anic term."
        ),
        "literal": "An Arabic proper name; no independent lexical gloss is asserted",
        "explain": (
            "Classical biographical sources record Hanbal ibn Hilal as Ahmad ibn Hanbal's grandfather. "
            "The name is a proper name; this record does not assert a lexical meaning or an Arabic "
            "root derivation beyond its use."
        ),
        "mconf": "MEDIUM",
        "sem": "Islamic scholarship and family names",
        "concepts": ["Hanbali school", "Imam Ahmad ibn Hanbal", "classical scholarship"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Hanbal is not a Qur'anic name; it is a personal name recorded in biographical sources for Imam Ahmad ibn Hanbal.",
        "rel_assoc": "Islamic scholarship",
        "rel_status": "A historical personal name, not a Qur'anic or divine name.",
        "rel_explain": "The name's significance is biographical, through Imam Ahmad ibn Hanbal. The record does not claim a religious virtue for the name itself.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Hanbal is not the name of a prophet."),
        "companion": ("not_verified", "Hanbal ibn Hilal is not recorded as a Companion."),
        "cult_note": "The name is associated with the family of Imam Ahmad ibn Hanbal and the Hanbali legal school.",
        "cult_interp": "Use of the name may be commemorative of scholarly heritage; the record does not infer character from it.",
        "hist_note": "Classical biographical sources for Imam Ahmad ibn Hanbal name his grandfather as Hanbal ibn Hilal.",
        "trs": {
            "urdu": ("حنبل", "امام احمد بن حنبل کے دادا کا نام"),
            "persian": ("حنبل", "نام پدربزرگ امام احمد بن حنبل"),
            "hindi": ("हनबल", "इमाम अहमद बिन हनबल के दादा का नाम"),
            "pashto": ("حنبل", "د امام احمد بن حنبل د نیکه نوم"),
            "arabic": ("حنبل", "اسم جد الإمام أحمد بن حنبل"),
        },
        "pron": "HAN-bal",
        "mispron": "han-BAL",
        "evidence": [
            ("al-Dhahabī, Siyar Aʿlām al-Nubalāʾ", "", "Biography of Imam Ahmad ibn Hanbal, naming his grandfather Hanbal ibn Hilal.", "Classical reports are not independently rechecked in this pass."),
            ("Ibn Abī Yaʿlā, Ṭabaqāt al-Ḥanābilah", "", "Hanbali biographical literature on the family of Imam Ahmad.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Hanbal ibn Hilal was the grandfather of Imam Ahmad ibn Hanbal", "al-Dhahabī, Siyar Aʿlām al-Nubalāʾ", "classical_source_listed_not_rechecked"),
            ("Hanbal is not a Qur'anic name", "https://quran.com", "negative_claim_based_on_text_search"),
        ],
        "flags": ["historical_name_not_Quranic", "lexical_meaning_not_asserted"],
        "selection": "Included because a historically significant name in Islamic scholarship is absent from the dataset.",
    },
    {
        "name": "Shamsuddin",
        "slug": "shamsuddin",
        "gender": "Male",
        "aliases": ["Shamsudeen", "Shamsudheen", "Shams-Ud-Din"],
        "ar": "شَمْسُ الدِّين",
        "tr": "shams al-dīn",
        "root": "ش م س / د ي ن",
        "roottr": "sh-m-s / d-y-n",
        "morph": "Compound genitive: شمس (“sun”) + الدين (“the religion”).",
        "short": "Sun of the religion",
        "primary": (
            "Shamsuddin (شمس الدين) is a compound honorific name meaning “sun of the religion”. It "
            "is formed from shams (“sun”) and al-din (“the religion”) and was borne by numerous "
            "classical scholars, including the historian Shams al-Din al-Dhahabi (d. 748/1348). The "
            "name is not Qur'anic; it is a historical Muslim honorific."
        ),
        "literal": "Sun of the religion",
        "explain": (
            "The compound joins two Arabic nouns in a genitive construction. Names of the form X "
            "al-Din were widespread among scholars and rulers from the medieval period. The record "
            "describes the construction and its historical bearers; it does not claim a Qur'anic "
            "origin."
        ),
        "sem": "Islamic honorific names and scholarship",
        "concepts": ["honorific names", "classical scholarship", "al-Din compounds"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Shamsuddin is a historical compound honorific, not a Qur'anic name.",
        "rel_assoc": "Islamic scholarly and honorific naming",
        "rel_status": "A historical honorific name, not a Qur'anic or divine name.",
        "rel_explain": "The name combines two ordinary Arabic words and was used as an honorific by scholars. It carries no scriptural status as a name.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Shamsuddin is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with the scholarly and administrative culture of the medieval Muslim world.",
        "cult_interp": "Families may value the imagery of light and learning; this is a naming preference, not a claim about the bearer.",
        "hist_note": "Shams al-Din al-Dhahabi (d. 748/1348) and other scholars bore the name; biographical dictionaries record it widely.",
        "trs": {
            "urdu": ("شمس الدین", "دین کا سورج"),
            "persian": ("شمس‌الدین", "خورشید دین"),
            "hindi": ("शम्सुद्दीन", "धर्म का सूर्य"),
            "pashto": ("شمس الدین", "د دین لمر"),
            "arabic": ("شمس الدين", "شمس الدين، اسم مركب بمعنى شمس الدين"),
        },
        "pron": "shams-ud-DEEN",
        "mispron": "shams-u-DEEN",
        "evidence": [
            ("Ibn Ḥajar, al-Durar al-Kāminah", "", "Biographical dictionary covering Shams al-Din al-Dhahabi.", "Classical reports are not independently rechecked in this pass."),
            ("Shams al-Dīn al-Dhahabī, Siyar Aʿlām al-Nubalāʾ", "", "The historian's own major work, whose author carries the name.", "This citation establishes the bearer, not a lexical meaning."),
        ],
        "claims": [
            ("Shams al-Din al-Dhahabi bore the name", "Ibn Ḥajar, al-Durar al-Kāminah", "classical_source_listed_not_rechecked"),
            ("Shamsuddin is a compound honorific meaning sun of the religion", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["compound_honorific_not_Quranic"],
        "selection": "Included because a widely used historical honorific is absent from the dataset.",
    },
    {
        "name": "Fakhruddin",
        "slug": "fakhruddin",
        "gender": "Male",
        "aliases": ["Fakhrudeen", "Fakhr-Ud-Din"],
        "ar": "فَخْرُ الدِّين",
        "tr": "fakhr al-dīn",
        "root": "ف خ ر / د ي ن",
        "roottr": "f-kh-r / d-y-n",
        "morph": "Compound genitive: فخر (“pride”) + الدين (“the religion”).",
        "short": "Pride of the religion",
        "primary": (
            "Fakhruddin (فخر الدين) is a compound honorific name meaning “pride of the religion”. "
            "Its most famous bearer is Fakhr al-Din al-Razi (d. 606/1209), the theologian and Qur'an "
            "commentator. The name is not Qur'anic; it is a historical Muslim honorific."
        ),
        "literal": "Pride of the religion",
        "explain": (
            "The compound joins fakhr (“pride”) with al-din (“the religion”). It was used as an "
            "honorific by scholars and officials. The record describes the construction and its "
            "bearers; it makes no scriptural claim for the name."
        ),
        "sem": "Islamic honorific names and scholarship",
        "concepts": ["honorific names", "theology", "Qur'an commentary"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Fakhruddin is a historical compound honorific, not a Qur'anic name.",
        "rel_assoc": "Islamic scholarly and honorific naming",
        "rel_status": "A historical honorific name, not a Qur'anic or divine name.",
        "rel_explain": "The name combines two ordinary Arabic words and was used as an honorific. Its association with Fakhr al-Din al-Razi is historical, not scriptural.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Fakhruddin is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with Fakhr al-Din al-Razi and the tradition of Islamic theology and Qur'an commentary.",
        "cult_interp": "Families may value the association with scholarship and religious learning; this is a naming preference.",
        "hist_note": "Fakhr al-Din al-Razi (d. 606/1209) is the best-known bearer; biographical sources also record others.",
        "trs": {
            "urdu": ("فخر الدین", "دین کا فخر"),
            "persian": ("فخرالدین", "افتخار دین"),
            "hindi": ("फ़ख़रुद्दीन", "धर्म का गौरव"),
            "pashto": ("فخر الدین", "د دین ویاړ"),
            "arabic": ("فخر الدين", "فخر الدين، اسم مركب بمعنى فخر الدين"),
        },
        "pron": "fakhr-ud-DEEN",
        "mispron": "fa-khur-DEEN",
        "evidence": [
            ("al-Subkī, Ṭabaqāt al-Shāfiʿiyyah al-Kubrā", "", "Biographical entry for Fakhr al-Din al-Razi.", "Classical reports are not independently rechecked in this pass."),
            ("Ibn Khallikān, Wafayāt al-Aʿyān", "", "Biographical notices for scholars bearing the name.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Fakhr al-Din al-Razi bore the name", "al-Subkī, Ṭabaqāt al-Shāfiʿiyyah al-Kubrā", "classical_source_listed_not_rechecked"),
            ("Fakhruddin is a compound honorific meaning pride of the religion", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["compound_honorific_not_Quranic"],
        "selection": "Included because a widely used historical honorific is absent from the dataset.",
    },
]

DATA += [
    {
        "name": "Imaduddin",
        "slug": "imaduddin",
        "gender": "Male",
        "aliases": ["Imadudeen", "Emaduddin"],
        "ar": "عِمَادُ الدِّين",
        "tr": "ʿimād al-dīn",
        "root": "ع م د / د ي ن",
        "roottr": "ʿ-m-d / d-y-n",
        "morph": "Compound genitive: عماد (“pillar, support”) + الدين (“the religion”).",
        "short": "Pillar of the religion",
        "primary": (
            "Imaduddin (عماد الدين) is a compound honorific name meaning “pillar of the religion”. "
            "It was borne by Imad al-Din Zengi (d. 541/1146), the Zengid ruler whose campaigns "
            "preceded Salah al-Din's. The name is not Qur'anic; it is a historical Muslim honorific."
        ),
        "literal": "Pillar of the religion",
        "explain": (
            "The compound joins ʿimād (“pillar, support”) with al-din (“the religion”). It belongs "
            "to the same medieval honorific pattern as other X al-Din names. The record describes "
            "the construction and its historical bearer without claiming a scriptural origin."
        ),
        "sem": "Islamic honorific names and rule",
        "concepts": ["honorific names", "Zengid dynasty", "medieval Islamic history"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Imaduddin is a historical compound honorific, not a Qur'anic name.",
        "rel_assoc": "Islamic historical and honorific naming",
        "rel_status": "A historical honorific name, not a Qur'anic or divine name.",
        "rel_explain": "The name combines two ordinary Arabic words and was used as an honorific. Its association with Imad al-Din Zengi is historical, not scriptural.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Imaduddin is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with Imad al-Din Zengi and the military history of the medieval Near East.",
        "cult_interp": "Families may value the imagery of support and steadfastness; this is a naming preference.",
        "hist_note": "Imad al-Din Zengi (d. 541/1146) is a well-known bearer; the name appears widely in biographical and historical works.",
        "trs": {
            "urdu": ("عماد الدین", "دین کا ستون"),
            "persian": ("عمادالدین", "ستون دین"),
            "hindi": ("इमादुद्दीन", "धर्म का स्तंभ"),
            "pashto": ("عماد الدین", "د دین ستنه"),
            "arabic": ("عماد الدين", "عماد الدين، اسم مركب بمعنى عماد الدين"),
        },
        "pron": "i-maad-ud-DEEN",
        "mispron": "IM-ad-ud-DEEN",
        "evidence": [
            ("Ibn al-Athīr, al-Kāmil fī al-Tārīkh", "", "Historical account of Imad al-Din Zengi.", "Classical reports are not independently rechecked in this pass."),
            ("Ibn Khallikān, Wafayāt al-Aʿyān", "", "Biographical notices for bearers of the name.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Imad al-Din Zengi bore the name", "Ibn al-Athīr, al-Kāmil fī al-Tārīkh", "classical_source_listed_not_rechecked"),
            ("Imaduddin is a compound honorific meaning pillar of the religion", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["compound_honorific_not_Quranic"],
        "selection": "Included because a widely used historical honorific is absent from the dataset.",
    },
    {
        "name": "Tajuddin",
        "slug": "tajuddin",
        "gender": "Male",
        "aliases": ["Tajudeen", "Tajudheen"],
        "ar": "تَاجُ الدِّين",
        "tr": "tāj al-dīn",
        "root": "ت ا ج / د ي ن",
        "roottr": "t-j / d-y-n",
        "morph": "Compound genitive: تاج (“crown”) + الدين (“the religion”).",
        "short": "Crown of the religion",
        "primary": (
            "Tajuddin (تاج الدين) is a compound honorific name meaning “crown of the religion”. It "
            "was borne by classical scholars such as Taj al-Din al-Subki (d. 771/1370). The name is "
            "not Qur'anic; it is a historical Muslim honorific."
        ),
        "literal": "Crown of the religion",
        "explain": (
            "The compound joins tāj (“crown”) with al-din (“the religion”). It follows the medieval "
            "X al-Din honorific pattern. The record describes the construction and its bearer "
            "without asserting a scriptural origin."
        ),
        "sem": "Islamic honorific names and scholarship",
        "concepts": ["honorific names", "classical scholarship", "al-Din compounds"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Tajuddin is a historical compound honorific, not a Qur'anic name.",
        "rel_assoc": "Islamic scholarly and honorific naming",
        "rel_status": "A historical honorific name, not a Qur'anic or divine name.",
        "rel_explain": "The name combines two ordinary Arabic words and was used as an honorific. Its association with Taj al-Din al-Subki is historical, not scriptural.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Tajuddin is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with the scholarly al-Subki family and the tradition of Islamic learning.",
        "cult_interp": "Families may value the imagery of honor and learning; this is a naming preference.",
        "hist_note": "Taj al-Din al-Subki (d. 771/1370) is a recorded bearer; the name appears in biographical dictionaries.",
        "trs": {
            "urdu": ("تاج الدین", "دین کا تاج"),
            "persian": ("تاج‌الدین", "تاج دین"),
            "hindi": ("ताजुद्दीन", "धर्म का मुकुट"),
            "pashto": ("تاج الدین", "د دین تاج"),
            "arabic": ("تاج الدين", "تاج الدين، اسم مركب بمعنى تاج الدين"),
        },
        "pron": "taaj-ud-DEEN",
        "mispron": "TAJ-ud-DEEN",
        "evidence": [
            ("al-Subkī, Ṭabaqāt al-Shāfiʿiyyah al-Kubrā", "", "Biographical entries for the al-Subki family, including Taj al-Din al-Subki.", "Classical reports are not independently rechecked in this pass."),
            ("Ibn Ḥajar, al-Durar al-Kāminah", "", "Biographical dictionary covering the same scholarly milieu.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Taj al-Din al-Subki bore the name", "al-Subkī, Ṭabaqāt al-Shāfiʿiyyah al-Kubrā", "classical_source_listed_not_rechecked"),
            ("Tajuddin is a compound honorific meaning crown of the religion", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["compound_honorific_not_Quranic"],
        "selection": "Included because a widely used historical honorific is absent from the dataset.",
    },
    {
        "name": "Qutbuddin",
        "slug": "qutbuddin",
        "gender": "Male",
        "aliases": ["Qutubuddin", "Kutbuddin"],
        "ar": "قُطْبُ الدِّين",
        "tr": "quṭb al-dīn",
        "root": "ق ط ب / د ي ن",
        "roottr": "q-ṭ-b / d-y-n",
        "morph": "Compound genitive: قطب (“axis, pole”) + الدين (“the religion”).",
        "short": "Axis or pole of the religion",
        "primary": (
            "Qutbuddin (قطب الدين) is a compound honorific name meaning “axis” or “pole of the "
            "religion”. It was borne by Qutb al-Din Aibak (d. 607/1210), the founder of the Mamluk "
            "dynasty of Delhi. The name is not Qur'anic; it is a historical Muslim honorific."
        ),
        "literal": "Axis or pole of the religion",
        "explain": (
            "The compound joins quṭb (“axis, pole”) with al-din (“the religion”). It follows the "
            "medieval X al-Din honorific pattern. The record describes the construction and its "
            "historical bearer without claiming a scriptural origin."
        ),
        "sem": "Islamic honorific names and rule",
        "concepts": ["honorific names", "Delhi Sultanate", "medieval Islamic history"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Qutbuddin is a historical compound honorific, not a Qur'anic name.",
        "rel_assoc": "Islamic historical and honorific naming",
        "rel_status": "A historical honorific name, not a Qur'anic or divine name.",
        "rel_explain": "The name combines two ordinary Arabic words and was used as an honorific. Its association with Qutb al-Din Aibak is historical, not scriptural.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Qutbuddin is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with Qutb al-Din Aibak and the foundation of the Delhi Sultanate.",
        "cult_interp": "Families may value the imagery of a center or axis of faith; this is a naming preference.",
        "hist_note": "Qutb al-Din Aibak (d. 607/1210) is a well-known bearer; the name is recorded in medieval biographical and historical works.",
        "trs": {
            "urdu": ("قطب الدین", "دین کا قطب/مرکز"),
            "persian": ("قطب‌الدین", "قطب دین"),
            "hindi": ("क़ुतबुद्दीन", "धर्म का केंद्र/ध्रुव"),
            "pashto": ("قطب الدین", "د دین قطب"),
            "arabic": ("قطب الدين", "قطب الدين، اسم مركب بمعنى قطب الدين"),
        },
        "pron": "qutb-ud-DEEN",
        "mispron": "kutub-ud-DEEN",
        "evidence": [
            ("Minhāj al-Sirāj, Ṭabaqāt-i Nāṣirī", "", "Chronicle of the Delhi Sultanate covering Qutb al-Din Aibak.", "Classical reports are not independently rechecked in this pass."),
            ("Ibn Bībī, al-Awāmir al-ʿAlāʾiyyah", "", "Court chronicle of the period; contextual source for the honorific.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Qutb al-Din Aibak bore the name", "Minhāj al-Sirāj, Ṭabaqāt-i Nāṣirī", "classical_source_listed_not_rechecked"),
            ("Qutbuddin is a compound honorific meaning axis of the religion", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["compound_honorific_not_Quranic"],
        "selection": "Included because a widely used historical honorific is absent from the dataset.",
    },
    {
        "name": "Sayfuddin",
        "slug": "sayfuddin",
        "gender": "Male",
        "aliases": ["Saifuddin", "Saifudeen", "Seifuddin"],
        "ar": "سَيْفُ الدِّين",
        "tr": "sayf al-dīn",
        "root": "س ي ف / د ي ن",
        "roottr": "s-y-f / d-y-n",
        "morph": "Compound genitive: سيف (“sword”) + الدين (“the religion”).",
        "short": "Sword of the religion",
        "primary": (
            "Sayfuddin (سيف الدين) is a compound honorific name meaning “sword of the religion”. It "
            "was borne by Sayf al-Din Qutuz (d. 658/1260), the Mamluk sultan who defeated the "
            "Mongols at Ain Jalut. The name is not Qur'anic; it is a historical Muslim honorific."
        ),
        "literal": "Sword of the religion",
        "explain": (
            "The compound joins sayf (“sword”) with al-din (“the religion”). Medieval honorific "
            "names of this type were used by rulers and scholars. The record describes the "
            "construction and its historical bearer without asserting a scriptural origin."
        ),
        "sem": "Islamic honorific names and military history",
        "concepts": ["honorific names", "Mamluk Sultanate", "Ain Jalut"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Sayfuddin is a historical compound honorific, not a Qur'anic name.",
        "rel_assoc": "Islamic historical and honorific naming",
        "rel_status": "A historical honorific name, not a Qur'anic or divine name.",
        "rel_explain": "The name combines two ordinary Arabic words and was used as an honorific. Its association with Sayf al-Din Qutuz is historical, not scriptural.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Sayfuddin is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with Sayf al-Din Qutuz and the Mamluk victory at Ain Jalut.",
        "cult_interp": "Families may value the imagery of defense and resolve; this is a naming preference.",
        "hist_note": "Sayf al-Din Qutuz (d. 658/1260) is a well-known bearer; the name also appears in biographical works on other figures.",
        "trs": {
            "urdu": ("سیف الدین", "دین کی تلوار"),
            "persian": ("سیف‌الدین", "شمشیر دین"),
            "hindi": ("सैफ़ुद्दीन", "धर्म की तलवार"),
            "pashto": ("سیف الدین", "د دین توره"),
            "arabic": ("سيف الدين", "سيف الدين، اسم مركب بمعنى سيف الدين"),
        },
        "pron": "sayf-ud-DEEN",
        "mispron": "sigh-fud-DEEN",
        "evidence": [
            ("al-Maqrīzī, al-Sulūk li-Maʿrifat Duwal al-Mulūk", "", "Mamluk history covering Sayf al-Din Qutuz.", "Classical reports are not independently rechecked in this pass."),
            ("Ibn Kathīr, al-Bidāyah wa-al-Nihāyah", "", "Historical account of the Mamluk period and Ain Jalut.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Sayf al-Din Qutuz bore the name", "al-Maqrīzī, al-Sulūk", "classical_source_listed_not_rechecked"),
            ("Sayfuddin is a compound honorific meaning sword of the religion", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["compound_honorific_not_Quranic"],
        "selection": "Included because a widely used historical honorific is absent from the dataset.",
    },
    {
        "name": "Nasiruddin",
        "slug": "nasiruddin",
        "gender": "Male",
        "aliases": ["Nasirudeen", "Nasruddin", "Nasirudheen"],
        "ar": "نَاصِرُ الدِّين",
        "tr": "nāṣir al-dīn",
        "root": "ن ص ر / د ي ن",
        "roottr": "n-ṣ-r / d-y-n",
        "morph": "Compound genitive: ناصر (“helper”) + الدين (“the religion”).",
        "short": "Helper of the religion",
        "primary": (
            "Nasiruddin (ناصر الدين) is a compound honorific name meaning “helper of the religion”. "
            "It was borne by the polymath Nasir al-Din al-Tusi (d. 672/1274). The name is not "
            "Qur'anic; it is a historical Muslim honorific."
        ),
        "literal": "Helper of the religion",
        "explain": (
            "The compound joins nāṣir (“helper”) with al-din (“the religion”). It follows the "
            "medieval X al-Din honorific pattern. The record describes the construction and its "
            "bearer without claiming a scriptural origin."
        ),
        "sem": "Islamic honorific names and scholarship",
        "concepts": ["honorific names", "Ilkhanid scholarship", "astronomy and philosophy"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Nasiruddin is a historical compound honorific, not a Qur'anic name.",
        "rel_assoc": "Islamic scholarly and honorific naming",
        "rel_status": "A historical honorific name, not a Qur'anic or divine name.",
        "rel_explain": "The name combines two ordinary Arabic words and was used as an honorific. Its association with Nasir al-Din al-Tusi is historical, not scriptural.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Nasiruddin is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with Nasir al-Din al-Tusi and the scholarly culture of the Ilkhanid period.",
        "cult_interp": "Families may value the imagery of support and learning; this is a naming preference.",
        "hist_note": "Nasir al-Din al-Tusi (d. 672/1274) is a well-known bearer; the name is widely recorded.",
        "trs": {
            "urdu": ("ناصر الدین", "دین کا مددگار"),
            "persian": ("ناصرالدین", "یاری‌کننده دین"),
            "hindi": ("नासिरुद्दीन", "धर्म का सहायक"),
            "pashto": ("ناصر الدین", "د دین مرستندوی"),
            "arabic": ("ناصر الدين", "ناصر الدين، اسم مركب بمعنى ناصر الدين"),
        },
        "pron": "naa-sir-ud-DEEN",
        "mispron": "NAS-ir-ud-DEEN",
        "evidence": [
            ("Ibn Khallikān, Wafayāt al-Aʿyān", "", "Biographical notices for Nasir al-Din al-Tusi.", "Classical reports are not independently rechecked in this pass."),
            ("Rashīd al-Dīn, Jāmiʿ al-Tawārīkh", "", "Ilkhanid historical work covering al-Tusi's period.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Nasir al-Din al-Tusi bore the name", "Ibn Khallikān, Wafayāt al-Aʿyān", "classical_source_listed_not_rechecked"),
            ("Nasiruddin is a compound honorific meaning helper of the religion", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["compound_honorific_not_Quranic"],
        "selection": "Included because a widely used historical honorific is absent from the dataset.",
    },
    {
        "name": "Nizamuddin",
        "slug": "nizamuddin",
        "gender": "Male",
        "aliases": ["Nizamudeen", "Nizamudheen"],
        "ar": "نِظَامُ الدِّين",
        "tr": "niẓām al-dīn",
        "root": "ن ظ م / د ي ن",
        "roottr": "n-ẓ-m / d-y-n",
        "morph": "Compound genitive: نظام (“order, system”) + الدين (“the religion”).",
        "short": "Order of the religion",
        "primary": (
            "Nizamuddin (نظام الدين) is a compound honorific name meaning “order of the religion”. "
            "It is best known from Nizam al-Din Auliya (d. 725/1325), the Chishti Sufi saint of "
            "Delhi. The name is not Qur'anic; it is a historical Muslim honorific."
        ),
        "literal": "Order of the religion",
        "explain": (
            "The compound joins niẓām (“order, system”) with al-din (“the religion”). It was used as "
            "an honorific by scholars and Sufi figures. The record describes the construction and "
            "its bearer without claiming a scriptural origin."
        ),
        "sem": "Islamic honorific names and Sufism",
        "concepts": ["honorific names", "Chishti order", "Delhi"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Nizamuddin is a historical compound honorific, not a Qur'anic name.",
        "rel_assoc": "Islamic historical and honorific naming",
        "rel_status": "A historical honorific name, not a Qur'anic or divine name.",
        "rel_explain": "The name combines two ordinary Arabic words and was used as an honorific. Its association with Nizam al-Din Auliya is historical, not scriptural.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Nizamuddin is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with Nizam al-Din Auliya and the Chishti Sufi tradition of Delhi.",
        "cult_interp": "Families may value the association with spiritual order and discipline; this is a naming preference.",
        "hist_note": "Nizam al-Din Auliya (d. 725/1325) is a well-known bearer; the name is recorded in Sufi and biographical literature.",
        "trs": {
            "urdu": ("نظام الدین", "دین کا نظام"),
            "persian": ("نظام‌الدین", "نظام دین"),
            "hindi": ("निज़ामुद्दीन", "धर्म की व्यवस्था"),
            "pashto": ("نظام الدین", "د دین نظام"),
            "arabic": ("نظام الدين", "نظام الدين، اسم مركب بمعنى نظام الدين"),
        },
        "pron": "ni-zaam-ud-DEEN",
        "mispron": "NIZ-am-ud-DEEN",
        "evidence": [
            ("Amīr Khwurd, Siyar al-Awliyāʾ", "", "Chishti biographical literature covering Nizam al-Din Auliya.", "Classical reports are not independently rechecked in this pass."),
            ("Ibn Ḥajar, al-Durar al-Kāminah", "", "Biographical dictionary covering the period.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Nizam al-Din Auliya bore the name", "Amīr Khwurd, Siyar al-Awliyāʾ", "classical_source_listed_not_rechecked"),
            ("Nizamuddin is a compound honorific meaning order of the religion", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["compound_honorific_not_Quranic"],
        "selection": "Included because a widely used historical honorific is absent from the dataset.",
    },
    {
        "name": "Jamaluddin",
        "slug": "jamaluddin",
        "gender": "Male",
        "aliases": ["Jamaludeen", "Jamal-Ud-Din"],
        "ar": "جَمَالُ الدِّين",
        "tr": "jamāl al-dīn",
        "root": "ج م ل / د ي ن",
        "roottr": "j-m-l / d-y-n",
        "morph": "Compound genitive: جمال (“beauty”) + الدين (“the religion”).",
        "short": "Beauty of the religion",
        "primary": (
            "Jamaluddin (جمال الدين) is a compound honorific name meaning “beauty of the religion”. "
            "It was borne by Jamal al-Din al-Afghani (d. 1314/1897), the reformist thinker. The name "
            "is not Qur'anic; it is a historical Muslim honorific."
        ),
        "literal": "Beauty of the religion",
        "explain": (
            "The compound joins jamāl (“beauty”) with al-din (“the religion”). It follows the "
            "medieval X al-Din honorific pattern and was used by scholars and modern reformers. The "
            "record describes the construction and its bearer without claiming a scriptural origin."
        ),
        "sem": "Islamic honorific names and reform",
        "concepts": ["honorific names", "Islamic modernism", "al-Afghani"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Jamaluddin is a historical compound honorific, not a Qur'anic name.",
        "rel_assoc": "Islamic historical and honorific naming",
        "rel_status": "A historical honorific name, not a Qur'anic or divine name.",
        "rel_explain": "The name combines two ordinary Arabic words and was used as an honorific. Its association with Jamal al-Din al-Afghani is historical, not scriptural.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Jamaluddin is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with Jamal al-Din al-Afghani and the reform debates of the late nineteenth century.",
        "cult_interp": "Families may value the imagery of beauty and faith; this is a naming preference.",
        "hist_note": "Jamal al-Din al-Afghani (d. 1314/1897) is a well-known modern bearer; the name also appears in earlier biographical works.",
        "trs": {
            "urdu": ("جمال الدین", "دین کی خوبصورتی"),
            "persian": ("جمال‌الدین", "زیبایی دین"),
            "hindi": ("जमालुद्दीन", "धर्म की सुंदरता"),
            "pashto": ("جمال الدین", "د دین ښکلا"),
            "arabic": ("جمال الدين", "جمال الدين، اسم مركب بمعنى جمال الدين"),
        },
        "pron": "ja-maal-ud-DEEN",
        "mispron": "JAM-al-ud-DEEN",
        "evidence": [
            ("Rashīd Riḍā, Taʾrīkh al-Ustādh al-Imām", "", "Biography of Jamal al-Din al-Afghani by his associate.", "Classical reports are not independently rechecked in this pass."),
            ("Ibn Khallikān, Wafayāt al-Aʿyān", "", "Earlier biographical notices for bearers of the name.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Jamal al-Din al-Afghani bore the name", "Rashīd Riḍā, Taʾrīkh al-Ustādh al-Imām", "classical_source_listed_not_rechecked"),
            ("Jamaluddin is a compound honorific meaning beauty of the religion", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["compound_honorific_not_Quranic"],
        "selection": "Included because a widely used historical honorific is absent from the dataset.",
    },
    {
        "name": "Nuruddin",
        "slug": "nuruddin",
        "gender": "Male",
        "aliases": ["Nuredeen", "Nooruddin", "Nur-Ud-Din"],
        "ar": "نُورُ الدِّين",
        "tr": "nūr al-dīn",
        "root": "ن و ر / د ي ن",
        "roottr": "n-w-r / d-y-n",
        "morph": "Compound genitive: نور (“light”) + الدين (“the religion”).",
        "short": "Light of the religion",
        "primary": (
            "Nuruddin (نور الدين) is a compound honorific name meaning “light of the religion”. It "
            "was borne by Nur al-Din Zengi (d. 569/1174), the Zengid ruler and contemporary of the "
            "Crusades. The name is not Qur'anic; it is a historical Muslim honorific."
        ),
        "literal": "Light of the religion",
        "explain": (
            "The compound joins nūr (“light”) with al-din (“the religion”). It follows the medieval "
            "X al-Din honorific pattern. The record describes the construction and its historical "
            "bearer without claiming a scriptural origin."
        ),
        "sem": "Islamic honorific names and rule",
        "concepts": ["honorific names", "Zengid dynasty", "medieval Islamic history"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Nuruddin is a historical compound honorific, not a Qur'anic name.",
        "rel_assoc": "Islamic historical and honorific naming",
        "rel_status": "A historical honorific name, not a Qur'anic or divine name.",
        "rel_explain": "The name combines two ordinary Arabic words and was used as an honorific. Its association with Nur al-Din Zengi is historical, not scriptural.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Nuruddin is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with Nur al-Din Zengi and the medieval politics of the Near East.",
        "cult_interp": "Families may value the imagery of light and guidance; this is a naming preference.",
        "hist_note": "Nur al-Din Mahmud Zengi (d. 569/1174) is a well-known bearer; the name is recorded in medieval historical works.",
        "trs": {
            "urdu": ("نور الدین", "دین کا نور"),
            "persian": ("نورالدین", "نور دین"),
            "hindi": ("नूरुद्दीन", "धर्म का प्रकाश"),
            "pashto": ("نور الدین", "د دین رڼا"),
            "arabic": ("نور الدين", "نور الدين، اسم مركب بمعنى نور الدين"),
        },
        "pron": "noor-ud-DEEN",
        "mispron": "NUR-ud-DEEN",
        "evidence": [
            ("Ibn al-Athīr, al-Kāmil fī al-Tārīkh", "", "Historical account of Nur al-Din Zengi.", "Classical reports are not independently rechecked in this pass."),
            ("Ibn Khallikān, Wafayāt al-Aʿyān", "", "Biographical notices for bearers of the name.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Nur al-Din Zengi bore the name", "Ibn al-Athīr, al-Kāmil fī al-Tārīkh", "classical_source_listed_not_rechecked"),
            ("Nuruddin is a compound honorific meaning light of the religion", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["compound_honorific_not_Quranic"],
        "selection": "Included because a widely used historical honorific is absent from the dataset.",
    },
    {
        "name": "Badruddin",
        "slug": "badruddin",
        "gender": "Male",
        "aliases": ["Badrudeen", "Badr-Ud-Din"],
        "ar": "بَدْرُ الدِّين",
        "tr": "badr al-dīn",
        "root": "ب د ر / د ي ن",
        "roottr": "b-d-r / d-y-n",
        "morph": "Compound genitive: بدر (“full moon”) + الدين (“the religion”).",
        "short": "Full moon of the religion",
        "primary": (
            "Badruddin (بدر الدين) is a compound honorific name meaning “full moon of the religion”. "
            "It was borne by several classical scholars, including Badr al-Din al-Ayni (d. "
            "855/1451), the hadith scholar and historian. The name is not Qur'anic; it is a "
            "historical Muslim honorific."
        ),
        "literal": "Full moon of the religion",
        "explain": (
            "The compound joins badr (“full moon”) with al-din (“the religion”). It follows the "
            "medieval X al-Din honorific pattern. The record describes the construction and its "
            "bearer without claiming a scriptural origin."
        ),
        "sem": "Islamic honorific names and scholarship",
        "concepts": ["honorific names", "hadith scholarship", "Mamluk period"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "Badruddin is a historical compound honorific, not a Qur'anic name.",
        "rel_assoc": "Islamic scholarly and honorific naming",
        "rel_status": "A historical honorific name, not a Qur'anic or divine name.",
        "rel_explain": "The name combines two ordinary Arabic words and was used as an honorific. Its association with Badr al-Din al-Ayni is historical, not scriptural.",
        "hadith": ("not_verified", "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented."),
        "prophetic": ("not_verified", "Badruddin is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with Badr al-Din al-Ayni and the hadith scholarship of the Mamluk period.",
        "cult_interp": "Families may value the imagery of radiance and learning; this is a naming preference.",
        "hist_note": "Badr al-Din al-Ayni (d. 855/1451) is a recorded bearer; the name appears in biographical dictionaries.",
        "trs": {
            "urdu": ("بدر الدین", "دین کا چاند"),
            "persian": ("بدرالدین", "ماه کامل دین"),
            "hindi": ("बदरुद्दीन", "धर्म का पूर्ण चंद्रमा"),
            "pashto": ("بدر الدین", "د دین بشپړه میاشت"),
            "arabic": ("بدر الدين", "بدر الدين، اسم مركب بمعنى بدر الدين"),
        },
        "pron": "badr-ud-DEEN",
        "mispron": "BAD-er-ud-DEEN",
        "evidence": [
            ("al-Sakhāwī, al-Ḍawʾ al-Lāmiʿ", "", "Biographical dictionary covering Badr al-Din al-Ayni.", "Classical reports are not independently rechecked in this pass."),
            ("Ibn Ḥajar, al-Durar al-Kāminah", "", "Biographical dictionary covering the same scholarly milieu.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Badr al-Din al-Ayni bore the name", "al-Sakhāwī, al-Ḍawʾ al-Lāmiʿ", "classical_source_listed_not_rechecked"),
            ("Badruddin is a compound honorific meaning full moon of the religion", "Lane, An Arabic-English Lexicon", "lexical_source_listed_not_rechecked"),
        ],
        "flags": ["compound_honorific_not_Quranic"],
        "selection": "Included because a widely used historical honorific is absent from the dataset.",
    },
    {
        "name": "AbdurRashid",
        "slug": "abdurrashid",
        "gender": "Male",
        "aliases": ["Abdur-Rashid", "Abdurrasheed", "AbdulRashid"],
        "ar": "عَبْدُ الرَّشِيد",
        "tr": "ʿabd al-rashīd",
        "root": "ع ب د / ر ش د",
        "roottr": "ʿ-b-d / r-sh-d",
        "morph": "Theophoric compound: عبد (“servant”) + الرشيد (the divine name).",
        "short": "Servant of the Rightly-Guided One",
        "primary": (
            "AbdurRashid (عبد الرشيد) is a theophoric compound name meaning “servant of the "
            "Rightly-Guided One”, from ʿabd (“servant”) and al-Rashid, a divine name meaning “the "
            "Rightly-Guided” or “the Guide to the right path”. It is a common male Muslim name. The "
            "name is not Qur'anic as a personal name, though the root ر ش د and the divine attribute "
            "are Qur'anic."
        ),
        "literal": "Servant of the Rightly-Guided One",
        "explain": (
            "The first element is ʿabd (“servant”), used in construct with a divine name in Islamic "
            "naming convention. Al-Rashid is transmitted as a divine name, and the root ر ش د means "
            "right guidance. The compound is a theophoric name, not a historical title like the X "
            "al-Din compounds."
        ),
        "sem": "Theophoric names and divine guidance",
        "concepts": ["theophoric names", "divine guidance", "servanthood"],
        "quran": False,
        "qstatus": "not_a_Quranic_person_name",
        "qnote": "The root ر ش د occurs in the Qur'an (e.g., 18:10 and 72:2) and al-Rashid is transmitted as a divine name, but AbdurRashid is not a Qur'anic personal name.",
        "rel_assoc": "Islamic monotheism; theophoric ʿAbd name",
        "rel_status": "A theophoric servant-name (ʿAbd + divine name).",
        "rel_explain": "Islamic naming convention uses ʿAbd in construct with a name or attribute of God. Al-Rashid is a divine name in the traditional lists; the record does not claim it is verbatim Qur'anic.",
        "hadith": ("not_verified", "No specific authentic hadith report about this compound name is cited; none is invented."),
        "prophetic": ("not_verified", "AbdurRashid is not the name of a prophet."),
        "companion": ("not_verified", "No companion attribution is asserted."),
        "cult_note": "The name is associated with the Islamic convention of servant-names and with the theme of right guidance.",
        "cult_interp": "Families may value the expression of servanthood and guidance; this is a naming preference.",
        "hist_note": "The name is widespread in Muslim societies; biographical works record bearers across the classical and modern periods.",
        "trs": {
            "urdu": ("عبدالرشید", "راست راہ دکھانے والے کا بندہ"),
            "persian": ("عبدالرشید", "بنده رهنمای راست"),
            "hindi": ("अब्दुर्रशीद", "सीधा मार्ग दिखाने वाले का सेवक"),
            "pashto": ("عبدالرشید", "د سمې لارې ښوونکي بنده"),
            "arabic": ("عبد الرشيد", "عبد الرشيد، اسم مركب بمعنى عبد الرشيد"),
        },
        "pron": "ab-dur-raz-ZEED",
        "mispron": "ab-dur-RA-shid",
        "pron_note": "Romanized guide only; the Arabic ʿayn and emphatic consonants have no exact English equivalent.",
        "evidence": [
            ("Qur'an 18:10 and 72:2", "https://quran.com/18/10", "Qur'anic usage of the root ر ش د in the sense of right guidance.", "The verses use the word, not the personal name AbdurRashid."),
            ("Traditional lists of the divine names (al-Tirmidhī, Sunan)", "https://sunnah.com/tirmidhi", "Al-Rashid transmitted among the divine names.", "The list is traditional; this record does not claim a verbatim Qur'anic form for the name."),
        ],
        "claims": [
            ("The root ر ش د occurs in the Qur'an in the sense of right guidance", "https://quran.com/18/10", "primary_text_cited_not_rechecked_in_this_pass"),
            ("Al-Rashid is transmitted as a divine name in traditional lists", "https://sunnah.com/tirmidhi", "traditional_source_listed_not_rechecked"),
        ],
        "flags": ["theophoric_abd_name", "not_Quranic_person_name"],
        "selection": "Included because a common theophoric name is absent from the dataset, with precise notes on what is and is not Qur'anic.",
    },
]


DATA += [
    {
        "name": "Abdulmuttalib",
        "slug": "abdulmuttalib",
        "gender": "Male",
        "gconf": "HIGH",
        "aliases": ["Abdul Muttalib", "Abd al-Muttalib", "Abdulmutalib"],
        "ar": "عَبْدُ الْمُطَّلِب",
        "tr": "ʿabd al-muṭṭalib",
        "root": "ع ب د",
        "roottr": "ʿ-b-d",
        "morph": "Compound: عبد (“servant”) + المطلب (a proper name); not a theophoric ʿAbd name.",
        "short": "Servant of al-Muttalib; the name of the Prophet's grandfather",
        "primary": (
            "Abdulmuttalib (عبد المطلب) is a compound name meaning “servant of al-Muttalib”. It is "
            "the name by which Shayba ibn Hashim, the Prophet Muhammad's paternal grandfather, was "
            "known. The second element is a personal name rather than an attribute of God, so the "
            "compound is not one of the theophoric ʿAbd names such as Abdullah."
        ),
        "literal": "Servant of al-Muttalib",
        "explain": (
            "The first element عبد means “servant” and the second is the proper name المطلب. Ibn "
            "Hisham's Sirah reports that Shayba was raised by his uncle al-Muttalib and became known "
            "as Abd al-Muttalib. The name is historical and is not a Qur'anic term or a divine "
            "attribute."
        ),
        "sem": "Prophetic family history",
        "concepts": ["Prophet's grandfather", "Shayba ibn Hashim", "pre-Islamic Makkah"],
        "quran": False,
        "qstatus": "not_in_Quran",
        "qnote": "The name is not Qur'anic; it is the historical name of the Prophet's grandfather.",
        "rel_assoc": "Prophetic family history",
        "rel_status": "A historical family name, not a divine attribute or a Qur'anic name.",
        "rel_explain": (
            "Abd al-Muttalib is recorded in the Sirah and biographical literature. It is not a "
            "theophoric ʿAbd name, because al-Muttalib is a person's name, not a name of God."
        ),
        "hadith": ("not_verified", "No specific authentic hadith report establishing a special virtue of the name is cited; none is invented."),
        "prophetic": ("not_verified", "The name is not the name of a prophet; it is the name of the Prophet Muhammad's grandfather."),
        "companion": ("not_verified", "Abd al-Muttalib died before the Prophet's mission and is not counted among the Companions."),
        "cult_note": "The name is associated with the Prophet's grandfather, the guardian of the young Muhammad and a leader of Quraysh.",
        "cult_interp": "Use of the name is often commemorative of the Prophet's family history; the record does not infer character from it.",
        "hist_status": "documented_in_classical_biographical_sources",
        "hist_note": "Ibn Hisham's Sirah and Ibn Sa'd's Tabaqat record Shayba ibn Hashim's life and the origin of the name Abd al-Muttalib.",
        "trs": {
            "urdu": ("عبدالمطلب", "المطلب کا خادم؛ نبی ﷺ کے دادا شیبہ بن ہاشم کا لقب"),
            "persian": ("عبدالمطلب", "خدمتگزار مطلب؛ لقب شیبه بن هاشم، نیای پیامبر"),
            "hindi": ("अब्दुलमुत्तलिब", "अल-मुत्तलिब का सेवक; पैग़ंबर के दादा शैबा बिन हाशिम का नाम"),
            "pashto": ("عبدالمطلب", "د المطلب خدمتګار؛ د پیغمبر نیکه شیبه بن هاشم"),
            "arabic": ("عبد المطلب", "اسم جَدّ النبي صلى الله عليه وسلم شيبة بن هاشم"),
        },
        "pron": "ab-dul-MUT-ta-lib",
        "mispron": "abdul-mu-TALIB",
        "evidence": [
            ("Ibn Hishām, al-Sīrah al-Nabawiyyah", "", "Account of Shayba ibn Hashim, known as Abd al-Muttalib, and the origin of the name.", "Classical reports are not independently rechecked in this pass."),
            ("Ibn Saʿd, Kitāb al-Ṭabaqāt al-Kabīr", "", "Biographical entry for the Prophet's grandfather.", "Classical reports are not independently rechecked in this pass."),
        ],
        "claims": [
            ("Shayba ibn Hashim was known as Abd al-Muttalib", "Ibn Hishām, al-Sīrah al-Nabawiyyah", "classical_source_listed_not_rechecked"),
            ("Abdulmuttalib is not a theophoric ʿAbd name", "Ibn Hishām, al-Sīrah al-Nabawiyyah", "classical_source_listed_not_rechecked"),
        ],
        "flags": ["historical_name_not_Quranic", "not_a_theophoric_Abd_name"],
        "selection": "Included because the Prophet's grandfather's name is absent from the dataset and is widely used as a male given name.",
    },
]


FALLBACK_SOURCES = {
    "shuja": ("Arabic Lexicon, root شجع", "https://arabiclexicon.hawramani.com/%D8%B4%D8%AC%D8%B9/", "Lexical senses of shujāʿ and shujāʿah: brave, courageous.", "The lexicon supports the lexical sense, not the biographical report."),
    "hanbal": ("Arabic Lexicon, root حنبل", "https://arabiclexicon.hawramani.com/%D8%AD%D9%86%D8%A8%D9%84/", "Lexical entries for حنبل, including its use as a man's name.", "Lexical attestation does not establish the biographical details."),
    "shamsuddin": ("Qur'an 91:1", "https://quran.com/91/1", "Qur'anic occurrence of شمس (sun), the first element of the compound.", "The verse uses the word, not the compound name."),
    "fakhruddin": ("Qur'an 31:18", "https://quran.com/31/18", "Qur'anic occurrence of the root فخر in the form فخور.", "The verse uses a related form, not the compound name."),
    "imaduddin": ("Qur'an 104:8–9", "https://quran.com/104/8", "Qur'anic occurrence of عمد (pillars).", "The verse uses the word, not the compound name."),
    "tajuddin": ("Arabic Lexicon, root تاج", "https://arabiclexicon.hawramani.com/%D8%AA%D8%A7%D8%AC/", "Lexical entry for تاج (crown).", "The lexicon supports the element, not the honorific."),
    "qutbuddin": ("Arabic Lexicon, root قطب", "https://arabiclexicon.hawramani.com/%D9%82%D8%B7%D8%A8/", "Lexical senses of قطب (axis, pole).", "The lexicon supports the element, not the honorific."),
    "sayfuddin": ("Arabic Lexicon, root سيف", "https://arabiclexicon.hawramani.com/%D8%B3%D9%8A%D9%81/", "Lexical entry for سيف (sword).", "The lexicon supports the element, not the honorific."),
    "nasiruddin": ("Qur'an 110:1", "https://quran.com/110/1", "Qur'anic occurrence of نصر (help, victory).", "The verse uses the word, not the compound name."),
    "nizamuddin": ("Arabic Lexicon, root نظم", "https://arabiclexicon.hawramani.com/%D9%86%D8%B8%D9%85/", "Lexical senses of نظم/نظام (order, arrangement).", "The lexicon supports the element, not the honorific."),
    "jamaluddin": ("Qur'an 16:6", "https://quran.com/16/6", "Qur'anic occurrence of جمال (beauty).", "The verse uses the word, not the compound name."),
    "nuruddin": ("Qur'an 24:35", "https://quran.com/24/35", "Qur'anic occurrence of نور (light).", "The verse uses the word, not the compound name."),
    "badruddin": ("Qur'an 3:123", "https://quran.com/3/123", "Qur'anic occurrence of بدر (Badr).", "The verse refers to the battle site, not the compound name."),
    "abdulmuttalib": ("Arabic Lexicon, root طلب", "https://arabiclexicon.hawramani.com/%D8%B7%D9%84%D8%A8/", "Lexical senses of طلب (to seek), the root behind the name المطلب.", "The lexicon supports the root, not the historical name."),
}
for _entry in DATA:
    if not any(item[1] for item in _entry["evidence"]):
        _entry["evidence"].append(FALLBACK_SOURCES[_entry["slug"]])


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def dataset_index(
    excluded_stems: set[str] | None = None,
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    excluded_stems = excluded_stems or set()
    latin: dict[str, set[str]] = {}
    script: dict[str, set[str]] = {}
    for path in sorted(DATASET.glob("*.json")):
        if path.name.startswith("PROGRESS") or path.stem in excluded_stems:
            continue
        try:
            record = read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        data = record.get("data")
        if not isinstance(data, dict):
            continue
        forms: list[str] = [path.stem]
        for key in ("name", "slug"):
            value = data.get(key)
            if isinstance(value, str):
                forms.append(value)
        identity = data.get("identity", {})
        if isinstance(identity, dict):
            for key in ("display_name", "normalized_name"):
                value = identity.get(key)
                if isinstance(value, str):
                    forms.append(value)
            for key in ("alternate_spellings", "search_variants", "merged_aliases"):
                forms.extend(str(item) for item in identity.get(key, []) if item)
        variants = data.get("name_variants", {})
        if isinstance(variants, dict):
            forms.extend(str(item) for item in variants.get("romanized_variants", []) if item)
        for form in forms:
            key = norm_latin(form)
            if key:
                latin.setdefault(key, set()).add(path.stem)

        script_forms: list[str] = []
        etymology = data.get("etymology", {})
        if isinstance(etymology, dict) and etymology.get("lexical_form"):
            script_forms.append(str(etymology["lexical_form"]))
        if isinstance(variants, dict):
            script_forms.extend(str(item) for item in variants.get("script_forms", []) if item)
        translations = data.get("translations", {})
        if isinstance(translations, dict):
            for locale in ("arabic", "urdu", "persian", "pashto"):
                item = translations.get(locale)
                if isinstance(item, dict) and item.get("script"):
                    script_forms.append(str(item["script"]))
        pronunciation = data.get("pronunciation", {})
        if isinstance(pronunciation, dict):
            scripts = pronunciation.get("scripts", {})
            if isinstance(scripts, dict):
                script_forms.extend(str(item) for item in scripts.values() if item)
        for form in script_forms:
            key = norm_script(form)
            if key:
                script.setdefault(key, set()).add(path.stem)
    return latin, script


def audit_collisions(
    entries: list[dict[str, Any]],
    latin_index: dict[str, set[str]],
    script_index: dict[str, set[str]],
) -> list[str]:
    errors: list[str] = []
    for entry in entries:
        latin_forms = [entry["name"], entry["slug"], *entry.get("aliases", [])]
        for form in latin_forms:
            key = norm_latin(form)
            hits = sorted(latin_index.get(key, set()))
            if hits:
                errors.append(f"Latin collision: {entry['name']} form {form!r} -> {hits}")
        script_forms = [entry["ar"], entry["trs"]["hindi"][0]]
        for locale in ("urdu", "persian", "pashto", "arabic"):
            script_forms.append(entry["trs"][locale][0])
        for form in script_forms:
            key = norm_script(form)
            hits = sorted(script_index.get(key, set()))
            if hits:
                errors.append(f"Script collision: {entry['name']} form {form!r} -> {hits}")
    return list(dict.fromkeys(errors))


def validate_record(record: dict[str, Any], template: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    label = entry["name"]
    if record.get("schema_version") != template.get("schema_version"):
        errors.append(f"{label}: schema_version mismatch")
    if record.get("success") is not True:
        errors.append(f"{label}: success must be true")
    if set(key_paths(record)) != set(key_paths(template)):
        missing = sorted(set(key_paths(template)) - set(key_paths(record)))
        extra = sorted(set(key_paths(record)) - set(key_paths(template)))
        errors.append(f"{label}: key-path mismatch; missing={missing[:5]} extra={extra[:5]}")
    data = record["data"]
    if data["name"] != entry["name"] or data["slug"] != entry["slug"]:
        errors.append(f"{label}: name/slug mismatch")
    if not data["core_meaning"]["primary_meaning"]:
        errors.append(f"{label}: empty primary meaning")
    if len(data["faq"]) < 8:
        errors.append(f"{label}: fewer than eight FAQs")
    faq_nodes = [n for n in data["structured_data"]["@graph"] if n.get("@type") == "FAQPage"]
    if not faq_nodes or len(faq_nodes[0]["mainEntity"]) != len(data["faq"]):
        errors.append(f"{label}: structured FAQ mismatch")
    if set(data["translations"]) != {"english", "urdu", "persian", "hindi", "pashto", "arabic"}:
        errors.append(f"{label}: translation locales mismatch")
    for locale, item in data["translations"].items():
        for key in ("name", "script", "meaning", "long_meaning"):
            if not item.get(key):
                errors.append(f"{label}: translations.{locale}.{key} is blank")
    if data["translation_quality"]["native_review_required"] is not True:
        errors.append(f"{label}: native review must be required")
    if data["popularity"]["score"] is not None:
        errors.append(f"{label}: popularity score must be null")
    if data["popularity"]["render"] is not False:
        errors.append(f"{label}: unmeasured popularity must be hidden")
    if data["numerology"]["render"] is not False:
        errors.append(f"{label}: numerology must be hidden")
    if data["lucky_attributes"]["render"] is not False:
        errors.append(f"{label}: lucky attributes must be hidden")
    if data["editorial_validation"]["needs_manual_verification"] is not True:
        errors.append(f"{label}: manual review flag must remain true")
    if not data["evidence"]["sources"]:
        errors.append(f"{label}: no evidence sources")
    if not data["evidence"]["claim_evidence"]:
        errors.append(f"{label}: no claim-level evidence")
    if data["render_policy"]["render_verified"] is not True:
        errors.append(f"{label}: render_verified must be true")
    return errors


def manifest_entry(entry: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(entry)
    for key in ("hadith", "prophetic", "companion"):
        value[key] = list(value[key])
    value["trs"] = {k: list(v) for k, v in value["trs"].items()}
    value["evidence"] = [list(item) for item in value["evidence"]]
    value["claims"] = [list(item) for item in value["claims"]]
    return value


def build_manifest() -> dict[str, Any]:
    return {
        "manifest_version": 1,
        "batch_id": BATCH_ID,
        "created_at": CREATED_AT,
        "dataset": "upgrading/names_upgraded/islamic",
        "template": "upgrading/names_upgraded/islamic/aaban.json",
        "builder": "upgrading/scripts/add_quranic_names_2026_10.py",
        "selection_policy": COLLECTION_POLICY,
        "verification_summary": {
            "names": len(DATA),
            "latin_and_arabic_script_collision_audit": "required before write",
            "schema": "super-2.0 key-path parity with aaban.json",
            "quranic_claims": "textual attestation recorded; never converted into a personal-name claim or a ruling",
            "popularity": "not measured; no figure asserted",
            "translations": "drafts; native review required",
        },
        "names": [manifest_entry(entry) for entry in DATA],
    }


def update_verification_csv(slugs: list[str]) -> int:
    with VERIFICATION_CSV.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = ["path", "slug", "status", "batch"]
    existing = {row["slug"] for row in rows}
    added = 0
    for slug in slugs:
        if slug in existing:
            continue
        rows.append({
            "path": f"upgrading/names_upgraded/islamic/{slug}.json",
            "slug": slug,
            "status": "QURANIC_BATCH_2026_10",
            "batch": "quranic-2026-10",
        })
        added += 1
    with VERIFICATION_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    return added


def verification_csv_row_count(slugs: list[str]) -> int:
    with VERIFICATION_CSV.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    wanted = set(slugs)
    return sum(1 for row in rows if row.get("slug") in wanted)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="Write records after all checks pass")
    group.add_argument("--check", action="store_true", help="Verify that persisted records match")
    args = parser.parse_args(argv)

    template = read_json(TEMPLATE)
    if template.get("schema_version") != "super-2.0":
        print("Template is not super-2.0", file=sys.stderr)
        return 1

    records = [build_record(entry, template) for entry in DATA]
    errors: list[str] = []
    for record, entry in zip(records, DATA):
        errors.extend(validate_record(record, template, entry))
    if errors:
        print("Record validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    latin_index, script_index = dataset_index({entry["slug"] for entry in DATA})
    collisions = audit_collisions(DATA, latin_index, script_index)
    if collisions:
        print("Collision audit failed:", file=sys.stderr)
        for error in collisions:
            print(f"  - {error}", file=sys.stderr)
        return 1

    slugs = [entry["slug"] for entry in DATA]
    if len(set(slugs)) != len(slugs):
        print("Duplicate slugs in batch", file=sys.stderr)
        return 1

    if args.check:
        missing = [slug for slug in slugs if not (DATASET / f"{slug}.json").exists()]
        if missing:
            print("Missing persisted records: " + ", ".join(missing), file=sys.stderr)
            return 1
        for record, entry in zip(records, DATA):
            persisted = read_json(DATASET / f"{entry['slug']}.json")
            if persisted != record:
                print(f"Persisted record differs from build: {entry['slug']}", file=sys.stderr)
                return 1
        print(f"OK: {len(records)} records match the manifest and template; no collisions.")
        return 0

    if args.write:
        existing = [slug for slug in slugs if (DATASET / f"{slug}.json").exists()]
        if existing:
            print("Refusing to overwrite existing files: " + ", ".join(existing), file=sys.stderr)
            return 1
        for record, entry in zip(records, DATA):
            path = DATASET / f"{entry['slug']}.json"
            with path.open("x", encoding="utf-8") as handle:
                json.dump(record, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
        with MANIFEST.open("w", encoding="utf-8") as handle:
            json.dump(build_manifest(), handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        csv_added = update_verification_csv(slugs)
        progress = {
            "schema_version": "super-2.0",
            "batch_id": BATCH_ID,
            "dataset": "upgrading/names_upgraded/islamic",
            "status": "complete",
            "names_added": len(records),
            "slugs": slugs,
            "verification_csv_rows_present": verification_csv_row_count(slugs),
            "schema_key_paths": len(key_paths(template)),
            "collision_audit": "passed (Latin and Arabic script)",
            "processed_at": CREATED_AT,
            "note": (
                "New records built from the super-2.0 template. Claims are source-listed but not "
                "independently rechecked; translations are drafts; popularity is not measured."
            ),
        }
        with PROGRESS_JSON.open("w", encoding="utf-8") as handle:
            json.dump(progress, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"Wrote {len(records)} records, the manifest, {csv_added} CSV rows and the progress file.")
        return 0

    print(f"Dry run OK: {len(records)} records; {len(latin_index)} Latin and {len(script_index)} script keys scanned; no collisions.")
    for entry in DATA:
        print(f"  {entry['name']} ({entry['slug']}) — ready")
    print("No files written. Use --write to add the records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
