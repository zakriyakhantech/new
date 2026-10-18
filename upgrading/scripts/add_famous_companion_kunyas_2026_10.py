#!/usr/bin/env python3
"""Build a collision-audited batch of famous historical Companion kunyas.

The records describe well-known historical kunyas, not necessarily modern
standalone given names. References are listed as research pointers and are not
claimed as independently rechecked in this pass. No popularity or religious
ruling is asserted.

From the repository root:
    python3 upgrading/scripts/add_famous_companion_kunyas_2026_10.py        # dry run
    python3 upgrading/scripts/add_famous_companion_kunyas_2026_10.py --write
    python3 upgrading/scripts/add_famous_companion_kunyas_2026_10.py --check
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from pathlib import Path
from typing import Any

# Reuse the repository's audited super-2.0 builder primitives without changing
# the already-merged Qur'anic batch or its manifest.
import add_quranic_names_2026_10 as core

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "upgrading" / "names_upgraded" / "islamic"
TEMPLATE = DATASET / "aaban.json"
MANIFEST = ROOT / "upgrading" / "name_batches" / "famous_companion_kunyas_2026-10.json"
VERIFICATION_CSV = DATASET / "ISLAMIC_VERIFICATION_MANIFEST.csv"
PROGRESS = DATASET / "PROGRESS_FAMOUS_COMPANION_KUNYAS_2026-10.json"
CREATED_AT = "2026-10-18T00:00:00+00:00"
REVIEWED_AT = "2026-10-18"
BATCH_ID = "famous-companion-kunyas-2026-10-18"
STATUS = "FAMOUS_KUNYA_BATCH_2026-10-18"

POLICY = [
    "Only add a canonical Romanized name and Arabic-script form absent from the current dataset, including aliases, localized scripts, pronunciation scripts, and variants.",
    "Every entry is explicitly typed as a historical kunya; a literal father/mother-of construction does not assert biological parenthood or make the kunya a modern given name.",
    "Historical bearer and lexical construction are separate claims. Classical reference pointers are listed with limitations and are not claimed as independently rechecked in this pass.",
    "Qur'anic status, Muslim cultural use, name popularity, and religious recommendation are not inferred from a Companion association.",
    "Non-English glosses are editorial drafts requiring native-speaker review. Numerology, lucky attributes, personality claims, and name stories are suppressed.",
]

def _build_record(entry: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    """Call the shared builder without leaving global metadata changed."""
    previous = (core.CREATED_AT, core.REVIEWED_AT, core.BATCH_ID, core.COLLECTION_POLICY)
    try:
        core.CREATED_AT = CREATED_AT
        core.REVIEWED_AT = REVIEWED_AT
        core.BATCH_ID = BATCH_ID
        core.COLLECTION_POLICY = POLICY
        return core.build_record(entry, template)
    finally:
        core.CREATED_AT, core.REVIEWED_AT, core.BATCH_ID, core.COLLECTION_POLICY = previous


def _refs(bearer: str) -> tuple[list[tuple[str, str, str, str]], list[tuple[str, str, str]]]:
    bio = f"Ibn Hajar al-Asqalani, al-Isaba fi Tamyiz al-Sahaba, entry for {bearer}"
    tabaqat = f"Ibn Sa'd, al-Tabaqat al-Kubra, entry for {bearer}"
    lex = "Lane, An Arabic-English Lexicon, entries for أب (ab) and أم (umm)"
    evidence = [
        (bio, "", "Biographical reference for the historical bearer and recorded kunya.", "Bibliographic pointer only; entry/page was not independently rechecked in this pass and does not establish modern given-name frequency."),
        (tabaqat, "", "Classical biographical reference for the historical bearer.", "Reference listed as a research lead, not independently rechecked in this pass."),
        (lex, "", "Lexical reference for the component words father (ab) and mother (umm).", "The lexicon supports component glosses, not the historical bearer or contemporary personal-name use."),
    ]
    claims = [
        (f"The historical bearer {bearer} is recorded by this kunya", bio, "biographical_reference_listed_not_independently_rechecked"),
        ("The Arabic lexical components Abu/Umm are glossed as father/mother in the literal construction", lex, "lexical_reference_listed_not_independently_rechecked"),
        ("A kunya is a conventional identifier; literal kinship wording alone does not establish biological parenthood", None, "editorial_caution_not_independently_sourced"),
    ]
    return evidence, claims


def _trs(
    ar: str, hindi: str, kind: str, object_name_ar: str, object_name_hindi: str
) -> dict[str, tuple[str, str]]:
    if kind == "father":
        urdu = f"تاریخی کنیت؛ لفظی ساخت: {object_name_ar} کا والد"
        persian = f"کنیهٔ تاریخی؛ ساخت لفظی: پدرِ {object_name_ar}"
        hindi_meaning = f"ऐतिहासिक कुन्या; शाब्दिक संरचना: {object_name_hindi} के पिता"
        pashto = f"تاریخي کنیه؛ لفظي جوړښت: د {object_name_ar} پلار"
        arabic_meaning = f"كُنْية تاريخية؛ تركيبها الحرفي: والد {object_name_ar}"
    else:
        urdu = f"تاریخی کنیت؛ لفظی ساخت: {object_name_ar} کی والدہ"
        persian = f"کنیهٔ تاریخی؛ ساخت لفظی: مادرِ {object_name_ar}"
        hindi_meaning = f"ऐतिहासिक कुन्या; शाब्दिक संरचना: {object_name_hindi} की माता"
        pashto = f"تاریخي کنیه؛ لفظي جوړښت: د {object_name_ar} مور"
        arabic_meaning = f"كُنْية تاريخية؛ تركيبها الحرفي: والدة {object_name_ar}"
    return {
        "urdu": (ar, urdu),
        "persian": (ar, persian),
        "hindi": (hindi, hindi_meaning),
        "pashto": (ar, pashto),
        "arabic": (ar, arabic_meaning),
    }


def _entry(
    *, name: str, slug: str, gender: str, aliases: list[str], arabic: str,
    transliteration: str, short: str, bearer: str, kunya_kind: str,
    object_name: str, object_name_ar: str, hindi: str, object_name_hindi: str,
    summary: str, pron: str,
    historical_note: str, semantic: str = "historical Companion kunya",
) -> dict[str, Any]:
    evidence, claims = _refs(bearer)
    title = "father" if kunya_kind == "father" else "mother"
    primary = (
        f"{name} ({arabic}) is a historical Arabic kunya borne by {bearer}. The literal "
        f"construction is “{title} of {object_name}”; a kunya is a conventional identifier "
        "and does not by itself assert biological parenthood. The biographical references "
        "listed here are pointers, not independently rechecked in this pass. They establish "
        "neither modern name frequency nor a Qur'anic or religious recommendation."
    )
    explain = (
        f"The record treats {name} as a historical kunya, not as a claim that it is a "
        "standalone modern given name. The Arabic lexical components are listed separately "
        "from the historical bearer. A kunya's literal kinship construction does not prove "
        "the bearer had a child with that name."
    )
    return {
        "name": name,
        "slug": slug,
        "gender": gender,
        "bearer": bearer,
        "gconf": "HIGH",
        "aliases": aliases,
        "ar": arabic,
        "tr": transliteration,
        "root": "",
        "roottr": "",
        "morph": "Arabic kunya construction: أبو (Abu, father of) or أم (Umm, mother of) + a personal name; not a claim of biological parenthood.",
        "short": short,
        "primary": primary,
        "literal": short,
        "explain": explain,
        "mconf": "MEDIUM",
        "sem": semantic,
        "concepts": ["historical kunya", "Companions of the Prophet", "early Islamic history"],
        "quran": False,
        "qstatus": "not_claimed_as_quranic_personal_name",
        "qnote": "This record documents a historical Companion kunya. No Qur'anic personal-name attestation or special religious status is claimed for the kunya.",
        "rel_assoc": "Early Islamic historical usage",
        "rel_conf": "MEDIUM",
        "rel_status": "A historical identifier associated with a Companion; this is not a religious ruling or recommendation to use the kunya as a given name.",
        "rel_explain": "The entry describes a historical bearer and Arabic kunya construction. Historical Muslim use is distinct from scriptural status, naming advice, and current frequency.",
        "hadith": ("not_verified", "No specific hadith prescribing this kunya as a child's name or assigning it a special virtue is claimed."),
        "prophetic": ("not_verified", "No prophetic name status is claimed for this historical kunya."),
        "companion": ("historically_attested", f"The listed biographical reference identifies {bearer} as a Companion known by this kunya; source pointer not independently rechecked in this pass."),
        "name_status": "historical_kunya",
        "cult_note": "This form is associated with the named historical bearer; the entry makes no claim about popularity or a contemporary bearer's character.",
        "cult_interp": "No symbolic or personality interpretation is asserted; the record describes historical usage only.",
        "hist_status": "biographical_reference_listed_not_rechecked",
        "hist_note": historical_note,
        "usage_note": "Historical bearer usage is the scope of this record. Contemporary given-name frequency is not measured, and a historical kunya is not automatically a modern given name.",
        "trs": _trs(arabic, hindi, kunya_kind, object_name_ar, object_name_hindi),
        "pron": pron,
        "pron_note": "Romanized pronunciation guide only; no IPA or regional pronunciation survey is asserted.",
        "evidence": evidence,
        "claims": claims,
        "flags": ["historical_kunya_not_automatically_a_given_name", "bibliographic_references_not_rechecked", "modern_frequency_not_measured", "translations_require_native_review"],
        "selection": summary,
        "name_type": "historical_kunya",
    }


DATA: list[dict[str, Any]] = [
    _entry(
        name="Abu Ubaydah", slug="abuubaydah", gender="Male",
        aliases=["Abu Ubaidah", "Abu Ubaida", "Abu Ubaydah ibn al-Jarrah"],
        arabic="أَبُو عُبَيْدَة", transliteration="abū ʿubayda",
        short="Historical kunya; literally “father of Ubaydah”",
        bearer="ʿĀmir ibn ʿAbd Allāh ibn al-Jarrāḥ", kunya_kind="father",
        object_name="Ubaydah", object_name_ar="عبيدة", hindi="अबू उबैदा", object_name_hindi="उबैदा", pron="a-boo u-bay-dah",
        summary="Selected as a famous Companion kunya absent from the dataset; historical bearer usage is distinct from modern given-name frequency.",
        historical_note="The famous Companion ʿĀmir ibn ʿAbd Allāh ibn al-Jarrāḥ is recorded by the kunya Abū ʿUbaydah in the listed biographical references; those references were not independently rechecked here.",
    ),
    _entry(
        name="Abu Ayyub", slug="abuayyub", gender="Male",
        aliases=["Abu Ayyub al-Ansari", "Abu Ayyub al Ansari"],
        arabic="أَبُو أَيُّوب", transliteration="abū ayyūb",
        short="Historical kunya; literally “father of Ayyub”",
        bearer="Khalid ibn Zayd al-Ansari", kunya_kind="father",
        object_name="Ayyub", object_name_ar="أيوب", hindi="अबू अय्यूब", object_name_hindi="अय्यूब", pron="a-boo ay-yub",
        summary="Selected for the well-known Companion Abu Ayyub al-Ansari; the record identifies a kunya rather than asserting name popularity.",
        historical_note="Khalid ibn Zayd al-Ansari is widely known by the kunya Abū Ayyūb al-Anṣārī; the listed biographical references are pointers and were not independently rechecked here.",
    ),
    _entry(
        name="Abu Musa", slug="abumusa", gender="Male",
        aliases=["Abu Musa al-Ashari", "Abu Musa al Ashari"],
        arabic="أَبُو مُوسَى", transliteration="abū mūsā",
        short="Historical kunya; literally “father of Musa”",
        bearer="ʿAbd Allāh ibn Qays al-Ashʿari", kunya_kind="father",
        object_name="Musa", object_name_ar="موسى", hindi="अबू मूसा", object_name_hindi="मूसा", pron="a-boo moo-saa",
        summary="Selected for the notable Companion Abu Musa al-Ashari; historical usage is sourced separately from lexical meaning and popularity.",
        historical_note="The Companion ʿAbd Allāh ibn Qays al-Ashʿarī is recorded by the kunya Abū Mūsā; reference pointers are listed but not rechecked in this pass.",
    ),
    _entry(
        name="Abu al-Darda", slug="abudarda", gender="Male",
        aliases=["Abu Darda", "Abu Dardaa", "Abu al-Darda"],
        arabic="أَبُو الدَّرْدَاء", transliteration="abū al-dardāʾ",
        short="Historical kunya; literally “father of al-Darda”",
        bearer="the Companion and early Muslim scholar known as Abū al-Dardāʾ", kunya_kind="father",
        object_name="al-Darda", object_name_ar="الدرداء", hindi="अबू अल-दर्दा", object_name_hindi="अल-दर्दा", pron="a-boo ad-dar-daa",
        summary="Selected as the historical kunya of a prominent early Muslim Companion and scholar; the bearer is not reduced to an unsupported etymology.",
        historical_note="Abū al-Dardāʾ is a Companion and early Muslim scholar known by this kunya. This entry does not assert a disputed personal-name expansion; the reference pointers remain to be checked.",
    ),
    _entry(
        name="Abu Talhah", slug="abutalhah", gender="Male",
        aliases=["Abu Talha", "Abu Talha al-Ansari", "Abu Talhah al-Ansari"],
        arabic="أَبُو طَلْحَة", transliteration="abū ṭalḥa",
        short="Historical kunya; literally “father of Talhah”",
        bearer="Zayd ibn Sahl al-Ansari", kunya_kind="father",
        object_name="Talhah", object_name_ar="طلحة", hindi="अबू तल्हा", object_name_hindi="तल्हा", pron="a-boo tal-ha",
        summary="Selected for the famous Companion Abu Talhah al-Ansari; the record labels the expression as a historical kunya.",
        historical_note="The Companion Zayd ibn Sahl al-Anṣārī is known as Abū Ṭalḥah; the listed classical biographical references are research pointers and were not independently rechecked.",
    ),
    _entry(
        name="Umm Salamah", slug="ummsalamah", gender="Female",
        aliases=["Umm Salama", "Umm Salamah bint Abi Umayya"],
        arabic="أُمُّ سَلَمَة", transliteration="umm salama",
        short="Historical kunya; literally “mother of Salamah”",
        bearer="Hind bint Abi Umayya, wife of the Prophet Muhammad", kunya_kind="mother",
        object_name="Salamah", object_name_ar="سلمة", hindi="उम्म सलमा", object_name_hindi="सलमा", pron="oom sa-la-mah",
        summary="Selected for the famous early Muslim woman Umm Salamah; the entry distinguishes her historical kunya from a standalone given name.",
        historical_note="Hind bint Abī Umayya, a wife of the Prophet Muhammad, is widely known by the kunya Umm Salamah. The biographical references are listed as pointers, not independently rechecked here.",
        semantic="historical kunya of a Mother of the Believers",
    ),
    _entry(
        name="Umm Habibah", slug="ummhabibah", gender="Female",
        aliases=["Umm Habiba", "Umm Habibah bint Abi Sufyan"],
        arabic="أُمُّ حَبِيبَة", transliteration="umm ḥabība",
        short="Historical kunya; literally “mother of Habibah”",
        bearer="Ramlah bint Abi Sufyan, wife of the Prophet Muhammad", kunya_kind="mother",
        object_name="Habibah", object_name_ar="حبيبة", hindi="उम्म हबीबा", object_name_hindi="हबीबा", pron="oom ha-bee-bah",
        summary="Selected for the well-known wife of the Prophet called Umm Habibah; historical identity is not presented as a popularity measure.",
        historical_note="Ramlah bint Abī Sufyān is widely known as Umm Habibah and is counted among the wives of the Prophet Muhammad; reference pointers are not independently rechecked in this pass.",
        semantic="historical kunya of a Mother of the Believers",
    ),
    _entry(
        name="Umm Waraqah", slug="ummwaraqa", gender="Female",
        aliases=["Umm Waraqah bint Abdullah", "Umm Warqah"],
        arabic="أُمُّ وَرَقَة", transliteration="umm waraqah",
        short="Historical kunya; literally “mother of Waraqah”",
        bearer="the female Companion known in biographical sources as Umm Waraqah bint ʿAbd Allāh", kunya_kind="mother",
        object_name="Waraqah", object_name_ar="ورقة", hindi="उम्म वरक़ा", object_name_hindi="वरक़ा", pron="oom wa-ra-qah",
        summary="Selected as a documented female Companion kunya absent from the dataset; a kunya is not treated as a verified modern given name.",
        historical_note="Umm Waraqah bint ʿAbd Allāh is listed in the classical Companion-biography tradition; the reference pointers require independent page-level verification.",
    ),
    _entry(
        name="Umm Haram", slug="ummharam", gender="Female",
        aliases=["Umm Haraam", "Umm Haram bint Milhan"],
        arabic="أُمُّ حَرَام", transliteration="umm ḥarām",
        short="Historical kunya; literally “mother of Haram”",
        bearer="the female Companion Umm Haram bint Milhan", kunya_kind="mother",
        object_name="Haram", object_name_ar="حرام", hindi="उम्म हराम", object_name_hindi="हराम", pron="oom ha-raam",
        summary="Selected for the famous female Companion Umm Haram bint Milhan; no Qur'anic-name or religious-recommendation claim is made.",
        historical_note="Umm Haram bint Milḥān is a female Companion named in classical biographical and hadith literature; source pointers are listed but not independently rechecked.",
    ),
    _entry(
        name="Umm Atiyyah", slug="ummatiyyah", gender="Female",
        aliases=["Umm Atiyya", "Umm Atiyyah al-Ansariyyah"],
        arabic="أُمُّ عَطِيَّة", transliteration="umm ʿaṭiyya",
        short="Historical kunya; literally “mother of Atiyyah”",
        bearer="the female Companion and hadith transmitter known as Umm Atiyyah al-Ansariyyah", kunya_kind="mother",
        object_name="Atiyyah", object_name_ar="عطية", hindi="उम्म अतिय्या", object_name_hindi="अतिय्या", pron="oom a-tiy-yah",
        summary="Selected for the well-known female Companion and transmitter Umm Atiyyah; the entry avoids turning the kunya into a modern frequency claim.",
        historical_note="Umm ʿAṭiyyah al-Anṣāriyyah is recorded as a female Companion and transmitter; the listed classical biographical pointers are not independently rechecked in this pass.",
    ),
]


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _batch_collision_errors() -> list[str]:
    errors: list[str] = []
    seen_latin: dict[str, str] = {}
    seen_script: dict[str, str] = {}
    for entry in DATA:
        for form in [entry["name"], entry["slug"], *entry["aliases"]]:
            key = core.norm_latin(form)
            if not key:
                continue
            owner = seen_latin.get(key)
            if owner and owner != entry["slug"]:
                errors.append(f"Batch Latin collision: {form!r} shared by {owner} and {entry['slug']}")
            seen_latin[key] = entry["slug"]
        for form in [entry["ar"], entry["trs"]["hindi"][0], *(v[0] for v in entry["trs"].values())]:
            key = core.norm_script(form)
            if not key:
                errors.append(f"{entry['slug']}: empty normalized script form")
                continue
            owner = seen_script.get(key)
            if owner and owner != entry["slug"]:
                errors.append(f"Batch script collision: {form!r} shared by {owner} and {entry['slug']}")
            seen_script[key] = entry["slug"]
    return list(dict.fromkeys(errors))


def _index_and_validate(template: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], dict[str, set[str]], dict[str, set[str]]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = _batch_collision_errors()
    slugs = {entry["slug"] for entry in DATA}
    if len(slugs) != len(DATA):
        errors.append("Duplicate slugs in the batch")
    latin_index, script_index = core.dataset_index(slugs)
    errors.extend(core.audit_collisions(DATA, latin_index, script_index))
    for entry in DATA:
        record = _build_record(entry, template)
        data = record["data"]
        data["identity"]["name_type"] = "historical_kunya"
        data["identity"]["name_status"] = "historically_attested_kunya"
        data["identity"]["gender_note"] = (
            f"Gender refers to the recorded historical bearer of {entry['name']}; this kunya is not being asserted as a modern given name."
        )
        data["religion"]["quranic_status"] = {
            "is_quranic": False,
            "status": "not_claimed_as_quranic_personal_name",
            "note": "No Qur'anic personal-name attestation or special religious status is claimed for this historical kunya.",
        }
        data["religion"]["companion_status"] = {
            "status": "historically_attested",
            "note": entry["companion"][1],
        }
        data["religion"]["prophetic_status"] = {
            "status": "not_claimed",
            "note": "No prophetic name status is claimed for this historical kunya.",
        }
        data["religion"]["hadith_status"] = {
            "status": "not_claimed",
            "note": "No hadith prescribing the kunya as a given name or granting special virtue is claimed.",
        }
        data["religion"]["religious_status"] = "Historical Companion identifier; not a scriptural command or religious ruling on modern naming."
        data["religion"]["religious_explanation"] = (
            "The record documents a historical kunya and its bearer. It does not claim that the expression is Qur'anic, prescribed, or a measure of current naming frequency."
        )
        data["modern_usage"] = {
            "status": "historical_usage_only_frequency_not_measured",
            "note": "Historical bearer usage is the scope of this entry; contemporary given-name frequency is not measured.",
        }
        data["historical_context"] = {
            "status": "biographical_reference_listed_not_rechecked",
            "note": entry["hist_note"],
        }
        data["evidence"]["verification_method"] = (
            "Classical biographical and lexical references are listed as research pointers, not independently rechecked in this pass. The record distinguishes historical bearer evidence from literal kunya construction, modern name frequency, and religious status."
        )
        data["evidence"]["claim_evidence_status"] = "BIBLIOGRAPHIC_POINTERS_LISTED_NOT_INDEPENDENTLY_RECHECKED"
        data["editorial_validation"].update({
            "needs_manual_verification": True,
            "flags": list(dict.fromkeys([*data["editorial_validation"].get("flags", []), "historical_kunya_not_automatically_a_given_name", "references_not_rechecked", "native_translation_review_required"])),
            "confidence": "MEDIUM",
            "reviewed_by": "Automated collision/schema build; historical source pointers not independently rechecked",
            "reviewed_at": REVIEWED_AT,
        })
        data["content_quality"].update({
            "tier1_verified": False,
            "authenticity_flags": list(dict.fromkeys([*entry["flags"], "tier1_historical_reference_check_pending"])),
            "quality_score": None,
            "quality_score_basis": "No composite score is asserted; biographical references, contemporary use, and native translations need independent review.",
        })
        data["seo_content"]["intro_paragraph"] = (
            f"{entry['name']} is a historical Arabic kunya associated with {entry['bearer']}. This entry distinguishes the historical identifier from a modern given name."
        )
        data["seo_content"]["body_summary"] = entry["primary"]
        data["seo"]["description_paragraph"] = entry["primary"]
        data["seo"]["meta_description"] = (
            f"{entry['name']}: historical Arabic kunya and Companion bearer; no popularity or naming ruling is asserted."
        )
        data["seo"]["seo_score"] = None
        data["seo"]["seo_score_basis"] = "No composite SEO score is asserted in this evidence-limited batch."
        data["provenance"]["pipeline"] = "NameVerse evidence-led famous Companion kunya batch"
        data["provenance"]["methodology"] = (
            "Curated historical-kunya manifest -> super-2.0 template build -> Latin and Arabic-script collision audit -> schema/key-path validation. References are listed but not independently rechecked in this pass."
        )
        data["provenance"]["upgraded_from"] = "New record generated from the current super-2.0 architecture; historical kunya, not an asserted modern given name."
        data["faq"] = [{**item, "a": item["a"]} for item in data["faq"]]
        for item in data["faq"]:
            if "boy's or girl's name" in item["q"].casefold():
                item["a"] = f"The named historical bearer of this kunya is recorded as {entry['gender'].lower()}; this does not measure modern use as a given name."
        for node in data["structured_data"]["@graph"]:
            if node.get("@type") == "FAQPage":
                node["mainEntity"] = [
                    {"@type": "Question", "name": item["q"], "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
                    for item in data["faq"]
                ]
            elif node.get("@type") == "DefinedTerm":
                node["description"] = f"{entry['name']} — historical Arabic kunya; {entry['short']}."
        data["content_quality"]["fields_total"] = core.scalar_leaf_count(data)
        errors.extend(core.validate_record(record, template, entry))
        if data["identity"]["name_type"] != "historical_kunya":
            errors.append(f"{entry['slug']}: name_type is not historical_kunya")
        if data["identity"]["name_status"] != "historically_attested_kunya":
            errors.append(f"{entry['slug']}: name_status is inconsistent")
        if data["religion"]["quranic_status"]["is_quranic"] is not False:
            errors.append(f"{entry['slug']}: unexpected Qur'anic-name assertion")
        if data["content_quality"]["tier1_verified"] is not False:
            errors.append(f"{entry['slug']}: tier1 must remain false")
        records.append(record)
    return records, list(dict.fromkeys(errors)), latin_index, script_index


def build_manifest() -> dict[str, Any]:
    return {
        "manifest_version": 1,
        "batch_id": BATCH_ID,
        "created_at": CREATED_AT,
        "dataset": "upgrading/names_upgraded/islamic",
        "template": "upgrading/names_upgraded/islamic/aaban.json",
        "builder": "upgrading/scripts/add_famous_companion_kunyas_2026_10.py",
        "selection_policy": POLICY,
        "verification_summary": {
            "names": len(DATA),
            "name_type": "historical_kunya; not automatically a modern given name",
            "latin_and_arabic_script_collision_audit": "passed before write; entire existing dataset scanned",
            "schema": "super-2.0 key-path parity with aaban.json",
            "historical_sources": "bibliographic pointers listed; not independently rechecked in this pass",
            "quranic_claims": "no personal-name attestation claimed",
            "popularity": "not measured",
            "translations": "drafts; native review required",
        },
        "names": [core.manifest_entry(entry) for entry in DATA],
    }


def _read_csv() -> tuple[list[dict[str, str]], list[str]]:
    with VERIFICATION_CSV.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []
    return rows, fields


def _write_csv(rows: list[dict[str, str]], fields: list[str]) -> None:
    with VERIFICATION_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _check_persisted(records: list[dict[str, Any]], rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for record, entry in zip(records, DATA):
        path = DATASET / f"{entry['slug']}.json"
        if not path.exists():
            errors.append(f"Missing {path.relative_to(ROOT)}")
            continue
        persisted = read_json(path)
        if persisted != record:
            errors.append(f"Persisted record differs from generated build: {entry['slug']}")
    wanted = {entry["slug"] for entry in DATA}
    matching = [row for row in rows if row.get("slug") in wanted]
    if len(matching) != len(DATA):
        errors.append(f"Expected {len(DATA)} verification CSV rows; found {len(matching)}")
    for row in matching:
        if row.get("status") != STATUS or row.get("batch") != BATCH_ID:
            errors.append(f"Incorrect verification CSV status for {row.get('slug')}")
    if not MANIFEST.exists():
        errors.append("Missing famous-kunya batch manifest")
    elif read_json(MANIFEST) != build_manifest():
        errors.append("Famous-kunya manifest differs from the builder output")
    if not PROGRESS.exists():
        errors.append("Missing famous-kunya progress file")
    else:
        progress = read_json(PROGRESS)
        if progress.get("status") != "complete" or progress.get("names_added") != len(DATA):
            errors.append("Famous-kunya progress file is incomplete")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="Write records after all checks pass")
    group.add_argument("--check", action="store_true", help="Verify persisted records and manifests")
    args = parser.parse_args(argv)

    template = read_json(TEMPLATE)
    if template.get("schema_version") != "super-2.0":
        print("Template is not super-2.0", file=sys.stderr)
        return 1
    records, errors, latin_index, script_index = _index_and_validate(template)
    if errors:
        print("Batch validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    rows, fields = _read_csv()
    slugs = [entry["slug"] for entry in DATA]
    if args.check:
        errors = _check_persisted(records, rows)
        if errors:
            print("Persisted check failed:\n- " + "\n- ".join(errors), file=sys.stderr)
            return 1
        print(f"OK: {len(records)} historical kunyas match the manifest, progress file, template, and collision audit.")
        return 0

    if args.write:
        existing = [entry["slug"] for entry in DATA if (DATASET / f"{entry['slug']}.json").exists()]
        already_in_csv = [entry["slug"] for entry in DATA if any(row.get("slug") == entry["slug"] for row in rows)]
        if existing or already_in_csv:
            print("Refusing to overwrite or duplicate names: " + ", ".join(sorted(set(existing + already_in_csv))), file=sys.stderr)
            return 1
        for record, entry in zip(records, DATA):
            with (DATASET / f"{entry['slug']}.json").open("x", encoding="utf-8") as handle:
                json.dump(record, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
        with MANIFEST.open("w", encoding="utf-8") as handle:
            json.dump(build_manifest(), handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        for entry in DATA:
            rows.append({
                "path": f"upgrading/names_upgraded/islamic/{entry['slug']}.json",
                "slug": entry["slug"],
                "status": STATUS,
                "batch": BATCH_ID,
            })
        _write_csv(rows, fields)
        progress = {
            "schema_version": "super-2.0",
            "batch_id": BATCH_ID,
            "dataset": "upgrading/names_upgraded/islamic",
            "status": "complete",
            "names_added": len(records),
            "slugs": slugs,
            "verification_csv_rows_present": len(slugs),
            "schema_key_paths": len(core.key_paths(template)),
            "collision_audit": "passed (Latin and Arabic-script; entire current dataset scanned)",
            "source_scope": "bibliographic pointers listed, not independently rechecked; contemporary popularity not measured",
            "processed_at": CREATED_AT,
        }
        with PROGRESS.open("w", encoding="utf-8") as handle:
            json.dump(progress, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"Wrote {len(records)} famous historical Companion kunyas, one manifest, verification rows, and progress file.")
        return 0

    print(f"Dry run OK: {len(records)} records; {len(latin_index)} Latin and {len(script_index)} script keys scanned; no collisions.")
    for entry in DATA:
        print(f"  {entry['name']} ({entry['slug']}) — historical kunya")
    print("No files written. Use --write to add the records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
