#!/usr/bin/env python3
"""Build and validate a curated batch of super-2.0 Islamic name records.

The builder copies the repository's current super-2.0 template, fills every
existing data section from a reviewed manifest, and refuses to overwrite an
unrelated record or add any exact normalized alias/script collision.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "upgrading/name_batches/demand_2026-10.json"
DEFAULT_DATASET = REPO_ROOT / "upgrading/names_upgraded/islamic"
DEFAULT_TEMPLATE = DEFAULT_DATASET / "aabid.json"

ARABIC_CHAR_MAP = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي",
    "ی": "ي", "ے": "ي", "ئ": "ي", "ؤ": "و",
    "ة": "ه", "ہ": "ه", "ھ": "ه", "ک": "ك",
})
LATIN_CHAR_MAP = str.maketrans({
    "ł": "l", "ø": "o", "đ": "d", "ð": "d", "þ": "th",
    "æ": "ae", "œ": "oe", "ı": "i", "ß": "ss",
})
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

AUTHENTICITY_FLAGS: dict[str, list[str]] = {
    "yusra": ["root_has_multiple_contextual_senses"],
    "yumna": ["blessing_is_a_lexical_association_not_a_promise", "Nameberry_page_labelled_AI_written_used_only_for_scoped_popularity_data"],
    "samiha": ["personality_traits_not_inferred_from_name"],
    "sariya": ["unsupported_S-R-A_root_label_rejected", "same_spelling_has_separate_lexical_histories"],
    "abyan": ["comparative_not_superlative", "gender_distribution_not_quantified"],
    "tasmir": ["popular_roman_spelling_is_not_strict_transliteration_of_th", "direct_Quranic_name_status_not_claimed"],
    "salwa": ["multiple_contextual_lexical_senses", "unsupported_S-L-A_root_label_rejected"],
    "salsabil": ["deeper_etymology_uncertain", "Quranic_referent_is_a_spring_not_a_person"],
    "alparslan": ["Turkish_origin_not_Quranic_or_Arabic"],
    "duru": ["Turkish_origin_not_Quranic_or_religiously_specific"],
}

FALSE_ETYMOLOGY_WARNINGS: dict[str, str] = {
    "sariya": "Some baby-name pages assign S-R-A. Independent Arabic lexical entries place the night-travel/cloud form under س ر ي (s-r-y); the S-R-A label and a direct Qur'anic-name claim are not adopted.",
    "tasmir": "The searched spelling Tasmir represents تَثْمِير; its Arabic first consonant is ث (th), not س (s). Do not infer the root س م ر from the Roman spelling.",
    "salwa": "This record uses س ل و (s-l-w), supported by Arabic lexical entries, and does not copy the S-L-A label from some name sites.",
    "salsabil": "The Qur'anic referent is clear, but the deeper etymology is uncertain/probabilistic. No triliteral root or literal Arabic compound derivation is asserted.",
}

LONG_GLOSS_TEMPLATES = {
    "urdu": "{name} کے لغوی معنی {meaning} ہیں۔ یہ ترجمہ ابتدائی مسودہ ہے اور مقامی لسانی جائزے کا محتاج ہے۔",
    "persian": "معنای لغوی {name} در این مدخل «{meaning}» است؛ این برگردان پیش‌نویس است و به بازبینی بومی نیاز دارد.",
    "hindi": "{name} का शब्दार्थ यहाँ {meaning} दिया गया है। यह अनुवाद प्रारूप है और स्थानीय भाषायी समीक्षा आवश्यक है।",
    "pashto": "د {name} لغوي مانا «{meaning}» ده؛ دا د ژباړې مسوده ده او د اصلي ژبې ویونکي بیاکتنې ته اړتیا لري.",
    "arabic": "المعنى اللغوي لـ{name} في هذا السجل هو «{meaning}»؛ وهذه صياغة أولية تحتاج إلى مراجعة لغوية.",
}


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def normalize_latin(value: str) -> str:
    """Normalize Latin-script name spellings for exact alias comparison."""
    value = unicodedata.normalize("NFKD", value.translate(LATIN_CHAR_MAP)).casefold()
    output: list[str] = []
    for char in value:
        if unicodedata.combining(char):
            continue
        if char.isascii() and char.isalnum():
            output.append(char)
    return "".join(output)


def normalize_script(value: str) -> str:
    """Normalize script forms without erasing Indic vowel signs.

    Arabic diacritics and tatweel are ignored because their presence varies
    across equivalent spellings. Marks in other writing systems are preserved;
    dropping Devanagari vowel signs, for example, creates false matches.
    """
    value = unicodedata.normalize("NFC", value.translate(ARABIC_CHAR_MAP)).casefold()
    output: list[str] = []
    for char in value:
        if char == "ـ":
            continue
        category = unicodedata.category(char)
        if category.startswith("M") and "ARABIC" in unicodedata.name(char, ""):
            continue
        if char.isalnum() or category.startswith("M"):
            output.append(char)
    return "".join(output)


def is_latin_text(value: str) -> bool:
    return any(
        "LATIN" in unicodedata.name(char, "")
        for char in value
        if char.isalpha()
    )


def normalized_keys(value: str) -> set[tuple[str, str]]:
    """Return namespace/value pairs so unrelated writing systems do not mix."""
    value = value.strip()
    if not value:
        return set()
    keys: set[tuple[str, str]] = set()
    if is_latin_text(value):
        normalized = normalize_latin(value)
        if normalized:
            keys.add(("latin", normalized))
    # Include a separate non-Latin normalization for mixed-script entries.
    if any(ord(char) > 127 and char.isalpha() for char in value):
        normalized = normalize_script(value)
        if normalized:
            keys.add(("script", normalized))
    if not keys:
        normalized = normalize_script(value)
        if normalized:
            keys.add(("script", normalized))
    return keys


def _append_string(target: list[str], value: Any) -> None:
    if isinstance(value, str) and value.strip():
        target.append(value.strip())


def _append_strings(target: list[str], value: Any) -> None:
    if isinstance(value, str):
        _append_string(target, value)
    elif isinstance(value, list):
        for item in value:
            _append_string(target, item)


def extract_record_forms(record: dict[str, Any], filename_stem: str = "") -> list[str]:
    """Extract identity spellings and script renderings, not meanings/prose."""
    forms: list[str] = []
    _append_string(forms, filename_stem)
    _append_string(forms, record.get("name"))
    _append_string(forms, record.get("slug"))
    data = record.get("data", {})
    if not isinstance(data, dict):
        return list(dict.fromkeys(forms))

    _append_string(forms, data.get("name"))
    _append_string(forms, data.get("slug"))

    identity = data.get("identity", {})
    if isinstance(identity, dict):
        for key in (
            "display_name", "normalized_name", "alternate_spellings",
            "aliases", "romanized_variants", "search_variants",
            "searchable_spellings",
        ):
            _append_strings(forms, identity.get(key))

    variants = data.get("name_variants", {})
    if isinstance(variants, dict):
        for key in ("romanized_variants", "script_forms", "alternate_spellings"):
            _append_strings(forms, variants.get(key))

    etymology = data.get("etymology", {})
    if isinstance(etymology, dict):
        for key in ("lexical_form", "transliteration", "romanization"):
            _append_string(forms, etymology.get(key))

    pronunciation = data.get("pronunciation", {})
    if isinstance(pronunciation, dict):
        scripts = pronunciation.get("scripts", {})
        if isinstance(scripts, dict):
            for value in scripts.values():
                _append_string(forms, value)

    translations = data.get("translations", {})
    if isinstance(translations, dict):
        for translation in translations.values():
            if not isinstance(translation, dict):
                continue
            for key in ("name", "script", "display_name", "transliteration", "romanized"):
                _append_string(forms, translation.get(key))

    return list(dict.fromkeys(forms))


def load_dataset_records(dataset_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(dataset_dir.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Cannot parse dataset JSON {path}: {exc}") from exc
        if isinstance(value, dict) and isinstance(value.get("data"), dict):
            records.append((path, value))
    return records


def build_existing_index(
    records: Iterable[tuple[Path, dict[str, Any]]],
    excluded_stems: set[str] | None = None,
) -> dict[tuple[str, str], list[dict[str, str]]]:
    excluded_stems = excluded_stems or set()
    index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for path, record in records:
        if path.stem in excluded_stems:
            continue
        data = record.get("data", {})
        canonical = str(data.get("name") or record.get("name") or path.stem)
        for form in extract_record_forms(record, path.stem):
            for key in normalized_keys(form):
                hit = {"file": path.name, "canonical": canonical, "form": form}
                if hit not in index[key]:
                    index[key].append(hit)
    return index


def candidate_forms(record: dict[str, Any]) -> list[str]:
    return extract_record_forms(record, str(record.get("data", {}).get("slug", "")))


def check_batch_collisions(
    records: list[dict[str, Any]],
    dataset_index: dict[tuple[str, str], list[dict[str, str]]],
) -> list[str]:
    errors: list[str] = []
    batch_index: dict[tuple[str, str], tuple[str, str, str]] = {}
    for record in records:
        data = record["data"]
        slug = data["slug"]
        display_name = data["name"]
        for form in candidate_forms(record):
            for key in normalized_keys(form):
                previous = batch_index.get(key)
                if previous and previous[0] != slug:
                    errors.append(
                        f"In-batch collision: {display_name!r} form {form!r} "
                        f"normalizes to the same {key[0]} spelling as "
                        f"{previous[1]!r} (form {previous[2]!r})."
                    )
                else:
                    batch_index[key] = (slug, display_name, form)
                for hit in dataset_index.get(key, []):
                    errors.append(
                        f"Dataset collision: {display_name!r} form {form!r} "
                        f"matches {hit['file']} ({hit['canonical']!r}, "
                        f"indexed form {hit['form']!r})."
                    )
    return list(dict.fromkeys(errors))


def clean_primary_language(value: str) -> str:
    return value.split(" (", 1)[0].strip()


def scalar_leaf_count(value: Any) -> int:
    if isinstance(value, dict):
        return sum(scalar_leaf_count(item) for item in value.values())
    if isinstance(value, list):
        return sum(scalar_leaf_count(item) for item in value)
    return 1


def article_for(noun: str) -> str:
    return "an" if noun[:1].casefold() in {"a", "e", "i", "o", "u"} else "a"


def concise_metric(measurement: dict[str, Any]) -> str:
    region = measurement["region"]
    year = measurement["year"]
    rank = measurement.get("rank")
    category = measurement.get("category")
    births = measurement.get("births")
    percent = measurement.get("relative_interest_percent")
    source = measurement["source_title"]
    if percent is not None:
        return (
            f"{region}, {year}, {category} list: #{rank}, "
            f"{percent}% relative visitor-search interest ({source})"
        )
    suffix = f" among {category}" if category else ""
    births_text = f", {births:,} births" if isinstance(births, int) else ""
    return f"{region}, {year}: #{rank}{suffix}{births_text} ({source})"


def quranic_faq_answer(candidate: dict[str, Any]) -> str:
    q = candidate["quranic"]
    if q["is_quranic"]:
        return f"The lexical/scriptural form is directly attested, but not as a named person: {q['note']}"
    return f"It is not claimed as a Qur'anic personal name. {q['note']}"


def make_faq(candidate: dict[str, Any], primary_language: str) -> list[dict[str, str]]:
    name = candidate["name"]
    quran_answer = quranic_faq_answer(candidate)
    if candidate["gender"] == "Unisex":
        gender_answer = "The source records this name for boys and girls; a population-level gender split is not available."
    else:
        gender_answer = (
            f"The documented naming sources record {name} as a {candidate['gender'].lower()} name; "
            "actual use can vary by language and community."
        )
    root = candidate.get("root", "")
    if root:
        root_answer = f"The recorded Arabic root is {root} ({candidate.get('root_transliteration', '')})."
    else:
        root_answer = "No triliteral Arabic root is asserted for this name."
    metric_text = "; ".join(concise_metric(m) for m in candidate["popularity"]["measurements"])
    popularity_answer = f"Available scoped measure(s): {metric_text}. {candidate['popularity']['note']}"
    urdu = candidate["translations"]["urdu"]
    urdu_answer = (
        f"The draft Urdu rendering is {urdu['name']}; its gloss is {urdu['meaning']}. "
        "Localized translations have not had native-speaker review."
    )
    spelling_label = "Arabic" if primary_language == "Arabic" else primary_language
    language_article = article_for(primary_language)
    pronunciation_guide = re.sub(
        r"\s*\(approximate(?:;?[^)]*)?\)",
        "",
        candidate["pronunciation"]["guide"],
        flags=re.IGNORECASE,
    ).strip()
    return [
        {"q": f"What does {name} mean?", "a": candidate["primary_meaning"]},
        {"q": f"What is the origin of {name}?", "a": candidate["meaning_explanation"]},
        {"q": f"Is {name} {language_article} {primary_language} name?", "a": f"Yes. The recorded language/origin is {primary_language}; the source form is {candidate['script_form']}."},
        {"q": f"How is {name} written in {spelling_label}?", "a": candidate["script_form"]},
        {"q": f"Is {name} a Quranic name?", "a": quran_answer},
        {"q": f"Is {name} an Islamic name?", "a": f"{candidate['religious_status']} {candidate['religious_explanation']}"},
        {"q": f"How is {name} pronounced?", "a": f"An approximate romanized guide is {pronunciation_guide}. {candidate['pronunciation']['note']}"},
        {"q": f"Is {name} a boy's or girl's name?", "a": gender_answer},
        {"q": f"How popular is {name}?", "a": popularity_answer},
        {"q": f"What does {name} mean in Urdu?", "a": urdu_answer},
        {"q": f"What is the root of {name}?", "a": root_answer},
    ]


def build_translations(candidate: dict[str, Any], primary_language: str) -> dict[str, Any]:
    name = candidate["name"]
    translations: dict[str, Any] = {
        "english": {
            "name": name,
            "script": name,
            "meaning": candidate["short_meaning"],
            "long_meaning": candidate["primary_meaning"],
        }
    }
    for language in ("urdu", "persian", "hindi", "pashto", "arabic"):
        item = candidate["translations"][language]
        rendered = {
            "name": item["name"],
            "script": item["script"],
            "meaning": item["meaning"],
            "long_meaning": LONG_GLOSS_TEMPLATES[language].format(
                name=item["name"], script=item["script"], meaning=item["meaning"]
            ),
        }
        if language in {"pashto", "arabic"}:
            rendered["native_review_required"] = True
        translations[language] = rendered
    return translations


def build_popularity(candidate: dict[str, Any]) -> dict[str, Any]:
    by_region = []
    for measurement in candidate["popularity"]["measurements"]:
        by_region.append({
            "region": measurement["region"],
            "measure": measurement["measure"],
            "year": measurement["year"],
            "category": measurement.get("category"),
            "rank": measurement.get("rank"),
            "births": measurement.get("births"),
            "relative_interest_percent": measurement.get("relative_interest_percent"),
            "observation_period": measurement.get("observation_period"),
            "source_title": measurement["source_title"],
            "source": measurement["source_url"],
            "limitation": measurement["limitation"],
        })
    return {
        "status": "source_scoped_metrics_available",
        "render": True,
        "score": None,
        "by_region": by_region,
        "note": candidate["popularity"]["note"],
    }


def build_evidence(candidate: dict[str, Any]) -> dict[str, Any]:
    sources = []
    for source in candidate["evidence"]:
        sources.append(
            f"{source['title']} — {source['supports']} "
            f"Source: {source['url']} Limitation: {source['limitation']}"
        )
    method = (
        "The lexical/scriptural or language claim is separated from name-site glosses; "
        "name usage and popularity are checked separately. Every frequency figure retains "
        "its source, region, year, category, metric, and limitation. Candidate spellings, "
        "Romanized variants, source-script forms, and localized script renderings are "
        "checked against the existing dataset. Non-English glosses are drafts requiring "
        "native-speaker review."
    )
    return {"sources": sources, "verification_method": method}


def build_record(candidate: dict[str, Any], template: dict[str, Any], created_at: str) -> dict[str, Any]:
    record = copy.deepcopy(template)
    data = record["data"]
    name = candidate["name"]
    slug = candidate["slug"]
    primary_language = clean_primary_language(candidate["language"])
    language_article = article_for(primary_language)
    source_form = candidate["script_form"]
    quranic = candidate["quranic"]
    etymology_confidence = "MEDIUM" if slug == "salsabil" else candidate["meaning_confidence"]
    popularity = build_popularity(candidate)
    faq = make_faq(candidate, primary_language)
    translations = build_translations(candidate, primary_language)
    cultural_note = candidate["cultural_note"]

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
        "gender": candidate["gender"],
        "gender_confidence": candidate["gender_confidence"],
        "gender_note": (
            "The source records this name for boys and girls; no population-level gender split is asserted."
            if candidate["gender"] == "Unisex"
            else "Gender follows documented naming usage, not an inference from the word's meaning; usage can vary by community."
        ),
        "alternate_spellings": list(dict.fromkeys([name, slug, *candidate["aliases"]])),
        "name_status": "attested",
    }
    data["core_meaning"] = {
        "short_meaning": candidate["short_meaning"],
        "primary_meaning": candidate["primary_meaning"],
        "literal_meaning": candidate["literal_meaning"],
        "meaning_explanation": candidate["meaning_explanation"],
        "meaning_confidence": candidate["meaning_confidence"],
    }
    data["etymology"] = {
        "primary_language": primary_language,
        "lexical_form": source_form,
        "transliteration": candidate["transliteration"],
        "root": candidate["root"],
        "root_transliteration": candidate["root_transliteration"],
        "morphology": candidate["morphology"],
        "feminine_form": None,
        "etymological_meaning": candidate["short_meaning"],
        "root_family": [],
        "etymology_explanation": candidate["meaning_explanation"],
        "etymology_confidence": etymology_confidence,
        "false_etymology_warning": FALSE_ETYMOLOGY_WARNINGS.get(
            slug,
            "No derivation beyond the documented lexical analysis is asserted; unsupported name-site etymologies are not adopted.",
        ),
    }
    if primary_language == "Arabic":
        primary_note = f"Arabic is the language of the recorded form {source_form}."
        usage_note = "Other scripts are transliterations or localized glosses; they are not independent origins."
        associated_languages = ["Arabic"]
    else:
        primary_note = f"{name} is recorded as a {primary_language} name in that language's own script/orthography."
        usage_note = "Arabic, Urdu, Persian, Pashto, and Hindi forms in this record are transliterations or draft glosses, not evidence of another origin."
        associated_languages = [primary_language]
    if slug == "salsabil":
        primary_note = "The form is attested in Qur'anic Arabic; a dictionary source proposes a probable Aramaic/ultimately Akkadian etymology, so its deeper origin remains uncertain."
    data["language"] = {
        "primary": primary_language,
        "associated_languages": associated_languages,
        "language_notes": {"primary": primary_note, "usage": usage_note},
        "language_confidence": "MEDIUM" if slug == "salsabil" else candidate["meaning_confidence"],
    }
    origin_confidence = "MEDIUM" if slug == "salsabil" else candidate["meaning_confidence"]
    if slug == "salsabil":
        origin_label = "Qur'anic Arabic usage; deeper origin uncertain"
        origin_explanation = (
            "The form is attested as the spring's name in Qur'anic Arabic. A reference proposes "
            "a probable Aramaic, ultimately Akkadian, etymology; that proposal is not treated as settled."
        )
    else:
        origin_label = primary_language
        origin_explanation = (
            f"The recorded form and meaning are associated with {primary_language}. "
            "The evidence distinguishes linguistic origin from religious/cultural use."
        )
    data["origin"] = {
        "primary_origin": origin_label,
        "origin_type": "linguistic",
        "origin_confidence": origin_confidence,
        "origin_explanation": origin_explanation,
        "cultural_transmission": list(candidate["cultural_transmission"]),
    }
    data["religion"] = {
        "primary_association": candidate["religion_association"],
        "religion_confidence": "MEDIUM",
        "religious_status": candidate["religious_status"],
        "religious_explanation": candidate["religious_explanation"],
        "quranic_status": {
            "is_quranic": quranic["is_quranic"],
            "status": quranic["status"],
            "note": quranic["note"],
        },
        "hadith_status": {
            "status": "not_verified",
            "note": "No specific authentic hadith report establishing this name or a special virtue is cited; none is invented.",
        },
        "prophetic_status": {
            "status": "not_verified",
            "note": "No verified source establishing this as a prophet's personal name is cited.",
        },
        "companion_status": {
            "status": "not_verified",
            "note": "No companion attribution is asserted without a verified source.",
        },
    }
    data["islamic_naming_context"] = {
        "can_be_used_by_muslims": True,
        "context": candidate["religion_association"],
        "interpretation": candidate["cultural_interpretation"],
        "important_distinction": "This descriptive record is not a religious ruling. Muslim cultural use, linguistic origin, and direct Qur'anic attestation are separate claims.",
    }
    data["cultural_context"] = {
        "primary_cultural_associations": list(candidate["cultural_associations"]),
        "cultural_meaning": cultural_note,
        "personal_name_interpretation": candidate["cultural_interpretation"],
        "interpretation_warning": "A symbolic naming preference is distinct from dictionary meaning and is not a claim about a bearer's personality or future.",
    }
    data["semantic_field"] = {
        "primary_semantic_domain": candidate["semantic_domain"],
        "related_concepts": list(candidate["related_concepts"]),
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
        "note": "Numerology is not evidence-based and is not supplied in this record.",
    }
    data["lucky_attributes"] = {
        "status": "not_verified",
        "render": False,
        "lucky_number": None,
        "lucky_day": None,
        "lucky_colors": [],
        "lucky_stone": None,
        "ruling_planet": None,
    }
    data["translations"] = translations
    data["translation_quality"] = {
        "strategy": "source_language_gloss_with_localized_draft",
        "confidence": "MEDIUM",
        "native_review_required": True,
        "note": "The source-language core gloss is evidence-backed. All non-English localized meanings and script renderings are editorial drafts and require native-speaker review; transliteration does not establish a separate origin.",
    }
    if primary_language == "Arabic":
        pronunciation_scripts = {"arabic": source_form}
    else:
        pronunciation_scripts = {"arabic": candidate["translations"]["arabic"]["script"]}
    data["pronunciation"] = {
        "romanized": candidate["pronunciation"]["guide"],
        "ipa": None,
        "approximation_note": candidate["pronunciation"]["note"],
        "common_mispronunciation": candidate["pronunciation"]["common_mispronunciation"],
        "scripts": pronunciation_scripts,
    }
    script_forms = [source_form]
    hindi_form = candidate["translations"]["hindi"]["script"]
    if hindi_form not in script_forms:
        script_forms.append(hindi_form)
    data["name_variants"] = {
        "romanized_variants": list(candidate["aliases"]),
        "script_forms": script_forms,
        "variant_notes": (
            "Romanized forms reflect documented orthographic/transliteration variants. "
            "For Tasmir, the common searched spelling is not a strict transliteration of ث."
            if slug == "tasmir"
            else "Alternate spellings reflect orthographic or transliteration variants; they do not establish different etymologies or pronunciations."
        ),
        "do_not_merge_with": [],
    }
    data["related_names"] = []
    data["historical_context"] = {
        "status": candidate["historical_status"],
        "note": candidate["historical_note"],
    }
    data["modern_usage"] = {
        "status": "source_scoped_usage_data_available",
        "note": candidate["usage_note"],
    }
    data["popularity"] = popularity
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
    data["faq"] = faq
    keywords = [
        f"{name} meaning", f"{name} name meaning", f"{name} origin",
        f"{name} pronunciation", f"{name} name in Urdu",
    ]
    if primary_language == "Arabic":
        keywords.append(f"{name} Arabic name")
    data["seo"] = {
        "title": f"{name} Name Meaning, Origin & Usage",
        "meta_description": f"Explore the sourced meaning, origin, pronunciation, script, and regional usage evidence for {name}.",
        "meta_keywords": ", ".join(keywords),
        "description_paragraph": f"{name} is {language_article} {primary_language}-origin given name. This entry separates its lexical meaning, cultural and scriptural context, and source-scoped usage evidence.",
        "keywords": keywords,
        "focus_keyword": f"{name} meaning",
        "secondary_keywords": keywords[1:],
        "canonical_url": "",
        "seo_score": None,
        "seo_score_basis": "No composite SEO score is assigned; editorial and evidence quality are recorded separately.",
    }
    data["seo_content"] = {
        "intro_paragraph": f"{name} is {language_article} {primary_language}-origin given name. The entry explains its documented meaning and distinguishes linguistic origin, religious/scriptural status, and regional usage.",
        "body_summary": f"{candidate['primary_meaning']} {candidate['popularity']['note']}",
    }
    tag_origin = "#ArabicNames" if primary_language == "Arabic" else "#TurkishNames"
    data["social_tags"] = [f"#{name}", f"#{name}Meaning", "#NameMeaning", tag_origin]
    if primary_language == "Arabic":
        data["social_tags"].append("#IslamicNames")
    flags = list(AUTHENTICITY_FLAGS.get(slug, []))
    flags.append("localized_translations_require_native_review")
    flags.append("popularity_metrics_are_source_and_region_scoped")
    data["content_quality"] = {
        "tier1_verified": candidate["meaning_confidence"] == "HIGH",
        "authenticity_flags": flags,
        "fabricated_content_removed": True,
        "fields_total": 0,
        "quality_score": None,
        "quality_score_basis": "No composite quality score is asserted; source support, limitations, scriptural status, and review flags are explicit.",
    }
    data["evidence"] = build_evidence(candidate)
    data["provenance"] = {
        "pipeline": "NameVerse super-2.0 demand-informed batch builder",
        "methodology": "Curated evidence manifest -> template-matched record build -> alias/script collision audit -> schema and integrity validation",
        "upgraded_from": "New record generated from the current super-2.0 architecture; not converted from a legacy record.",
        "processed_at": created_at,
    }
    faq_entities = [
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
                "description": f"{name} — {language_article} {primary_language}-origin given name: {candidate['short_meaning']}",
                "inDefinedTermSet": {"@type": "DefinedTermSet", "name": "NameVerse Islamic Names"},
            },
            {"@type": "FAQPage", "mainEntity": faq_entities},
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": ""},
                    {"@type": "ListItem", "position": 2, "name": "Islamic Names", "item": ""},
                    {"@type": "ListItem", "position": 3, "name": name, "item": ""},
                ],
            },
        ],
    }
    data["editorial_validation"] = {
        "needs_manual_verification": True,
        "flags": flags,
        "confidence": candidate["meaning_confidence"],
        "reviewed_by": "Automated source-aware build and validation; not a human or native-speaker review",
        "reviewed_at": created_at,
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
            "numerology",
            "lucky_attributes",
            "spiritual_meaning",
            "celebrity_usage",
            "real_world_usage",
            "name_story",
        ],
    }
    data["content_quality"]["fields_total"] = scalar_leaf_count(data)
    return record


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    names = manifest.get("names")
    if not isinstance(names, list) or len(names) != 10:
        return ["Manifest must contain exactly ten names."]
    seen_slugs: set[str] = set()
    for candidate in names:
        if not isinstance(candidate, dict):
            errors.append("Every manifest name must be an object.")
            continue
        name = candidate.get("name", "")
        slug = candidate.get("slug", "")
        if not isinstance(name, str) or not name.strip():
            errors.append("Manifest name is missing a display name.")
        if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
            errors.append(f"Invalid slug {slug!r} for {name!r}.")
        elif slug in seen_slugs:
            errors.append(f"Duplicate manifest slug {slug!r}.")
        else:
            seen_slugs.add(slug)
        if isinstance(name, str) and isinstance(slug, str) and normalize_latin(name) != slug:
            errors.append(f"Slug {slug!r} does not match normalized name {name!r}.")
        for required in ("aliases", "script_form", "primary_meaning", "meaning_explanation", "evidence", "popularity", "translations", "quranic"):
            if required not in candidate:
                errors.append(f"{name!r} lacks required manifest field {required!r}.")
        for source in candidate.get("evidence", []):
            if not source.get("url", "").startswith("https://"):
                errors.append(f"{name!r} has an evidence source without an HTTPS URL.")
        for metric in candidate.get("popularity", {}).get("measurements", []):
            for required in ("region", "measure", "year", "rank", "source_title", "source_url", "limitation"):
                if required not in metric:
                    errors.append(f"{name!r} popularity metric lacks {required!r}.")
            if not metric.get("limitation"):
                errors.append(f"{name!r} popularity metric needs an explicit limitation.")
            if not isinstance(metric.get("year"), int) or not isinstance(metric.get("rank"), int):
                errors.append(f"{name!r} popularity metric year and rank must be integers.")
            if metric.get("births") is not None and not isinstance(metric.get("births"), int):
                errors.append(f"{name!r} popularity birth count must be an integer or null.")
            percent = metric.get("relative_interest_percent")
            if percent is not None and (not isinstance(percent, (int, float)) or not 0 <= percent <= 100):
                errors.append(f"{name!r} relative visitor-interest percentage must be between 0 and 100.")
    return errors


def object_shape_errors(actual: Any, expected: Any, path: str = "$") -> list[str]:
    """Compare nested object keys to the template while allowing variable lists."""
    errors: list[str] = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected object, got {type(actual).__name__}."]
        expected_keys = set(expected)
        actual_keys = set(actual)
        for key in sorted(expected_keys - actual_keys):
            errors.append(f"{path}: missing template key {key!r}.")
        for key in sorted(actual_keys - expected_keys):
            errors.append(f"{path}: unexpected key {key!r}.")
        for key in sorted(expected_keys & actual_keys):
            errors.extend(object_shape_errors(actual[key], expected[key], f"{path}.{key}"))
        return errors
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}: expected array, got {type(actual).__name__}."]
        if path.endswith(".structured_data.@graph") and len(actual) != len(expected):
            errors.append(f"{path}: expected {len(expected)} graph nodes, got {len(actual)}.")
            return errors
        if not expected:
            return errors
        if path.endswith(".structured_data.@graph"):
            for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
                errors.extend(object_shape_errors(actual_item, expected_item, f"{path}[{index}]"))
        elif isinstance(expected[0], (dict, list)):
            for index, actual_item in enumerate(actual):
                errors.extend(object_shape_errors(actual_item, expected[0], f"{path}[{index}]"))
        return errors
    return errors


def validate_record(
    record: dict[str, Any],
    candidate: dict[str, Any],
    template: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    label = candidate["name"]
    if record.get("schema_version") != template.get("schema_version"):
        errors.append(f"{label}: schema_version does not match the template.")
    if record.get("success") is not True:
        errors.append(f"{label}: success must be true.")
    if list(record.get("data", {}).keys()) != list(template.get("data", {}).keys()):
        errors.append(f"{label}: data keys/order do not match the super-2.0 template.")
        return errors
    data = record["data"]
    errors.extend(object_shape_errors(data, template["data"], "$.data"))
    if data.get("name") != candidate["name"] or data.get("slug") != candidate["slug"]:
        errors.append(f"{label}: top-level name/slug mismatch.")
    for section in ("identity", "core_meaning", "etymology", "language", "origin", "religion", "translations", "translation_quality", "pronunciation", "name_variants", "popularity", "faq", "evidence", "provenance", "structured_data", "editorial_validation", "render_policy"):
        if not isinstance(data.get(section), dict) and section not in {"faq"}:
            errors.append(f"{label}: required section {section!r} is missing or not an object.")
    if len(data.get("faq", [])) < 8:
        errors.append(f"{label}: fewer than eight FAQs.")
    if not data.get("evidence", {}).get("sources"):
        errors.append(f"{label}: no evidence source strings.")
    popularity = data.get("popularity", {})
    if popularity.get("score") is not None:
        errors.append(f"{label}: composite popularity score must remain null.")
    if not popularity.get("by_region"):
        errors.append(f"{label}: no source-scoped popularity evidence.")
    if "popularity" in data.get("render_policy", {}).get("hidden_sections", []):
        errors.append(f"{label}: source-scoped popularity is unexpectedly hidden by render policy.")
    expected_metric_keys = {
        "region", "measure", "year", "category", "rank", "births",
        "relative_interest_percent", "observation_period", "source_title",
        "source", "limitation",
    }
    for metric in popularity.get("by_region", []):
        if set(metric) != expected_metric_keys:
            errors.append(f"{label}: popularity metric keys do not match the batch format.")
        if not metric.get("source") or not metric.get("limitation") or not metric.get("region") or not metric.get("year") or not metric.get("rank"):
            errors.append(f"{label}: popularity metric lacks source, limitation, region, year, or rank.")
        if not isinstance(metric.get("source"), str) or not metric["source"].startswith("https://"):
            errors.append(f"{label}: popularity source must be an HTTPS URL.")
        percent = metric.get("relative_interest_percent")
        if percent is not None and (not isinstance(percent, (int, float)) or not 0 <= percent <= 100):
            errors.append(f"{label}: relative visitor-interest percentage is outside 0–100.")
    translations = data.get("translations", {})
    if set(translations) != set(template["data"]["translations"]):
        errors.append(f"{label}: translation locales do not match the template.")
    for language, translation in translations.items():
        for key in ("name", "script", "meaning", "long_meaning"):
            if not translation.get(key):
                errors.append(f"{label}: translations.{language}.{key} is blank.")
    if data.get("translation_quality", {}).get("native_review_required") is not True:
        errors.append(f"{label}: localized translations must be flagged for native review.")
    if data.get("numerology", {}).get("render") is not False:
        errors.append(f"{label}: unsupported numerology must remain hidden.")
    if data.get("lucky_attributes", {}).get("render") is not False:
        errors.append(f"{label}: unsupported lucky attributes must remain hidden.")
    if data.get("editorial_validation", {}).get("needs_manual_verification") is not True:
        errors.append(f"{label}: manual/native editorial review must remain outstanding.")
    if not data.get("core_meaning", {}).get("primary_meaning"):
        errors.append(f"{label}: primary meaning is blank.")
    structured = data.get("structured_data", {}).get("@graph", [])
    faq_nodes = [node for node in structured if node.get("@type") == "FAQPage"] if isinstance(structured, list) else []
    if not faq_nodes or len(faq_nodes[0].get("mainEntity", [])) != len(data.get("faq", [])):
        errors.append(f"{label}: structured FAQ schema does not match the FAQ list.")
    return errors


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object: {path}")
    return value


def run(manifest_path: Path, dataset_dir: Path, template_path: Path, write: bool, check: bool) -> int:
    manifest = read_json(manifest_path, "manifest")
    manifest_errors = validate_manifest(manifest)
    if manifest_errors:
        print("Manifest validation failed:", file=sys.stderr)
        for error in manifest_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    template = read_json(template_path, "template")
    if template.get("schema_version") != "super-2.0" or not isinstance(template.get("data"), dict):
        print(f"Template is not a super-2.0 record: {template_path}", file=sys.stderr)
        return 1
    if not dataset_dir.is_dir():
        print(f"Dataset directory does not exist: {dataset_dir}", file=sys.stderr)
        return 1

    expected = [
        build_record(candidate, template, manifest["created_at"])
        for candidate in manifest["names"]
    ]
    record_errors = []
    for record, candidate in zip(expected, manifest["names"]):
        record_errors.extend(validate_record(record, candidate, template))
    if record_errors:
        print("Generated-record validation failed:", file=sys.stderr)
        for error in record_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    dataset_records = load_dataset_records(dataset_dir)
    exact_existing: set[str] = set()
    for candidate, expected_record in zip(manifest["names"], expected):
        path = dataset_dir / f"{candidate['slug']}.json"
        if not path.exists():
            continue
        existing = read_json(path, "existing candidate record")
        if existing != expected_record:
            print(
                f"Refusing to overwrite non-matching existing file {path}. "
                "Review it manually or select a different candidate.",
                file=sys.stderr,
            )
            return 1
        exact_existing.add(candidate["slug"])

    index = build_existing_index(dataset_records, excluded_stems=exact_existing)
    collisions = check_batch_collisions(expected, index)
    if collisions:
        print("Duplicate/collision audit failed:", file=sys.stderr)
        for error in collisions:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if check:
        missing = [c["slug"] for c in manifest["names"] if c["slug"] not in exact_existing]
        if missing:
            print("Batch check failed; expected records are missing: " + ", ".join(missing), file=sys.stderr)
            return 1
        print(f"OK: {len(expected)} records exactly match the manifest/template; no dataset collisions.")
        return 0

    if write:
        created: list[Path] = []
        try:
            for candidate, record in zip(manifest["names"], expected):
                path = dataset_dir / f"{candidate['slug']}.json"
                if candidate["slug"] in exact_existing:
                    continue
                with path.open("x", encoding="utf-8") as handle:
                    json.dump(record, handle, ensure_ascii=False, indent=2)
                    handle.write("\n")
                created.append(path)
        except OSError as exc:
            print(f"Could not write complete batch: {exc}", file=sys.stderr)
            return 1
        print(f"Wrote {len(created)} records to {dataset_dir}.")
        if exact_existing:
            print(f"Left {len(exact_existing)} identical existing batch record(s) unchanged.")
        return 0

    print(f"Dry run OK: {len(expected)} candidates; {len(dataset_records)} existing records scanned; no collisions.")
    for candidate in manifest["names"]:
        state = "already built" if candidate["slug"] in exact_existing else "ready"
        print(f"  {candidate['name']} ({candidate['slug']}) — {state}")
    print("No files written. Use --write to add the records.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Curated JSON batch manifest")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET), help="Existing Islamic dataset directory")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="Existing super-2.0 JSON record")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Write records after all checks pass")
    mode.add_argument("--check", action="store_true", help="Check that all generated records already exist and match")
    args = parser.parse_args(argv)
    try:
        return run(
            resolve_path(args.manifest),
            resolve_path(args.dataset),
            resolve_path(args.template),
            write=args.write,
            check=args.check,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
