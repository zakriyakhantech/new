#!/usr/bin/env python3
"""Build one evidence-gated v2 Islamic-name entry per batch.

This script intentionally separates source entries reviewed from JSON pages emitted:
confirmed spelling variants are recorded in an alias ledger, while unsupported forms
are held for review. It never deletes or edits the original source JSON files.
"""
from __future__ import annotations

import argparse
import csv
import importlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "upgrading" / "names_upgraded" / "islamic"
SCRIPT_DIR = ROOT / "upgrading" / "scripts"
DEST_ROOT = ROOT / "upgrades-namesv2"
OUTPUT_DIR = DEST_ROOT / "islamic"
METADATA_DIR = DEST_ROOT / "metadata"
BATCH_DIR = METADATA_DIR / "batches"
PROGRESS_JSON = METADATA_DIR / "progress.json"
PROGRESS_MD = METADATA_DIR / "progress.md"
ALIAS_LEDGER = METADATA_DIR / "alias_ledger.csv"
HOLD_LEDGER = METADATA_DIR / "source_holds.csv"
BATCH_SIZE = 1
ACCESS_DATE = "2026-10-08"
CONTROL_FILES = {"PROGRESS_CONTENT_FIX.json", "PROGRESS_SUPER2.json", "PROGRESS_V8.json"}

# Explicit same-name alias decisions are applied only when their source file reaches
# the one-name cursor. Each relationship is rechecked against source/target script forms.
ALIASES: dict[str, dict[str, str]] = {
    "aadhil": {
        "canonical_slug": "aadil",
        "basis": "curated42 explicitly identifies the same name; Arabic form, origin, and gender agree.",
    },
    "aadilah": {
        "canonical_slug": "aadila",
        "basis": "curated42 explicitly identifies the same name; Arabic form, origin, and gender agree.",
    },
    "aaf": {
        "canonical_slug": "aisha",
        "basis": "curated42 explicitly links Aaf with Aaisha/Aisha; the Arabic lexical form عائشة, origin, and gender agree.",
    },
    "aafak": {
        "canonical_slug": "aafaq",
        "basis": "curated42 explicitly identifies the same name; Arabic form, origin, gender, and lexical sense agree.",
    },
    "aafia": {
        "canonical_slug": "aafiya",
        "basis": "The source record and curated Aafiya entry have the same Arabic lexical form عافية (diacritics normalized), origin, and gender; spelling is a transliteration variant.",
    },
}

# A missing curation/source is a hold, not evidence that a name is nonexistent.
MANUAL_HOLDS: dict[str, str] = {
    "aad": "No entry in the aggregated curated maps; hold for lexical/name-use source review.",
    "aabish": "Curated record marks عابش as a low-confidence uncertain form and asserts no meaning; hold pending better evidence.",
}

# Named sources are attached to records individually. These support lexical or direct
# textual claims only; they do NOT certify translations, naming frequency, or gender.
SOURCE_REFERENCES: dict[str, list[dict[str, Any]]] = {
    "aaban": [
        {
            "title": "آبان — Dehkhoda Dictionary",
            "publisher": "Vajehyab / Dehkhoda Dictionary",
            "url": "https://vajehyab.com/dehkhoda/%D8%A2%D8%A8%D8%A7%D9%86",
            "source_type": "lexical_dictionary",
            "supports": ["آبان as the eighth month of the Persian solar year"],
        }
    ],
    "aabid": [
        {
            "title": "عبد — The Arabic Lexicon (dictionary entries for عابد)",
            "publisher": "The Arabic Lexicon; includes historical Arabic-English lexicons",
            "url": "https://arabiclexicon.hawramani.com/%D8%B9%D8%A8%D8%AF/",
            "source_type": "lexical_dictionary",
            "supports": ["عابد as a worshipper/devout person; active-participle use"],
        }
    ],
    "aabida": [
        {
            "title": "عبد — The Arabic Lexicon (dictionary entries for عابدة)",
            "publisher": "The Arabic Lexicon; includes historical Arabic-English lexicons",
            "url": "https://arabiclexicon.hawramani.com/%D8%B9%D8%A8%D8%AF/",
            "source_type": "lexical_dictionary",
            "supports": ["عابدة as the feminine form of عابد; worshipper/devout person"],
        }
    ],
    "aabir": [
        {
            "title": "عابر — Lane's Arabic-English Lexicon",
            "publisher": "Lane's Lexicon",
            "url": "https://www.laneslexicon.com/word/%D8%B9%D8%A7%D8%A8%D8%B1",
            "source_type": "lexical_dictionary",
            "supports": ["عابر as a wayfarer, traveller, or person passing along a way"],
        }
    ],
    "aadam": [
        {
            "title": "Surah Al-Baqarah, verse 31",
            "publisher": "Quran.com",
            "url": "https://quran.com/en/al-baqarah/31-33",
            "source_type": "primary_religious_text",
            "supports": ["The Arabic personal name Adam (آدم) occurs in Qur'an 2:31"],
        }
    ],
    "aadil": [
        {
            "title": "عادل — Britannica English Arabic-English Dictionary",
            "publisher": "Britannica English, in collaboration with Merriam-Webster",
            "url": "https://arabic.britannicaenglish.com/en/%D8%B9%D8%A7%D8%AF%D9%84",
            "source_type": "lexical_dictionary",
            "supports": ["عادل as an adjective meaning just, equitable, fair, or honest"],
        }
    ],
    "aadila": [
        {
            "title": "عادلة — Britannica English Arabic-English Dictionary",
            "publisher": "Britannica English, in collaboration with Merriam-Webster",
            "url": "https://arabic.britannicaenglish.com/en/%D8%B9%D8%A7%D8%AF%D9%84%D8%A9",
            "source_type": "lexical_dictionary",
            "supports": ["عادلة as the feminine adjective meaning just, equitable, or fair"],
        }
    ],
    "aafaq": [
        {
            "title": "آفاق — Almaany English-Arabic Dictionary",
            "publisher": "Almaany",
            "url": "https://www.almaany.com/en/dict/ar-en/%D8%A2%D9%81%D8%A7%D9%82/",
            "source_type": "lexical_dictionary",
            "supports": ["آفاق as the plural of أفق; horizons, distant regions, or perspectives"],
        }
    ],
    "aafiya": [
        {
            "title": "عافية — Britannica English Arabic-English Dictionary",
            "publisher": "Britannica English, in collaboration with Merriam-Webster",
            "url": "https://arabic.britannicaenglish.com/en/%D8%B9%D8%A7%D9%81%D9%8A%D8%A9",
            "source_type": "lexical_dictionary",
            "supports": ["عافية as health, wellbeing, or vitality"],
        }
    ],
    "aafreen": [
        {
            "title": "آفرین — Dehkhoda Dictionary",
            "publisher": "Vajehyab / Dehkhoda Dictionary",
            "url": "https://vajehyab.com/dehkhoda/%D8%A2%D9%81%D8%B1%DB%8C%D9%86",
            "source_type": "lexical_dictionary",
            "supports": ["آفرین as praise, good wishes, blessing, or commendation"],
        }
    ],
    "aaftab": [
        {
            "title": "آفتاب — Dehkhoda Dictionary",
            "publisher": "Vajehyab / Dehkhoda Dictionary",
            "url": "https://vajehyab.com/dehkhoda/%D8%A2%D9%81%D8%AA%D8%A7%D8%A8",
            "source_type": "lexical_dictionary",
            "supports": ["آفتاب as sunlight or the sun"],
        }
    ],
    "aahoo": [
        {
            "title": "آهو — Dehkhoda Dictionary",
            "publisher": "Vajehyab / Dehkhoda Dictionary",
            "url": "https://vajehyab.com/dehkhoda/%D8%A2%D9%87%D9%88-2",
            "source_type": "lexical_dictionary",
            "supports": ["آهو as gazelle"],
        }
    ],
}


class BatchError(RuntimeError):
    """Raised when a batch cannot safely be built."""


def load_curations() -> tuple[Any, dict[str, tuple], dict[str, dict[str, str]]]:
    """Merge legacy maps plus the small v2 overlay; reject conflicting entries."""
    sys.path.insert(0, str(SCRIPT_DIR))
    builder = importlib.import_module("nv_build")
    modules = []
    for i in range(1, 56):
        module_name = "curated" if i == 1 else f"curated{i}"
        modules.append(importlib.import_module(module_name))

    curated: dict[str, tuple] = {}
    glosses: dict[str, dict[str, str]] = {}
    owners: dict[str, str] = {}
    for module in modules:
        glosses.update(module.GLOSSES)
        for slug, row in module.CUR.items():
            if slug in curated and curated[slug] != row:
                raise BatchError(f"Conflicting curated records for {slug}: {owners[slug]} and {module.__name__}")
            curated[slug] = row
            owners[slug] = module.__name__

    if len(curated) != 5493:
        raise BatchError(f"Expected 5,493 legacy curated entries, found {len(curated)}")
    overlay = importlib.import_module("v2_curated")
    glosses.update(overlay.GLOSSES)
    for slug, row in overlay.CUR.items():
        if slug in curated:
            raise BatchError(f"The v2 curation overlay duplicates legacy slug {slug}")
        curated[slug] = row
    builder.CUR = curated
    builder.GLOSSES = glosses
    return builder, curated, glosses


def source_name_files() -> list[Path]:
    """Return all source records, excluding only the three progress JSON files."""
    if not SOURCE_DIR.is_dir():
        raise BatchError(f"Source directory is missing: {SOURCE_DIR}")
    files = [p for p in SOURCE_DIR.glob("*.json") if p.name not in CONTROL_FILES]
    files.sort(key=lambda p: (p.stem.casefold(), p.stem))
    if len(files) != 6503:
        raise BatchError(
            f"Source-count reconciliation failed: expected 6,503 name records after excluding "
            f"three progress JSONs, found {len(files)}"
        )
    return files


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise BatchError(f"Invalid source JSON {path.name}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("data"), dict):
        raise BatchError(f"Source record {path.name} has no data object")
    return value


def normalize_script(value: Any) -> str:
    """Normalize Unicode combining marks, retaining the written lexical characters."""
    text = unicodedata.normalize("NFD", str(value or ""))
    return "".join(ch for ch in text if not unicodedata.category(ch).startswith("M"))


def source_identity(path: Path) -> dict[str, str]:
    wrapper = read_json(path)
    data = wrapper["data"]
    identity = data.get("identity") or {}
    etymology = data.get("etymology") or {}
    origin = etymology.get("primary_language") or (data.get("origin") or {}).get("primary_origin") or ""
    return {
        "lexical_form": str(etymology.get("lexical_form") or ""),
        "origin": str(origin),
        "gender": str(identity.get("gender") or "Unknown"),
        "display_name": str(data.get("name") or path.stem),
    }


def curated_identity(slug: str, curated: dict[str, tuple]) -> dict[str, str]:
    row = curated.get(slug)
    if row is None:
        return {"lexical_form": "", "origin": "", "gender": "Unknown", "display_name": slug}
    return {"lexical_form": str(row[0] or ""), "origin": str(row[6] or ""), "gender": str(row[7] or "Unknown"), "display_name": slug.capitalize()}


def confirm_alias(source_slug: str, target_slug: str, source_path: Path, curated: dict[str, tuple]) -> tuple[bool, str, str]:
    """Require a same-script, same-origin match; never merge on English gloss alone."""
    if target_slug not in curated:
        return False, "canonical target has no curated entry", ""
    original = source_identity(source_path)
    target = curated_identity(target_slug, curated)
    source_form = normalize_script(original["lexical_form"])
    target_form = normalize_script(target["lexical_form"])
    if not source_form or not target_form or source_form != target_form:
        return False, "source and target script forms do not match exactly after diacritic normalization", target["lexical_form"]
    if original["origin"].casefold() != target["origin"].casefold():
        return False, "source and target linguistic origins do not match", target["lexical_form"]
    source_gender = original["gender"].casefold()
    target_gender = target["gender"].casefold()
    if source_gender not in ("unknown", "not specified", "") and target_gender not in ("unknown", "not specified", "") and source_gender != target_gender:
        return False, "source and target gender labels conflict", target["lexical_form"]
    return True, "exact lexical-form and origin match; merge is based on identity, not gloss", target["lexical_form"]


def copy_refs(slug: str) -> list[dict[str, Any]]:
    refs = []
    for source in SOURCE_REFERENCES.get(slug, []):
        item = dict(source)
        item["accessed_on"] = ACCESS_DATE
        refs.append(item)
    return refs


def name_alias_objects(ledger: list[dict[str, str]], canonical_slug: str) -> list[dict[str, str]]:
    return [
        {
            "slug": row["source_slug"],
            "display_name": row["source_slug"].capitalize(),
            "status": row["status"],
            "reason": row["basis"],
        }
        for row in ledger
        if row.get("canonical_slug") == canonical_slug
    ]


def unique_spellings(slug: str, aliases: list[dict[str, str]]) -> list[str]:
    values = [slug.capitalize(), slug]
    for alias in aliases:
        values.extend([alias["display_name"], alias["slug"]])
    seen = set()
    result = []
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def quranic_status(slug: str, refs: list[dict[str, Any]]) -> dict[str, Any]:
    if slug == "aadam":
        quran_ref = next((r for r in refs if r.get("source_type") == "primary_religious_text"), None)
        return {
            "is_quranic_name": True,
            "quranic_reference": "Qur'an 2:31",
            "source_url": quran_ref["url"] if quran_ref else None,
            "note": "The verse names Adam. This supports the proper-name reference, not an independent etymology.",
        }
    return {
        "is_quranic_name": None,
        "quranic_reference": None,
        "source_url": None,
        "note": "Not assessed; this record makes no Quranic-name claim.",
    }


def sanitize_record(record: dict[str, Any], slug: str, curated: dict[str, tuple], glosses: dict[str, dict[str, str]], refs: list[dict[str, Any]], ledger: list[dict[str, str]]) -> dict[str, Any]:
    """Remove unsupported template prose and annotate source/review limitations."""
    data = record["data"]
    row = curated[slug]
    ar, ur, fa, hi, ps, gloss_key, origin, gender, root, _quranic, confidence, _note = row
    gloss = glosses[gloss_key]
    lexical_form = str(ar or ur or fa or hi or ps or "")
    aliases = name_alias_objects(ledger, slug)
    spellings = unique_spellings(slug, aliases)
    cited_titles = "; ".join(ref["title"] for ref in refs)
    source_label = "source" if len(refs) == 1 else "sources"
    article = "an" if origin[:1].casefold() in "aeiou" else "a"
    lexical_claim = f"{lexical_form} is {article} {origin} lexical form, and the cited source glosses it as {gloss['en']}."
    limitation = "The cited lexical source does not establish personal-name frequency, gender distribution, religious suitability, or translation quality."

    data["identity"]["alternate_spellings"] = spellings
    data["identity"]["search_variants"] = spellings
    data["identity"]["merged_aliases"] = aliases
    data["identity"]["name_status"] = "lexical form source-supported; personal-name attestation not independently established in the cited sources"
    if gender == "Unknown":
        data["identity"]["gender_confidence"] = "unknown"
        data["identity"]["gender_note"] = "No personal-name gender classification is asserted; the cited lexical source does not establish name-use gender."
    else:
        data["identity"]["gender_confidence"] = "provisional"
        data["identity"]["gender_note"] = "Provisional gender label retained from the local curation; the cited dictionary verifies the lexical form, not population-level given-name gender."

    data["core_meaning"]["short_meaning"] = gloss["en"]
    data["core_meaning"]["primary_meaning"] = gloss["en"]
    data["core_meaning"]["secondary_meanings"] = []
    data["core_meaning"]["literal_meaning"] = gloss["en"]
    data["core_meaning"]["extended_meaning"] = gloss["en"]
    data["core_meaning"]["meaning_explanation"] = f"{lexical_claim} {limitation}"
    data["core_meaning"]["meaning_confidence"] = "source_supported"

    root_text = str(root or "")
    if slug == "aadam":
        root_status = "Proper name; no separate lexical root or name etymology is asserted."
    elif origin == "Arabic" and "root" in root_text.casefold():
        root_status = root_text
    elif origin == "Persian":
        root_status = "Persian lexical item; no additional root analysis asserted."
    else:
        root_status = "No additional root analysis asserted."
    data["etymology"].update({
        "primary_language": origin,
        "lexical_form": lexical_form,
        "transliteration": slug,
        "romanization": slug,
        "root_status": root_status,
        "etymological_meaning": [gloss["en"]],
        "etymology_explanation": f"The cited reference(s) support the lexical form {lexical_form} in {origin}. No additional derivation is asserted.",
        "etymology_confidence": "source_supported",
        "false_etymology_warning": "Do not infer a personal-name etymology beyond the cited lexical evidence.",
    })

    data["language"].update({
        "primary": origin,
        "associated_languages": [],
        "language_notes": {origin: f"Named lexical {source_label}: {cited_titles}. Other-language forms are not independently verified."},
        "language_confidence": "source_supported",
    })
    data["origin"].update({
        "primary_origin": origin,
        "origin_type": "lexical_language",
        "origin_confidence": "source_supported",
        "origin_explanation": f"The cited lexical source identifies {lexical_form} as {article} {origin} form. This does not by itself establish the origin or frequency of the spelling as a personal name.",
        "cultural_transmission": [],
    })
    data["religion"].update({
        "primary_association": "Not established by the cited lexical source",
        "religion": "not_assessed",
        "religion_confidence": "not_assessed",
        "religious_status": "No religious classification asserted",
        "religious_explanation": "Linguistic origin and a positive lexical meaning do not establish religious affiliation, permissibility, or recommendation.",
        "quranic_status": quranic_status(slug, refs),
        "hadith_status": {"direct_reference": None, "reference": None, "note": "Not assessed; no claim made."},
        "prophetic_status": {"prophet_association": None, "reference": None, "note": "Not assessed; no claim made."},
        "companion_status": {"known_companion_association": None, "reference": None, "note": "Not assessed; no claim made."},
    })
    data["islamic_naming_context"].update({
        "can_be_used_by_muslims": None,
        "context": "Religious suitability is not assessed in this lexical record.",
        "interpretation": "No religious ruling or recommendation is asserted.",
        "important_distinction": "A language origin or lexical meaning alone does not establish Quranic status or religious suitability.",
    })
    data["cultural_context"].update({
        "primary_cultural_associations": [],
        "cultural_meaning": "No name-specific cultural meaning is asserted beyond the cited lexical gloss.",
        "place_name_significance": None,
        "personal_name_interpretation": None,
        "interpretation_warning": "Symbolic or cultural interpretation requires a separate source and is not included as fact.",
    })
    data["semantic_field"].update({
        "primary_semantic_domain": gloss["en"],
        "related_concepts": [],
        "semantic_relationship": "Only the cited lexical gloss is asserted; no extended semantic associations are added.",
    })
    data["spiritual_meaning"].update({
        "status": "not_assessed",
        "meaning": None,
        "is_direct_religious_definition": False,
        "note": "No spiritual interpretation is added without a named religious source.",
    })
    data["personality_associations"].update({
        "status": "not_asserted",
        "traits": [],
        "note": "No personality traits are inferred from a name's lexical meaning.",
    })

    translations = data["translations"]
    for lang, block in translations.items():
        if not isinstance(block, dict):
            continue
        block["long_meaning"] = None
        if lang == "english" and block.get("meaning"):
            block["meaning"] = gloss["en"]
            block["translation_status"] = "source_supported_lexical_gloss"
            block["review_note"] = "The cited dictionary supports this English lexical gloss; it does not establish name-use or other-language translation quality."
        elif block.get("meaning"):
            block["translation_status"] = "draft_needs_native_review"
            block["review_note"] = "Editorial draft; not supported by a named translation source or native-speaker review."
        else:
            block["translation_status"] = "unverified"
            block["review_note"] = "No supported rendering supplied for this language."
    data["translation_quality"].update({
        "strategy": "source-backed English lexical gloss; other-language renderings are drafts",
        "warning": "Non-English translations have not been reviewed by native speakers or supported with named translation sources. Do not publish them as verified.",
        "confidence": "requires_native_review",
        "native_review_required": True,
        "named_translation_source_present": False,
    })

    data["pronunciation"].update({
        "romanized": data["name"],
        "ipa": None,
        "approximation_note": "The source spelling is preserved; pronunciation and IPA have not been independently verified.",
        "urdu": None,
        "persian": None,
        "hindi": None,
        "pashto": None,
    })
    data["name_variants"].update({
        "romanized_variants": spellings,
        "script_variants": [lexical_form] if lexical_form else [],
        "variant_notes": "Only reviewed same-lexeme aliases are listed; generic spelling simplifications are omitted.",
        "do_not_merge_with": data["name_variants"].get("do_not_merge_with", []),
    })
    data["historical_context"].update({
        "known_linguistic_history": [],
        "historical_person_association": "Adam is named in Qur'an 2:31." if slug == "aadam" else None,
        "historical_event_association": None,
        "historical_claim_confidence": "not_assessed",
        "editorial_note": "No historical person or event is added unless explicitly supported by a cited source.",
    })
    data["modern_usage"].update({
        "status": "not_assessed; frequency data required",
        "usage_regions": [],
        "regional_usage_note": "No regional or popularity claim is made without a defined name-frequency dataset.",
        "modern_relevance": None,
        "social_media_trend": None,
        "popularity_claim": None,
    })
    data["name_story"].update({
        "type": "not_provided",
        "story": None,
        "is_fictional": None,
    })

    data["faq"] = [
        {"question": f"What does {data['name']} mean?", "answer": f"The cited dictionary glosses {lexical_form} as {gloss['en']}."},
        {"question": f"What is the linguistic origin of {data['name']}?", "answer": f"The cited lexical source identifies the form as {origin}. It does not establish name frequency."},
        {"question": f"Is {data['name']} a Quranic name?", "answer": ("Adam is named in Qur'an 2:31; this confirms the proper-name reference, not an etymology." if slug == "aadam" else "Not assessed. This record makes no Quranic-name claim." )},
        {"question": f"Are the translations for {data['name']} verified?", "answer": "No. Non-English renderings are drafts that require native-speaker review."},
        {"question": f"Is the gender label for {data['name']} confirmed?", "answer": ("No gender is asserted." if gender == "Unknown" else "The label is provisional; the cited dictionary supports the lexical form, not name-use gender." )},
    ]

    data["seo"].update({
        "title": f"{data['name']} Name Meaning — {origin} Lexical Source",
        "meta_description": f"{data['name']} ({lexical_form}) is glossed as {gloss['en']} in the cited {origin} lexical source. Non-English translations require native review.",
        "h1": f"{data['name']} name meaning and lexical source",
        "focus_keyword": f"{data['name']} meaning",
        "secondary_keywords": [f"{data['name']} name meaning", f"{data['name']} origin", f"{data['name']} pronunciation"],
        "search_intents": ["lexical meaning", "origin", "source verification", "pronunciation"],
        "description_paragraph": f"{lexical_claim} {limitation}",
        "editorial_seo_rule": "Prioritize cited lexical information; do not infer religious, popularity, or name-use claims from keywords.",
    })
    data["seo_content"].update({
        "intro": lexical_claim,
        "meaning_section": f"Cited gloss: {gloss['en']}.",
        "origin_section": f"Language of the cited lexical entry: {origin}.",
        "islam_section": "Religious suitability and Quranic status are not inferred from the lexical gloss.",
        "cultural_section": "No name-specific cultural usage claim is made in this draft.",
        "pronunciation_section": "No IPA transcription is supplied without a phonetic source.",
    })
    data["content_quality"].update({
        "overall_status": "draft_pending_editorial_and_native_review",
        "linguistic_authenticity": "lexical_source_attached",
        "etymological_authenticity": "only_cited_claims_retained",
        "meaning_authenticity": "dictionary_supported_lexical_gloss",
        "translation_quality": "requires_native_review",
        "religious_claim_safety": "no_religious_suitability_claim_asserted",
        "historical_claim_safety": "no_unsupported_history_asserted",
        "cultural_accuracy": "no_name_specific_cultural_claim_asserted",
        "originality": "not_independently_assessed",
        "ai_hallucination_risk": "not_independently_assessed",
        "unsupported_claims_removed": [
            "uncited religious classification", "uncited regional and popularity claims", "generic cultural transmission claims",
            "symbolic personality/spiritual prose", "invented pronunciation details", "padded name story", "unsourced translations marked verified",
        ],
    })
    data["evidence"].update({
        "core_claims": [
            {"claim": f"{lexical_form} is a {origin} lexical form", "evidence_type": "named_dictionary_or_primary_text", "confidence": "source_supported"},
            {"claim": f"The cited lexical gloss is {gloss['en']}", "evidence_type": "named_dictionary_or_primary_text", "confidence": "source_supported"},
        ],
        "source_references": refs,
        "citation_status": "named_source_attached_for_lexical_claims",
        "limitations": ["Sources do not establish name popularity or gender distribution.", "Non-English translations require native-speaker review.", "Religious suitability is not assessed."],
        "claims_requiring_external_dataset": ["Personal-name popularity", "Country rankings", "Modern naming frequency", "Celebrity usage", "Social-media trends"],
    })
    data["provenance"].update({
        "verified_or_verifiable_fields": ["cited lexical form", "English lexical gloss"],
        "interpretive_fields": ["spiritual meaning", "personality associations", "name story"],
        "dataset_required_fields": ["gender distribution", "popularity", "regional rankings", "modern frequency", "celebrity usage"],
        "generated_content_policy": "Generated prose is limited to cited lexical claims and explicit review limitations.",
    })
    data["structured_data"].update({
        "alternateName": spellings,
        "description": f"{data['name']}: {origin} lexical form {lexical_form}; cited gloss: {gloss['en']}.",
        "inLanguage": [origin],
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Lexical origin", "value": origin},
            {"@type": "PropertyValue", "name": "Cited lexical gloss", "value": gloss["en"]},
            {"@type": "PropertyValue", "name": "Editorial status", "value": "Draft; translations require native review"},
        ],
    })
    data["accessibility"].update({
        "primary_language": "en",
        "rtl_languages_present": bool(origin == "Arabic" or any(ord(ch) >= 0x0600 and ord(ch) <= 0x06FF for ch in lexical_form)),
        "rtl_languages": ["ar"] if origin == "Arabic" else [],
        "screen_reader_description": f"{data['name']}; {origin} lexical form {lexical_form}; cited gloss {gloss['en']}.",
    })
    data["editorial_validation"].update({
        "name_identity_checked": False,
        "origin_checked": True,
        "meaning_checked": True,
        "language_checked": True,
        "religious_claims_checked": False,
        "translation_checked": False,
        "historical_claims_checked": False,
        "popularity_verified": False,
        "celebrity_verified": False,
        "real_person_story_verified": False,
        "numerology_verified": False,
        "lucky_attributes_verified": False,
        "ready_for_publication": False,
        "source_citations_present": bool(refs),
        "publication_blockers": [
            "Personal-name attestation/gender not independently sourced where applicable",
            "Non-English translations require qualified native-speaker review",
            "Religious suitability is not assessed",
        ],
    })
    data["timestamps"]["created_at"] = f"{ACCESS_DATE}T00:00:00.000Z"
    data["timestamps"]["updated_at"] = f"{ACCESS_DATE}T00:00:00.000Z"
    return record


def load_csv(path: Path, fieldnames: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_progress() -> dict[str, Any] | None:
    if not PROGRESS_JSON.exists():
        return None
    return json.loads(PROGRESS_JSON.read_text(encoding="utf-8"))


def write_markdown_report(manifest: dict[str, Any]) -> str:
    rows = manifest["entries"]
    created = [r for r in rows if r["outcome"] == "CREATED"]
    aliases = [r for r in rows if r["outcome"].startswith("MERGED")]
    holds = [r for r in rows if r["outcome"].startswith("HOLD")]
    lines = [
        f"# v2 Islamic-name batch {manifest['batch_number']:03d}",
        "",
        f"- Source entries reviewed: **{manifest['source_entries_reviewed']}**",
        f"- JSON records created: **{manifest['json_records_created']}**",
        f"- Aliases merged: **{manifest['aliases_merged']}**",
        f"- Held for review: **{manifest['source_holds']}**",
        "",
        "Named dictionary/primary-text references are included in each generated JSON record and support only the listed lexical claims. All non-English translations remain drafts pending native-speaker review; no record is marked ready for publication.",
        "",
        "## Records created",
        "",
        "| Source name | Output | Meaning gloss |",
        "|---|---|---|",
    ]
    for row in created:
        lines.append(f"| `{row['source_slug']}` | `{row['output_file']}` | {row['meaning'] or '—'} |")
    lines.extend(["", "## Same-name aliases", "", "| Source spelling | Merged into | Disposition |", "|---|---|---|"])
    for row in aliases:
        lines.append(f"| `{row['source_slug']}` | `{row['canonical_slug']}` | `{row['outcome']}` — {row['reason']} |")
    lines.extend(["", "## Source holds", "", "| Source name | Reason |", "|---|---|"])
    for row in holds:
        lines.append(f"| `{row['source_slug']}` | {row['reason']} |")
    lines.append("")
    return "\n".join(lines)


def build_batch(requested_batch: int | None = None) -> dict[str, Any]:
    builder, curated, glosses = load_curations()
    source_files = source_name_files()
    progress = load_progress()
    if progress:
        start = int(progress["next_source_index"])
        next_batch = int(progress["next_batch_number"])
        if requested_batch is not None and requested_batch != next_batch:
            raise BatchError(f"Progress requires batch {next_batch}; requested {requested_batch}")
        batch_number = next_batch
    else:
        start = 0
        batch_number = 1
        if requested_batch not in (None, 1):
            raise BatchError("The first v2 batch must be batch 1")
    if start >= len(source_files):
        raise BatchError("All source-name records have already been reviewed")

    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    batch_path = BATCH_DIR / f"batch_{batch_number:03d}.json"
    if batch_path.exists():
        raise BatchError(f"Batch manifest already exists: {batch_path}")

    paths = source_files[start : start + BATCH_SIZE]
    alias_fields = ["source_slug", "canonical_slug", "source_script", "canonical_script", "origin", "basis", "status", "batch_id", "output_file"]
    hold_fields = ["batch_id", "source_slug", "display_name", "reason", "source_file"]
    alias_rows = load_csv(ALIAS_LEDGER, alias_fields)
    hold_rows = load_csv(HOLD_LEDGER, hold_fields)
    known_aliases = {r.get("source_slug", "") for r in alias_rows}
    new_aliases: list[dict[str, str]] = []
    new_holds: list[dict[str, str]] = []
    candidate_records: list[tuple[str, dict[str, Any], list[dict[str, Any]]]] = []
    entries: list[dict[str, Any]] = []
    batch_id = f"v2-{batch_number:03d}"

    for source_path in paths:
        slug = source_path.stem.casefold()
        try:
            wrapper = read_json(source_path)
        except BatchError as exc:
            reason = str(exc)
            new_holds.append({"batch_id": batch_id, "source_slug": slug, "display_name": slug.capitalize(), "reason": reason, "source_file": source_path.name})
            entries.append({"source_slug": slug, "display_name": slug.capitalize(), "outcome": "HOLD_SOURCE_JSON_ERROR", "canonical_slug": "", "output_file": "", "meaning": "", "reason": reason})
            continue

        if slug in ALIASES:
            decision = ALIASES[slug]
            canonical_slug = decision["canonical_slug"]
            okay, check_note, target_script = confirm_alias(slug, canonical_slug, source_path, curated)
            if not okay:
                reason = f"Alias candidate not merged: {check_note}. Manual evidence review required."
                new_holds.append({"batch_id": batch_id, "source_slug": slug, "display_name": slug.capitalize(), "reason": reason, "source_file": source_path.name})
                entries.append({"source_slug": slug, "display_name": slug.capitalize(), "outcome": "HOLD_ALIAS_REVIEW", "canonical_slug": canonical_slug, "output_file": "", "meaning": "", "reason": reason})
                continue
            source_form = source_identity(source_path)["lexical_form"]
            output_file = f"{canonical_slug}.json" if (OUTPUT_DIR / f"{canonical_slug}.json").exists() or canonical_slug in {p[0] for p in candidate_records} or any(p.stem.casefold() == canonical_slug for p in paths) else ""
            row = {
                "source_slug": slug,
                "canonical_slug": canonical_slug,
                "source_script": source_form,
                "canonical_script": target_script,
                "origin": source_identity(source_path)["origin"],
                "basis": f"{decision['basis']} {check_note}",
                "status": "MERGED" if output_file else "MERGED_PENDING_TARGET",
                "batch_id": batch_id,
                "output_file": output_file,
            }
            if slug in known_aliases:
                raise BatchError(f"Alias {slug} is already present in alias ledger")
            new_aliases.append(row)
            entries.append({
                "source_slug": slug,
                "display_name": wrapper["data"].get("name", slug.capitalize()),
                "outcome": row["status"],
                "canonical_slug": canonical_slug,
                "output_file": output_file,
                "meaning": "",
                "reason": row["basis"],
            })
            continue

        if slug in MANUAL_HOLDS:
            reason = MANUAL_HOLDS[slug]
            new_holds.append({"batch_id": batch_id, "source_slug": slug, "display_name": wrapper["data"].get("name", slug.capitalize()), "reason": reason, "source_file": source_path.name})
            entries.append({"source_slug": slug, "display_name": wrapper["data"].get("name", slug.capitalize()), "outcome": "HOLD_SOURCE_REVIEW", "canonical_slug": "", "output_file": "", "meaning": "", "reason": reason})
            continue

        if slug not in curated:
            reason = "No entry in the aggregated curated maps; hold for named lexical/name-use source review."
            new_holds.append({"batch_id": batch_id, "source_slug": slug, "display_name": wrapper["data"].get("name", slug.capitalize()), "reason": reason, "source_file": source_path.name})
            entries.append({"source_slug": slug, "display_name": wrapper["data"].get("name", slug.capitalize()), "outcome": "HOLD_NO_CURATION", "canonical_slug": "", "output_file": "", "meaning": "", "reason": reason})
            continue

        c = curated[slug]
        gloss_key, origin, confidence = c[5], c[6], c[10]
        if not gloss_key or gloss_key == "uncertain_form" or gloss_key not in glosses or confidence not in ("high", "medium") or origin in ("Unknown", ""):
            reason = "Curation does not support a publishable lexical identification; held without asserting a meaning."
            new_holds.append({"batch_id": batch_id, "source_slug": slug, "display_name": wrapper["data"].get("name", slug.capitalize()), "reason": reason, "source_file": source_path.name})
            entries.append({"source_slug": slug, "display_name": wrapper["data"].get("name", slug.capitalize()), "outcome": "HOLD_LOW_CONFIDENCE", "canonical_slug": "", "output_file": "", "meaning": "", "reason": reason})
            continue

        refs = copy_refs(slug)
        if not refs:
            reason = "No named lexical/primary-text citation has been added; hold rather than label the entry verified."
            new_holds.append({"batch_id": batch_id, "source_slug": slug, "display_name": wrapper["data"].get("name", slug.capitalize()), "reason": reason, "source_file": source_path.name})
            entries.append({"source_slug": slug, "display_name": wrapper["data"].get("name", slug.capitalize()), "outcome": "HOLD_NO_NAMED_SOURCE", "canonical_slug": "", "output_file": "", "meaning": "", "reason": reason})
            continue

        if (OUTPUT_DIR / f"{slug}.json").exists():
            raise BatchError(f"Refusing to overwrite existing v2 record {slug}.json")
        record = builder.build(slug, wrapper["data"])
        candidate_records.append((slug, record, refs))
        entries.append({
            "source_slug": slug,
            "display_name": wrapper["data"].get("name", slug.capitalize()),
            "outcome": "CREATED",
            "canonical_slug": slug,
            "output_file": f"{slug}.json",
            "meaning": glosses[gloss_key]["en"],
            "reason": "Named source attached for the lexical claim; other translations and name-use details remain under review.",
        })

    # Apply both new and earlier pending aliases to any canonical page built in this batch.
    all_alias_rows = alias_rows + new_aliases
    created_slugs = {slug for slug, _record, _refs in candidate_records}
    previously_emitted = {p.stem.casefold() for p in OUTPUT_DIR.glob("*.json")}
    available_targets = created_slugs | previously_emitted
    for row in all_alias_rows:
        if row.get("canonical_slug") in available_targets:
            row["status"] = "MERGED"
            row["output_file"] = f"{row['canonical_slug']}.json"
        elif row.get("status") == "MERGED":
            row["status"] = "MERGED_PENDING_TARGET"
            row["output_file"] = ""

    for slug, record, refs in candidate_records:
        aliases_for_record = all_alias_rows
        clean = sanitize_record(record, slug, curated, glosses, refs, aliases_for_record)
        write_json(OUTPUT_DIR / f"{slug}.json", clean)

    # Existing pending aliases can become resolved when a future batch emits their target.
    write_csv(ALIAS_LEDGER, all_alias_rows, alias_fields)
    hold_rows.extend(new_holds)
    write_csv(HOLD_LEDGER, hold_rows, hold_fields)

    source_end = start + len(paths)
    old_counts = progress or {}
    counts = Counter(r["outcome"] for r in entries)
    created_count = counts["CREATED"]
    alias_count = sum(count for outcome, count in counts.items() if outcome.startswith("MERGED"))
    hold_count = sum(count for outcome, count in counts.items() if outcome.startswith("HOLD"))
    manifest = {
        "batch_id": batch_id,
        "batch_number": batch_number,
        "date": ACCESS_DATE,
        "source_directory": "upgrading/names_upgraded/islamic",
        "destination_directory": "upgrades-namesv2/islamic",
        "batch_size": BATCH_SIZE,
        "source_cursor_start": start,
        "source_cursor_end_exclusive": source_end,
        "source_entries_reviewed": len(paths),
        "json_records_created": created_count,
        "aliases_merged": alias_count,
        "source_holds": hold_count,
        "entries": entries,
        "named_source_references_by_record": {slug: refs for slug, _record, refs in candidate_records},
        "structural_validation_note": "Run nv_validate.py separately; that validator checks structure only, not factual authenticity.",
        "translation_status_note": "Non-English translations are drafts requiring native-speaker review; no record is marked ready for publication.",
    }
    write_json(batch_path, manifest)
    report = write_markdown_report(manifest)
    (BATCH_DIR / f"batch_{batch_number:03d}.md").write_text(report, encoding="utf-8")

    total_reviewed = int(old_counts.get("source_entries_reviewed_total", 0)) + len(paths)
    total_created = int(old_counts.get("json_records_created_total", 0)) + created_count
    total_aliases = int(old_counts.get("aliases_merged_total", 0)) + alias_count
    total_holds = int(old_counts.get("source_holds_total", 0)) + hold_count
    next_name = source_files[source_end].stem if source_end < len(source_files) else None
    new_progress = {
        "source_directory": "upgrading/names_upgraded/islamic",
        "destination_directory": "upgrades-namesv2/islamic",
        "source_json_files_including_controls": 6506,
        "source_name_records": 6503,
        "excluded_control_files": sorted(CONTROL_FILES),
        "curated_entries": len(curated),
        "batch_size": BATCH_SIZE,
        "last_completed_batch": batch_number,
        "next_batch_number": batch_number + 1,
        "next_source_index": source_end,
        "next_source_slug": next_name,
        "source_entries_reviewed_total": total_reviewed,
        "json_records_created_total": total_created,
        "aliases_merged_total": total_aliases,
        "source_holds_total": total_holds,
        "updated_on": ACCESS_DATE,
    }
    write_json(PROGRESS_JSON, new_progress)
    PROGRESS_MD.write_text(
        "# v2 Islamic-name progress\n\n"
        f"- Batch size: **{BATCH_SIZE} source names per batch**\n"
        f"- Source records: **6,503** (6,506 JSON files minus three progress-control JSON files)\n"
        f"- Curated entries across local maps: **{len(curated):,}**\n"
        f"- Last completed batch: **{batch_number:03d}**\n"
        f"- Source names reviewed: **{total_reviewed:,}**\n"
        f"- v2 JSON records created: **{total_created:,}**\n"
        f"- Same-name aliases merged/logged: **{total_aliases:,}**\n"
        f"- Source holds: **{total_holds:,}**\n"
        f"- Next source index: **{source_end}** (`{next_name or 'complete'}`)\n\n"
        "A source hold is not a claim that a name does not exist. Alias decisions require matching lexical forms and explicit curation evidence. Non-English translations remain drafts until native-speaker review.\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=int, default=None, help="Expected next batch number (must match progress.json)")
    args = parser.parse_args()
    try:
        manifest = build_batch(args.batch)
    except BatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        f"{manifest['batch_id']}: reviewed {manifest['source_entries_reviewed']} source names; "
        f"created {manifest['json_records_created']} JSON records; "
        f"logged {manifest['aliases_merged']} aliases; held {manifest['source_holds']} for review."
    )
    print(f"Output: {OUTPUT_DIR}")
    manifest_path = BATCH_DIR / ("batch_%03d.json" % manifest["batch_number"])
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
