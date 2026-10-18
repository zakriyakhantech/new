#!/usr/bin/env python3
"""Apply and validate the 2026-10-18 Islamic verification batches.

This closes the 27-record early-A manifest gap and reviews the next ten pending
records after the completed 82-291 block. It does not certify unsupported name
usage or translations: uncertainty is retained in the records and manifest.
Run from the repository root:
    python3 upgrading/scripts/review_islamic_verification_batch_2026_10_18.py --write
    python3 upgrading/scripts/review_islamic_verification_batch_2026_10_18.py --check
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "upgrading" / "names_upgraded" / "islamic"
MANIFEST = DATASET / "ISLAMIC_VERIFICATION_MANIFEST.csv"
REVIEWED_AT = "2026-10-18"
BATCH = "quality-repair-2026-10-18"
STATUS = "REVIEWED_BATCH_2026-10-18"

GAP_SLUGS = [
    "aalam", "aalee", "aali", "aalia", "aaliah", "aalif", "aalim",
    "aalima", "aaliya", "aaliyah", "aamaal", "aamal", "aameen",
    "aamer", "aamil", "aamilah", "aamin", "aamina", "aaminaat",
    "aaminah", "aamira", "aamirah", "aamirat", "aamirul", "aamiya",
    "aamla", "aamna",
]
CONTINUATION_SLUGS = [
    "adel", "adem", "aden", "adena", "adha", "adham", "adhara",
    "adi", "adib", "adiba",
]
ALL_SLUGS = GAP_SLUGS + CONTINUATION_SLUGS

# These are editorial conclusions for this review. Where the record has no
# directly cited lexical source, confidence is deliberately capped and the
# script records the source gap rather than promoting the claim to Tier 1.
PATCHES: dict[str, dict[str, Any]] = {
    "aalam": {
        "confidence": "HIGH",
        "short": "World; creation; realm",
        "primary": (
            "The Arabic lexical form عَالَم (ʿālam) is glossed by the listed dictionary "
            "sources as “world” or “creation.” Those sources support the lexical sense only; "
            "modern given-name attestation, frequency, and gender distribution are separate "
            "claims and are not established here."
        ),
        "explain": "The two dictionary references already recorded for عَالَم support the world/creation sense. They do not establish personal-name use, gender distribution, or popularity; those remain unverified.",
        "morphology": "Arabic lexical noun عَالَم; root analysis ع ل م is listed in the cited lexicon, but no personal-name derivation is asserted.",
        "etymological_meaning": "World/creation (lexical sense; personal-name etymology not asserted)",
        "etymology_explanation": "The listed dictionary references support the lexical world/creation sense only; they do not establish given-name frequency or gender distribution.",
        "flags": ["given_name_attestation_not_independently_sourced", "gender_distribution_not_independently_sourced"],
    },
    "aalee": {
        "confidence": "LOW",
        "short": "High, elevated (provisional lexical gloss)",
        "primary": "The record associates the Latin spelling Aalee with the Arabic form علي and an elevation-related gloss. A direct lexical citation and evidence that this exact Latin spelling represents that form are not recorded; the gloss and name-use claim therefore remain provisional.",
        "explain": "علي and عالي are distinct written forms. The record's علی/علي mapping is not treated as proof that every spelling of Aalee is identical to Ali; manual transliteration review remains open.",
        "flags": ["direct_lexical_source_needed", "exact_transliteration_not_independently_sourced", "candidate_variant_manual_review"],
        "variant_note": "Candidate transliteration relationship with ali/other Ali spellings; exact form and route relationship require manual review. Do not merge automatically.",
    },
    "aali": {
        "confidence": "LOW",
        "short": "High, elevated (provisional lexical gloss)",
        "primary": "The record maps Aali to Arabic عالي (ʿālī), conventionally glossed “high” or “elevated.” No direct lexical reference or name-usage evidence is listed for this record, so the form-to-spelling match and personal-name use remain provisional.",
        "explain": "The recorded form عالي is distinct from علي. Root and morphology fields are retained as provisional until checked against a direct Arabic lexicon.",
        "flags": ["direct_lexical_source_needed", "exact_transliteration_not_independently_sourced"],
    },
    "aalia": {
        "confidence": "LOW",
        "short": "High, elevated (feminine form; provisional)",
        "primary": "The record maps Aalia to Arabic عالية, a feminine form conventionally glossed “high” or “elevated.” No direct lexical reference or name-usage evidence is listed; the exact transliteration and given-name claims remain provisional.",
        "explain": "The recorded form عالية is a feminine form in Arabic. Its use as a personal name and the spelling Aalia are not established by the lexical gloss alone.",
        "flags": ["direct_lexical_source_needed", "exact_transliteration_not_independently_sourced", "candidate_variant_manual_review"],
        "variant_note": "Candidate transliteration group with aaliah and aaliya (all currently record عالية); keep routes separate pending human review.",
    },
    "aaliah": {
        "confidence": "LOW",
        "short": "High, elevated (feminine form; provisional)",
        "primary": "The record maps Aaliah to Arabic عالية, a feminine form conventionally glossed “high” or “elevated.” No direct lexical reference or name-usage evidence is listed; the exact transliteration and given-name claims remain provisional.",
        "explain": "The recorded form عالية is shared with other Latin spellings in the dataset. That supports a candidate transliteration relationship, not an automatic merge or a frequency claim.",
        "flags": ["direct_lexical_source_needed", "exact_transliteration_not_independently_sourced", "candidate_variant_manual_review"],
        "variant_note": "Candidate transliteration group with aalia and aaliya (all currently record عالية); keep routes separate pending human review.",
    },
    "aalif": {
        "confidence": "MEDIUM",
        "short": "The Arabic letter alif",
        "primary": "Aalif is mapped in this record to the Arabic letter name أَلِف (alif), the first letter of the Arabic alphabet. This is a lexical identification, not evidence that Aalif is an attested personal name or that it has a particular gender distribution.",
        "explain": "The record identifies a letter name. No direct dictionary citation or source for its use as a personal name is supplied, so name status and gender remain unverified.",
        "morphology": "Arabic letter name alif; no personal-name morphology or root is asserted.",
        "etymological_meaning": "The Arabic letter-name alif",
        "etymology_explanation": "This record identifies a letter name; it does not establish the letter name as an attested given name.",
        "gender": "Unknown",
        "flags": ["direct_lexical_source_needed", "given_name_attestation_not_independently_sourced", "gender_distribution_not_independently_sourced"],
    },
    "aalim": {
        "confidence": "LOW",
        "short": "Learned person; scholar (provisional gloss)",
        "primary": "The record maps Aalim to Arabic عالم (ʿālim), conventionally glossed “learned person” or “scholar.” A direct lexical citation and independent evidence of use of this exact spelling as a personal name are not recorded; both claims remain provisional.",
        "explain": "The spelling and root are retained as candidate Arabic analysis only; confirm them against a direct dictionary before presenting them as fully verified.",
        "flags": ["direct_lexical_source_needed", "exact_transliteration_not_independently_sourced"],
    },
    "aalima": {
        "confidence": "LOW",
        "short": "Learned woman; female form (provisional gloss)",
        "primary": "The record maps Aalima to Arabic عالمة, the feminine form corresponding to عالم and conventionally glossed “learned woman.” Direct lexical sourcing and evidence of use of this exact Latin spelling as a personal name are not recorded.",
        "explain": "The feminine grammatical form is distinct from evidence about a person's gender or the name's frequency. A direct Arabic lexical source and name-usage source remain outstanding.",
        "flags": ["direct_lexical_source_needed", "exact_transliteration_not_independently_sourced"],
    },
    "aaliya": {
        "confidence": "LOW",
        "short": "High, elevated (feminine form; provisional)",
        "primary": "The record maps Aaliya to Arabic عالية, a feminine form conventionally glossed “high” or “elevated.” No direct lexical reference or name-usage evidence is listed; the exact transliteration and given-name claims remain provisional.",
        "explain": "The recorded form عالية is also attached to Aalia and Aaliah in this dataset. This is a candidate transliteration group, not a decision to merge records.",
        "flags": ["direct_lexical_source_needed", "exact_transliteration_not_independently_sourced", "candidate_variant_manual_review"],
        "variant_note": "Candidate transliteration group with aalia and aaliah (all currently record عالية); keep routes separate pending human review.",
    },
    "aaliyah": {
        "confidence": "LOW",
        "unresolved": True,
        "clear_form": False,
        "short": "Meaning not verified for this exact spelling",
        "primary": "The intended Arabic form and lexical meaning of the exact Latin spelling Aaliyah are not established by a direct source in this record. The current form علية differs from عالية, which is used in several translations and related records; those forms must not be conflated without evidence.",
        "explain": "The record contains a form/translation mismatch. Arabic script, root, gender, and meaning remain candidates for manual review; no popular gloss is asserted.",
        "flags": ["exact_lexical_form_unverified", "form_translation_mismatch", "direct_lexical_source_needed", "candidate_variant_manual_review"],
        "variant_note": "Do not merge with records using عالية until the intended form for Aaliyah is verified.",
        "translations_unverified": True,
    },
    "aamaal": {
        "confidence": "LOW",
        "short": "Hopes; aspirations (provisional gloss)",
        "primary": "The record maps Aamaal to Arabic آمال, commonly glossed “hopes” or “aspirations.” This lexical interpretation is not supported by a direct source in the record, and use of the spelling as a personal name is a separate, unverified claim.",
        "explain": "آمال is recorded as the plural form in this dataset; direct lexicon evidence and the relationship between the Latin spellings Aamaal and Aamal remain to be reviewed.",
        "flags": ["direct_lexical_source_needed", "candidate_variant_manual_review"],
        "variant_note": "Candidate transliteration pair with aamal (both currently record آمال); do not merge without route and usage review.",
    },
    "aamal": {
        "confidence": "LOW",
        "short": "Hopes; aspirations (provisional gloss)",
        "primary": "The record maps Aamal to Arabic آمال, commonly glossed “hopes” or “aspirations.” This lexical interpretation is not supported by a direct source in the record, and use of the spelling as a personal name is a separate, unverified claim.",
        "explain": "آمال is recorded as a plural form; the Latin spelling may be a transliteration variant of Aamaal, but that relationship and name usage require manual review.",
        "flags": ["direct_lexical_source_needed", "candidate_variant_manual_review"],
        "variant_note": "Candidate transliteration pair with aamaal (both currently record آمال); do not merge without route and usage review.",
    },
    "aameen": {
        "confidence": "LOW",
        "short": "Amen; a supplication meaning “O God, answer” (provisional)",
        "primary": "The record maps Aameen to آمين, a devotional response conventionally rendered “amen” or “O God, answer.” This is distinct from أمين (Amīn, “trustworthy”), which is a different Arabic form; no source for personal-name use of Aameen is recorded.",
        "explain": "The vowelled forms آمين and أمين must not be collapsed: the former is a supplicatory formula and the latter is a different lexical form. Direct lexical evidence and name-usage evidence remain outstanding.",
        "flags": ["direct_lexical_source_needed", "distinguish_from_amin_امين", "given_name_attestation_not_independently_sourced"],
    },
    "aamer": {
        "confidence": "LOW",
        "short": "Flourishing; inhabited (provisional gloss)",
        "primary": "The record maps Aamer to Arabic عامر, conventionally associated with the senses “inhabited” or “flourishing.” No direct dictionary reference is recorded. The same Arabic form appears under Aamir in this dataset, so the Latin spellings are a candidate transliteration pair, not two proven distinct names.",
        "explain": "عامر is distinct from أمير (amīr, “commander/prince”). The Aamer/Aamir spelling relationship, the lexical gloss, and personal-name frequency require separate evidence.",
        "flags": ["direct_lexical_source_needed", "candidate_variant_manual_review", "distinguish_from_amir_أمير"],
        "variant_note": "Candidate transliteration relationship with aamir; both records currently use عامر. Keep routes separate pending human review.",
    },
    "aamil": {
        "confidence": "LOW",
        "short": "Worker; agent; one who acts (provisional gloss)",
        "primary": "The record maps Aamil to Arabic عامل, conventionally glossed “worker,” “agent,” or “one who acts.” The cited record contains no direct lexical source, and the exact transliteration and modern name use remain unverified.",
        "explain": "The listed root and active-participle analysis are provisional pending a direct Arabic lexicon citation; the gloss does not establish a religious or scriptural name claim.",
        "flags": ["direct_lexical_source_needed", "exact_transliteration_not_independently_sourced"],
    },
    "aamilah": {
        "confidence": "LOW",
        "short": "Worker; one who acts (feminine form; provisional)",
        "primary": "The record maps Aamilah to Arabic عاملة, the feminine form corresponding to عامل, conventionally glossed “worker” or “one who acts.” No direct lexical source or independent name-usage evidence is listed.",
        "explain": "The grammatical feminine form does not by itself establish gender distribution among personal-name bearers. Direct lexical and usage sources remain outstanding.",
        "flags": ["direct_lexical_source_needed", "gender_distribution_not_independently_sourced"],
    },
    "aamin": {
        "confidence": "LOW",
        "short": "Trustworthy; reliable (provisional gloss)",
        "primary": "The record maps Aamin to Arabic أمين (amīn), conventionally glossed “trustworthy” or “reliable.” No direct dictionary source is listed. This is distinct from آمين (Aameen), a different devotional form.",
        "explain": "The form أمين is kept separate from آمين. Root analysis, the exact Latin vowel convention, and personal-name frequency need direct sources.",
        "flags": ["direct_lexical_source_needed", "distinguish_from_aameen_آمين", "exact_transliteration_not_independently_sourced"],
    },
    "aamina": {
        "confidence": "LOW",
        "short": "Trustworthy; reliable (provisional; recorded form أمينة)",
        "primary": "The record gives the Arabic form أمينة, which is conventionally associated with “trustworthy” or “reliable.” The earlier safety gloss belongs more directly to آمنة, a different written form. A direct lexical citation and evidence for this exact Latin spelling are still needed.",
        "explain": "The written form أمينة should not be translated as though it were آمنة without a source establishing that alternate spelling. Aamina/Aaminah currently share the same unvowelled Arabic form and are queued for variant review.",
        "flags": ["direct_lexical_source_needed", "corrected_form_meaning_mismatch", "candidate_variant_manual_review"],
        "variant_note": "Candidate transliteration pair with aaminah; both currently record أمينة. Review vowelled forms and route policy before any merge.",
        "translations": {
            "arabic": ("أمينة", "أمينة، جديرة بالثقة، موثوقة"),
            "urdu": ("امینہ", "قابلِ اعتماد، امانت دار"),
            "persian": ("امین", "قابل اعتماد، امین"),
            "hindi": ("आमीना", "विश्वसनीय, भरोसेमंद"),
            "pashto": ("آمینه", "باور وړ، امانتداره"),
        },
    },
    "aaminaat": {
        "confidence": "LOW",
        "short": "Trustworthy women (feminine plural; provisional gloss)",
        "primary": "The record maps أمينات to the feminine plural corresponding to أمينة (“trustworthy”). A plural lexical form is not evidence that Aaminaat is an established singular personal name; that usage and the English gloss require direct sourcing.",
        "explain": "The written form is plural in the record. Singular-name meanings should not be assigned automatically; the form and name usage remain provisional.",
        "flags": ["direct_lexical_source_needed", "plural_form_name_usage_unverified"],
        "translations": {
            "arabic": ("أمينات", "نساء موثوقات / أمينات"),
            "urdu": ("امینات", "قابلِ اعتماد خواتین"),
            "persian": ("امینات", "زنان امین، قابل اعتماد"),
            "hindi": ("आमिनात", "विश्वसनीय महिलाएँ"),
            "pashto": ("امینات", "باور وړ ښځې"),
        },
    },
    "aaminah": {
        "confidence": "LOW",
        "short": "Trustworthy; reliable (provisional gloss)",
        "primary": "The record gives the Arabic form أمينة, conventionally associated with “trustworthy” or “reliable.” Direct lexical evidence and evidence for the exact Latin spelling Aaminah are not recorded; the gloss remains provisional.",
        "explain": "The form أمينة is distinct from آمنة (“safe/secure”). Aaminah and Aamina share the same unvowelled form in this dataset and are queued for human transliteration review.",
        "flags": ["direct_lexical_source_needed", "distinguish_from_aamna_آمنة", "candidate_variant_manual_review", "corrected_gendered_translation"],
        "variant_note": "Candidate transliteration pair with aamina; both currently record أمينة. Review vowelled forms and route policy before any merge.",
        "translations": {
            "arabic": ("أمينة", "أمينة، جديرة بالثقة، موثوقة"),
            "urdu": ("امینہ", "قابلِ اعتماد، امانت دار"),
            "persian": ("امین", "قابل اعتماد، امین"),
            "hindi": ("आमिना", "विश्वसनीय, भरोसेमंद"),
            "pashto": ("آمینه", "باور وړ، امانتداره"),
        },
    },
    "aamira": {
        "confidence": "LOW",
        "short": "Inhabited; flourishing (feminine form; provisional)",
        "primary": "The record maps Aamira to Arabic عامرة, the feminine form corresponding to عامر and conventionally glossed “inhabited” or “flourishing.” Direct lexical and personal-name sources are not recorded.",
        "explain": "The feminine form عامرة is also used by Aamirah in this dataset. The identical written form supports a candidate transliteration relationship, not an automatic merge.",
        "flags": ["direct_lexical_source_needed", "candidate_variant_manual_review", "gender_distribution_not_independently_sourced"],
        "variant_note": "Candidate transliteration pair with aamirah; both currently record عامرة. Keep routes separate pending human review.",
        "translations": {
            "arabic": ("عامرة", "عامرة، مأهولة، مزدهرة"),
            "urdu": ("عامرہ", "آباد، خوشحال، پھلتی پھولتی"),
            "persian": ("عامره", "آباد، شکوفا، پررونق"),
            "hindi": ("आमिरा", "आबाद, समृद्ध, फलती-फूलती"),
            "pashto": ("عامره", "آباده، سمسوره، پرمختللې"),
        },
    },
    "aamirah": {
        "confidence": "LOW",
        "short": "Inhabited; flourishing (feminine form; provisional)",
        "primary": "The record maps Aamirah to Arabic عامرة, the feminine form corresponding to عامر and conventionally glossed “inhabited” or “flourishing.” Direct lexical and personal-name sources are not recorded.",
        "explain": "The feminine form عامرة is also used by Aamira in this dataset. The identical written form supports a candidate transliteration relationship, not an automatic merge.",
        "flags": ["direct_lexical_source_needed", "candidate_variant_manual_review", "gender_distribution_not_independently_sourced"],
        "variant_note": "Candidate transliteration pair with aamira; both currently record عامرة. Keep routes separate pending human review.",
        "translations": {
            "arabic": ("عامرة", "عامرة، مأهولة، مزدهرة"),
            "urdu": ("عامرہ", "آباد، خوشحال، پھلتی پھولتی"),
            "persian": ("عامره", "آباد، شکوفا، پررونق"),
            "hindi": ("आमिरा", "आबाद, समृद्ध, फलती-फूलती"),
            "pashto": ("عامره", "آباده، سمسوره، پرمختللې"),
        },
    },
    "aamirat": {
        "confidence": "LOW",
        "short": "Flourishing women (feminine plural; provisional gloss)",
        "primary": "The record maps عامرات to a feminine plural form related to عامرة. A plural form and its lexical gloss do not establish use of Aamirat as a singular personal name; both claims need direct sourcing.",
        "explain": "The plural morphology should not be converted into a singular personal-name meaning. Exact usage and translation remain unverified.",
        "flags": ["direct_lexical_source_needed", "plural_form_name_usage_unverified"],
        "translations": {
            "arabic": ("عامرات", "نساء مزدهرات / عامرات"),
            "urdu": ("عامرات", "آباد اور خوشحال خواتین"),
            "persian": ("عامرات", "زنان آباد و شکوفا"),
            "hindi": ("आमिरात", "आबाद और समृद्ध महिलाएँ"),
            "pashto": ("عامرات", "آبادې او سمسورې ښځې"),
        },
    },
    "aamirul": {
        "confidence": "LOW",
        "unresolved": True,
        "clear_form": True,
        "short": "Meaning not verified",
        "primary": "No source in this record establishes an Arabic form, language, lexical meaning, or gender for the exact spelling Aamirul. The prior meaning is not retained as a factual gloss.",
        "explain": "The Latin spelling alone does not establish a root or original script. A direct source for the exact form is required before assigning a meaning.",
        "gender": "Unknown",
        "flags": ["exact_lexical_form_unverified", "unsupported_gloss_removed", "personal_name_attestation_not_independently_sourced"],
        "translations_unverified": True,
    },
    "aamiya": {
        "confidence": "LOW",
        "unresolved": True,
        "clear_form": True,
        "short": "Meaning not verified",
        "primary": "No direct source identifies the exact spelling Aamiya with a particular Arabic form or establishes “colloquial” as its personal-name meaning. Language, origin, and name use remain unresolved.",
        "explain": "A possible resemblance to the Arabic adjective عامية is not sufficient to establish the spelling or a given-name meaning. No such derivation is asserted here.",
        "gender": "Unknown",
        "flags": ["exact_lexical_form_unverified", "unsupported_name_gloss_removed", "direct_lexical_source_needed"],
        "translations_unverified": True,
    },
    "aamla": {
        "confidence": "LOW",
        "unresolved": True,
        "clear_form": True,
        "short": "Meaning not verified",
        "primary": "The exact form, language, and meaning of Aamla are not established by a direct source in this record. No Arabic, South Asian, or other derivation is asserted from the Latin spelling alone.",
        "explain": "The prior placeholder gloss is removed. A direct lexical or biographical source for the exact spelling is needed before assigning an origin or meaning.",
        "gender": "Unknown",
        "flags": ["exact_lexical_form_unverified", "unsupported_gloss_removed", "personal_name_attestation_not_independently_sourced"],
        "translations_unverified": True,
    },
    "aamna": {
        "confidence": "LOW",
        "short": "Safe; secure; free from fear (provisional gloss)",
        "primary": "The record maps Aamna to Arabic آمنة, conventionally associated with safety or security. The form differs from أمينة (“trustworthy”); no direct dictionary source or independent frequency data is recorded here.",
        "explain": "آمنة and أمينة are distinct written forms with different conventional glosses. The exact Latin spelling and personal-name use still require source-specific review.",
        "flags": ["direct_lexical_source_needed", "distinguish_from_aamina_أمينة", "gender_distribution_not_independently_sourced"],
    },
    "adel": {
        "confidence": "LOW",
        "short": "Just; fair (provisional gloss)",
        "primary": "The record maps Adel to Arabic عادل, conventionally glossed “just” or “fair.” No direct lexicon citation is recorded, and the same Arabic form appears under Adil in this dataset; the spelling relationship is a candidate variant, not a decision to merge.",
        "explain": "The lexical form and root should be checked against a direct dictionary. The shared Arabic spelling with Adil does not establish identical community usage or canonical routes.",
        "flags": ["direct_lexical_source_needed", "candidate_variant_manual_review", "gender_distribution_not_independently_sourced"],
        "variant_note": "Candidate transliteration pair with adil; both currently record عادل. Keep routes separate pending human review.",
    },
    "adem": {
        "confidence": "MEDIUM",
        "short": "Qur'anic personal name آدم; etymology not asserted",
        "primary": "The Arabic personal name آدم is named in the Qur'an, including 2:31 and 3:33. Adem is a Latin spelling used for this form in some languages; this scriptural attestation does not establish a single etymology for the name or its frequency in any community.",
        "explain": "The Qur'anic text establishes the Arabic personal name آدم. The popular gloss “man/human being” is not treated here as a settled etymology; the Latin spelling Adem is a transliteration/usage claim that needs separate evidence.",
        "flags": ["quranic_personal_name_attested", "etymology_not_established", "exact_latin_spelling_usage_not_independently_sourced", "candidate_variant_manual_review"],
        "gender_confidence": "HIGH",
        "etymological_meaning": "Etymology not asserted",
        "etymology_explanation": "The cited Qur'anic verses attest the Arabic personal name آدم; they do not establish a single etymological derivation for it or the frequency of the Latin spelling Adem.",
        "variant_note": "Candidate spelling variant of Adam for the Arabic form آدم; verify community spelling and canonical-route policy before any consolidation.",
        "quran": "adam",
        "translations": {
            "arabic": ("آدم", "اسم شخصي قرآني؛ الاشتقاق غير محسوم في هذا السجل"),
            "urdu": ("آدم", "قرآنی شخصی نام؛ اس اندراج میں اشتقاقی معنی متعین نہیں"),
            "persian": ("آدم", "نام شخصی قرآنی؛ ریشه‌شناسی در این مدخل اثبات نشده است"),
            "hindi": ("आदम", "क़ुरआनी व्यक्तिनाम; व्युत्पत्ति यहाँ स्थापित नहीं है"),
            "pashto": ("آدم", "قرآني شخصي نوم؛ د نوم ریښه دلته نه ده ثابته شوې"),
        },
    },
    "aden": {
        "confidence": "LOW",
        "unresolved": True,
        "clear_form": False,
        "short": "Arabic word-form عدن; personal-name meaning unverified",
        "primary": "The record maps Aden to Arabic عدن. The phrase جَنَّاتُ عَدْنٍ (“gardens of ʿAdn”) occurs in Qur'an 9:72, but a scriptural word occurrence is not evidence that Aden is a Qur'anic personal name or that “Eden” is its settled modern name meaning.",
        "explain": "The cited verse supports the phrase and word occurrence only. The exact transliteration, lexical gloss, and personal-name use require separate lexical and naming evidence.",
        "flags": ["quranic_word_occurrence_not_personal_name_attestation", "direct_lexical_source_needed", "personal_name_attestation_not_independently_sourced"],
        "quran": "adn",
        "translations_unverified": True,
    },
    "adena": {
        "confidence": "LOW",
        "unresolved": True,
        "clear_form": True,
        "short": "Meaning not verified",
        "primary": "No direct source establishes the language, script, meaning, or gender for the exact spelling Adena. The prior gloss “Aisha” is unsupported and is not retained.",
        "explain": "Adena is not equated with Aisha or another similar-looking name without evidence. The exact form and any name-bearer history remain unresolved.",
        "gender": "Unknown",
        "flags": ["exact_lexical_form_unverified", "unsupported_gloss_removed", "possible_name_conflation_prevented"],
        "translations_unverified": True,
    },
    "adha": {
        "confidence": "LOW",
        "unresolved": True,
        "clear_form": False,
        "short": "Exact name sense not verified",
        "primary": "The Latin spelling Adha has not been tied to a single intended Arabic form by a direct source. The form currently recorded as أضحى has contextual Arabic uses; it is not sufficient evidence to define the name as “sacrifice” or to equate it with Eid al-Adha.",
        "explain": "The current Arabic candidate and the proposed sacrifice/forenoon glosses need direct lexical and naming sources. They are kept separate from the name's religious status.",
        "gender": "Unknown",
        "flags": ["exact_transliteration_not_independently_sourced", "form_meaning_needs_direct_lexicon", "religious_association_not_lexical_proof"],
        "translations_unverified": True,
    },
    "adham": {
        "confidence": "LOW",
        "short": "Dark; black (provisional gloss)",
        "primary": "The record maps Adham to Arabic أدهم, conventionally associated with “dark” or “black,” especially in descriptions of a dark-colored horse. No direct lexicon citation or independent evidence for this exact Latin spelling's name use is recorded.",
        "explain": "The lexical gloss should be checked against a direct Arabic source; it does not establish popularity, gender distribution, or any personal trait of a bearer.",
        "flags": ["direct_lexical_source_needed", "personal_name_attestation_not_independently_sourced"],
    },
    "adhara": {
        "confidence": "LOW",
        "unresolved": True,
        "clear_form": True,
        "short": "Meaning not verified",
        "primary": "No direct source establishes the intended language, script, or meaning of the exact spelling Adhara. The previous “star” and “moon” glosses are not supported by evidence in this record and are removed.",
        "explain": "Similar-looking forms in other languages do not establish an Arabic origin. The exact form and modern personal-name use remain unresolved.",
        "gender": "Unknown",
        "flags": ["exact_lexical_form_unverified", "unsupported_glosses_removed", "personal_name_attestation_not_independently_sourced"],
        "translations_unverified": True,
    },
    "adi": {
        "confidence": "LOW",
        "unresolved": True,
        "clear_form": False,
        "short": "Meaning not verified for the exact spelling",
        "primary": "The record's Arabic form عادي does not support the gloss “friend, companion”; that gloss would require a different form and independent evidence. The exact intended source form for the Latin spelling Adi is unresolved, so no lexical meaning is asserted.",
        "explain": "The Arabic candidate عادي and the proposed companion gloss are mismatched. This record does not silently replace it with another similar-looking Arabic form.",
        "gender": "Unknown",
        "flags": ["form_meaning_mismatch", "exact_lexical_form_unverified", "unsupported_gloss_removed", "personal_name_attestation_not_independently_sourced"],
        "translations_unverified": True,
    },
    "adib": {
        "confidence": "LOW",
        "short": "Cultured; refined; literary (provisional gloss)",
        "primary": "The record maps Adib to Arabic أديب, conventionally glossed “cultured,” “refined,” or “a person of letters.” A direct dictionary source and independent evidence for this exact Latin spelling as a personal name are not listed; the claims remain provisional.",
        "explain": "The feminine form أديبة is a separate grammatical form. Root and morphology should be confirmed against a direct lexicon; no special scriptural status is inferred.",
        "flags": ["direct_lexical_source_needed", "personal_name_attestation_not_independently_sourced"],
    },
    "adiba": {
        "confidence": "LOW",
        "short": "Cultured; refined (feminine form; provisional gloss)",
        "primary": "The record maps Adiba to Arabic أديبة, the feminine form corresponding to أديب, conventionally glossed “cultured” or “refined.” No direct lexicon citation or independent name-usage source is recorded.",
        "explain": "The Arabic translation in the prior record used masculine wording; this review corrects it to a feminine form. Adiba and Adibah share the recorded Arabic form and are queued for transliteration review.",
        "flags": ["direct_lexical_source_needed", "corrected_gendered_translation", "candidate_variant_manual_review"],
        "variant_note": "Candidate transliteration pair with adibah; both currently record أديبة. Keep routes separate pending human review.",
        "translations": {
            "arabic": ("أديبة", "أديبة، مهذّبة، مثقّفة"),
            "urdu": ("ادیبہ", "مہذب، باادب، تعلیم یافتہ"),
            "persian": ("ادیبه", "فرهیخته، باادب"),
            "hindi": ("अदीबा", "सुसंस्कृत, शिष्ट, शिक्षित"),
            "pashto": ("ادیبه", "باادبه، پوهه"),
        },
    },
}

# Same feminine Arabic form; the records remain separate pending route review.
PATCHES["adiba"] = {
    "confidence": "LOW",
    "short": "Cultured; refined (feminine form; provisional gloss)",
    "primary": "The record maps Adiba to Arabic أديبة, the feminine form corresponding to أديب, conventionally glossed “cultured” or “refined.” No direct lexicon citation or independent name-usage source is recorded.",
    "explain": "The Arabic translation in the prior record used masculine wording; this review corrects it to a feminine form. Adiba and Adibah share the recorded Arabic form and are queued for transliteration review.",
    "flags": ["direct_lexical_source_needed", "corrected_gendered_translation", "candidate_variant_manual_review"],
    "variant_note": "Candidate transliteration pair with adibah; both currently record أديبة. Keep routes separate pending human review.",
    "translations": {
        "arabic": ("أديبة", "أديبة، مهذّبة، مثقّفة"),
        "urdu": ("ادیبہ", "مہذب، باادب، تعلیم یافتہ"),
        "persian": ("ادیبه", "فرهیخته، باادب"),
        "hindi": ("अदीबा", "सुसंस्कृत, शिष्ट, शिक्षित"),
        "pashto": ("ادیبه", "باادبه، پوهه"),
    },
}

QURAN_SOURCES = {
    "adem": [
        "Qur'an 2:31 — https://quran.com/2/31 — names Adam in the narrative; the verse supports textual attestation, not a modern frequency claim.",
        "Qur'an 3:33 — https://quran.com/3/33 — names Adam among those chosen; this supports the Arabic personal-name attestation only.",
    ],
    "aden": [
        "Qur'an 9:72 — https://quran.com/9/72 — contains the phrase جَنَّاتُ عَدْنٍ; this is a word-form occurrence, not a personal-name attestation.",
    ],
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _safe_script_status(d: dict[str, Any], patch: dict[str, Any], slug: str) -> None:
    if not patch.get("unresolved"):
        return
    et = d["etymology"]
    clear_form = patch.get("clear_form", False)
    if clear_form:
        et.update({
            "primary_language": "Unverified",
            "lexical_form": "",
            "root": "",
            "root_transliteration": "",
            "morphology": "Not established for the exact Latin spelling.",
            "etymological_meaning": "Not established",
            "root_family": [],
            "feminine_form": None,
            "etymology_explanation": "No language, lexical form, or root is established for the exact recorded spelling.",
            "etymology_confidence": "LOW",
        })
        d["language"].update({
            "primary": "Unverified",
            "associated_languages": [],
            "language_notes": {
                "primary": "No source establishes the language or original-script form represented by this spelling.",
                "usage": "A Latin spelling alone is insufficient to determine origin or script.",
            },
            "language_confidence": "LOW",
        })
        d["origin"].update({
            "primary_origin": "Unverified",
            "origin_confidence": "LOW",
            "origin_explanation": "The linguistic origin is not established from the evidence recorded here.",
            "cultural_transmission": [],
        })
        d["name_variants"]["script_forms"] = []
        d["pronunciation"]["scripts"]["arabic"] = ""
    else:
        et["primary_language"] = "Unverified"
        et["etymology_confidence"] = "LOW"
        et["root"] = ""
        et["root_transliteration"] = ""
        et["root_family"] = []
        et["feminine_form"] = None
        et["morphology"] = "Candidate Arabic-script form; morphology is not established for the exact Latin spelling."
        et["etymological_meaning"] = "Not established for the exact Latin spelling"
        et["etymology_explanation"] = "The Arabic form currently recorded is only a candidate for this Latin spelling; its identification and any root analysis require direct evidence."
        d["language"].update({
            "primary": "Unverified",
            "associated_languages": ["Arabic (candidate form only)"],
            "language_notes": {
                "primary": "An Arabic-script candidate is present, but the exact relationship to the Latin spelling is not established.",
                "usage": "Do not treat a candidate script form as a verified transliteration or a separate name origin.",
            },
            "language_confidence": "LOW",
        })
        d["origin"].update({
            "primary_origin": "Unverified",
            "origin_confidence": "LOW",
            "origin_explanation": "The recorded Arabic-script form is a candidate only; the origin of the exact Latin spelling remains unverified.",
            "cultural_transmission": [],
        })
        d["pronunciation"]["scripts"]["arabic"] = et.get("lexical_form", "")
        d["name_variants"]["script_forms"] = [et["lexical_form"]] if et.get("lexical_form") else []

    note = f"No verified original-script form is recorded for {d['name']}."
    if patch.get("clear_form"):
        for locale, item in d["translations"].items():
            item.update({"name": d["name"], "script": d["name"], "meaning": "Not verified", "long_meaning": note, "native_review_required": True})
    else:
        for locale, item in d["translations"].items():
            item.update({"name": d["name"], "script": d["name"], "meaning": "Not verified", "long_meaning": note, "native_review_required": True})
    d["translations"]["english"]["long_meaning"] = patch["primary"]
    d["name_variants"]["variant_notes"] = patch.get("variant_note", "The exact source form remains unverified; no variant relationship is asserted.")
    d["identity"]["name_status"] = "requires_manual_verification"


def _apply_translation_overrides(d: dict[str, Any], patch: dict[str, Any]) -> None:
    overrides = patch.get("translations", {})
    for locale, (script, meaning) in overrides.items():
        item = d["translations"][locale]
        item["name"] = script
        item["script"] = script
        item["meaning"] = meaning
        item["long_meaning"] = f"{d['name']} ({script}) — {meaning}. Editorial translation draft; native-speaker review is required."
        item["native_review_required"] = True


def _answer_faq(d: dict[str, Any], patch: dict[str, Any], item: dict[str, Any]) -> str:
    name = d["name"]
    question = " ".join(item["q"].casefold().split())
    et = d["etymology"]
    language = et["primary_language"]
    form = et["lexical_form"]
    root = et["root"]
    if question.startswith("what does "):
        return d["core_meaning"]["primary_meaning"]
    if question.startswith("what is the origin"):
        if language == "Unverified":
            return f"The language and linguistic origin of the exact spelling {name} are not established in this record."
        return f"The record associates the form {form} with {language}; the exact Latin transliteration, personal-name use, and frequency are separate claims and remain unverified."
    if question.startswith("is ") and " an arabic name" in question:
        if language == "Unverified":
            return f"The exact spelling {name} has not been independently identified with a verified Arabic form."
        return f"The record lists {form} as the Arabic-script form, but its match to this exact Latin spelling and personal-name use are not independently sourced."
    if "root" in question:
        if root:
            return f"The record provisionally associates the listed form with root {root}; a direct lexicon citation is still needed."
        return "No root is asserted here because the exact lexical form or root analysis is not established."
    if question.startswith("is ") and "islamic name" in question:
        return "Muslim cultural use and religious status are separate claims. This record does not establish a religious recommendation or issue a naming ruling."
    if "quranic" in question or "qur'anic" in question:
        return d["religion"]["quranic_status"]["note"]
    if "urdu" in question:
        tr = d["translations"]["urdu"]
        if tr["meaning"] == "Not verified":
            return "A verified Urdu-script form and Urdu meaning are not established for this exact spelling."
        return f"The record lists the Urdu rendering “{tr['meaning']}” as an editorial draft; native-speaker review is required."
    if "pronounc" in question:
        guide = d["pronunciation"].get("romanized") or name
        return f"“{guide}” is only a romanized pronunciation guide; no verified IPA is recorded."
    if "boy's or girl's" in question or "gender" in question:
        if d.get("slug") == "adem":
            return "The Qur'anic bearer Adam is male; this establishes the historical figure's gender, not gender-frequency data for the Latin spelling Adem."
        gender = d["identity"].get("gender", "Unknown")
        if gender == "Unknown":
            return "Gender use is not established in this record; the classification is therefore recorded as Unknown."
        return f"The record provisionally classifies {name} as {gender.lower()}; no source-scoped gender-frequency data is asserted."
    return item.get("a", "")


def _apply_review(d: dict[str, Any], slug: str) -> dict[str, Any]:
    patch = PATCHES[slug]
    d = copy.deepcopy(d)
    cm = d["core_meaning"]
    cm["short_meaning"] = patch["short"]
    cm["primary_meaning"] = patch["primary"]
    cm["literal_meaning"] = patch["short"]
    cm["meaning_explanation"] = patch["explain"]
    cm["meaning_confidence"] = patch["confidence"]

    identity = d["identity"]
    identity["gender"] = patch.get("gender", identity.get("gender", "Unknown"))
    identity["gender_confidence"] = patch.get("gender_confidence", "LOW")
    identity["gender_note"] = (
        "The Qur'anic bearer Adam is male; this establishes the historical figure's gender, not gender-frequency data for the Latin spelling Adem."
        if patch.get("quran") == "adam"
        else "This is a provisional database classification; source-specific registration or gender-distribution evidence is not recorded in this review."
    )

    _safe_script_status(d, patch, slug)
    d["etymology"]["etymology_confidence"] = patch["confidence"] if not patch.get("unresolved") else "LOW"
    if not patch.get("unresolved"):
        if patch.get("morphology"):
            d["etymology"]["morphology"] = patch["morphology"]
        elif patch.get("quran") == "adam":
            d["etymology"]["morphology"] = "Qur'anic proper name آدم; no root or historical etymology is asserted in this review."
        else:
            d["etymology"]["morphology"] = "Lexical/root analysis is provisional pending a direct source; no personal-name derivation is asserted."
        if patch.get("etymological_meaning"):
            d["etymology"]["etymological_meaning"] = patch["etymological_meaning"]
        elif patch.get("quran") == "adam":
            d["etymology"]["etymological_meaning"] = "Etymology not asserted"
        else:
            d["etymology"]["etymological_meaning"] = cm["short_meaning"]
        d["etymology"]["etymology_explanation"] = patch.get(
            "etymology_explanation",
            "The recorded lexical form and any root analysis remain provisional until checked against a direct source; lexical form alone does not establish personal-name usage.",
        )
    d["semantic_field"]["primary_semantic_domain"] = cm["short_meaning"]
    d["semantic_field"]["related_concepts"] = []
    if patch.get("unresolved"):
        d["language"]["language_confidence"] = "LOW"
        d["origin"]["origin_confidence"] = "LOW"
    else:
        d["language"]["language_confidence"] = "MEDIUM" if patch["confidence"] in {"HIGH", "MEDIUM"} else "LOW"
        d["origin"]["origin_confidence"] = "MEDIUM" if d["etymology"]["primary_language"] == "Arabic" else "LOW"
    d["origin"]["origin_explanation"] = (
        "The record identifies an Arabic lexical form, but personal-name attestation, "
        "frequency, and regional gender distribution are not established by that form alone."
        if d["etymology"]["primary_language"] == "Arabic"
        else "No source establishes the language or personal-name origin of the exact Latin spelling."
    )
    d["origin"]["cultural_transmission"] = []
    if not patch.get("unresolved"):
        d["language"]["language_notes"]["usage"] = "The recorded script form does not establish modern name use; any Latin rendering and cultural distribution require separate evidence."

    # Scriptural status is deliberately kept separate from a lexical word
    # occurrence and from use as a personal name.
    name = d["name"]
    d["religion"]["quranic_status"] = {
        "is_quranic": False,
        "status": "not_verified",
        "note": f"No source in this record establishes {name} as a Qur'anic personal name. A lexical form or ordinary word occurrence is not by itself a personal-name attestation.",
    }
    if patch.get("quran") == "adam":
        d["religion"]["quranic_status"] = {
            "is_quranic": True,
            "status": "personal_name_attested_in_quran",
            "note": "The Arabic personal name آدم is named in Qur'an 2:31 and 3:33. This establishes textual name attestation, not a settled etymology or modern frequency for the Latin spelling Adem.",
        }
    elif patch.get("quran") == "adn":
        d["religion"]["quranic_status"] = {
            "is_quranic": False,
            "status": "word_form_occurs_not_as_personal_name",
            "note": "The phrase جَنَّاتُ عَدْنٍ occurs in Qur'an 9:72. This is a word-form occurrence, not evidence that Aden is a Qur'anic personal name.",
        }
    if patch.get("quran") == "adam":
        d["religion"]["prophetic_status"] = {
            "status": "not_assessed_in_this_review",
            "note": "This focused pass records Qur'anic name attestation but does not assess theological or biographical claims about prophetic status.",
        }
    d["religion"]["primary_association"] = "Not independently established"
    d["religion"]["religion_confidence"] = "LOW"
    d["religion"]["religious_status"] = "No specific religious status is established by this record; this is not a naming ruling."
    d["religion"]["religious_explanation"] = "Lexical form, Muslim cultural use, scriptural occurrence, and religious recommendation are distinct claims; only claims with separate evidence should be treated as established."
    d["islamic_naming_context"].update({
        "context": "No source-scoped modern naming-use data is recorded in this review.",
        "interpretation": "No religious or symbolic interpretation is assigned from a lexical gloss alone.",
        "important_distinction": "A lexical or scriptural word occurrence does not by itself establish personal-name usage or religious recommendation. This record is descriptive, not a religious ruling.",
    })
    d["cultural_context"].update({
        "primary_cultural_associations": ["Arabic lexical form"] if d["etymology"]["primary_language"] == "Arabic" else [],
        "cultural_meaning": "Personal-name cultural meaning is not independently sourced in this review.",
        "personal_name_interpretation": "No symbolic reading is asserted beyond the provisional lexical description.",
        "interpretation_warning": "Cultural interpretation, dictionary meaning, and a bearer's character are separate claims.",
    })
    d["spiritual_meaning"].update({
        "status": "not_verified",
        "render": False,
        "meaning": "No separate spiritual meaning is established in this record.",
        "basis": None,
        "is_direct_religious_definition": False,
    })
    d["identity"]["name_status"] = (
        "scriptural_personal_name_attested_modern_usage_not_measured"
        if patch.get("quran") == "adam"
        else "requires_manual_verification"
        if patch.get("unresolved")
        else "name_use_not_independently_sourced"
    )

    d["modern_usage"] = {
        "status": "requires_frequency_data",
        "note": "No source-scoped personal-name registration or frequency data is recorded in this review.",
    }
    d["popularity"].update({"status": "not_measured", "render": False, "score": None, "by_region": [], "note": "No verified population or registration measure is recorded; no estimate is asserted."})
    d["celebrity_usage"].update({"status": "not_verified", "render": False, "items": [], "note": "No independently sourced bearer examples are included in this review."})
    d["real_world_usage"].update({"status": "not_verified", "render": False, "note": "No source-verified personal-name use story is included."})
    d["personality_associations"].update({"status": "not_verified", "render": False, "note": "No evidence links this name to personality traits."})
    d["hidden_personality_traits"].update({"status": "not_verified", "render": False, "note": "No evidence-based hidden traits are asserted."})
    d["numerology"].update({
        "status": "not_verified", "render": False, "lucky_number": None,
        "life_path_number": None, "ruling_planet": None, "lucky_day": None,
        "lucky_colors": [], "lucky_stone": None, "meaning": None,
        "note": "Numerology is not evidence-based and is not supplied as factual name content.",
    })
    d["lucky_attributes"].update({
        "status": "not_verified", "render": False, "lucky_number": None,
        "lucky_day": None, "lucky_colors": [], "lucky_stone": None,
        "ruling_planet": None, "note": "Lucky attributes are not evidence-based and are not supplied as factual name content.",
    })

    if patch.get("translations_unverified"):
        _safe_script_status(d, patch, slug)
    _apply_translation_overrides(d, patch)
    d["translations"]["english"]["meaning"] = cm["short_meaning"]
    d["translations"]["english"]["long_meaning"] = cm["primary_meaning"]
    d["translation_quality"]["confidence"] = "LOW"
    d["translation_quality"]["native_review_required"] = True
    d["translation_quality"]["note"] = "Localized renderings are editorial drafts; direct lexical support and native-speaker review remain separate requirements."

    additional_flags = ["native_translation_review_required"]
    if patch.get("quran") != "adam":
        additional_flags.append("personal_name_attestation_not_independently_sourced")
    flags = list(dict.fromkeys([*patch.get("flags", []), *additional_flags]))
    d["editorial_validation"].update({
        "needs_manual_verification": True,
        "flags": flags,
        "confidence": "LOW" if patch["confidence"] == "LOW" else "MEDIUM",
        "reviewed_by": "NameVerse evidence-led review; unverified claims retained as such",
        "reviewed_at": REVIEWED_AT,
    })
    d["content_quality"].update({
        "tier1_verified": False,
        "authenticity_flags": flags,
        "quality_score": None,
        "quality_score_basis": "No composite score is asserted. This review records source limitations, distinguishes lexical from naming claims, and preserves manual/native review requirements.",
    })
    d["provenance"].update({
        "pipeline": "NameVerse evidence-led Islamic verification review",
        "methodology": "Reconciled the recorded Arabic/Latin form and meaning fields, corrected clear form/translation mismatches, and separated lexical claims from name-use, gender, scriptural, and cultural claims. External lexical references were not independently rechecked unless explicitly listed.",
        "processed_at": f"{REVIEWED_AT}T00:00:00+00:00",
    })
    if patch.get("quran") == "adam":
        d["historical_context"].update({"status": "scriptural_text_attested", "note": "The Arabic personal name آدم is named in Qur'an 2:31 and 3:33; this does not establish modern frequency or a settled etymology for Adem."})
    elif patch.get("quran") == "adn":
        d["historical_context"].update({"status": "word_occurrence_attested", "note": "Qur'an 9:72 contains جَنَّاتُ عَدْنٍ; this is a word-form occurrence, not a personal-name biography."})
    else:
        d["historical_context"].update({"status": "not_verified", "note": "No separate, source-verified historical bearer or personal-name history is established in this review."})
    if "seo" in d:
        d["seo"]["seo_score"] = None
        d["seo"]["seo_score_basis"] = "No composite SEO score is asserted in this evidence-led review."

    sources = list(d.get("evidence", {}).get("sources", []))
    # Remove generated placeholder strings that described a claim as a source.
    sources = [s for s in sources if isinstance(s, str) and not s.strip().startswith(("http://", "https://")) and ("http://" in s or "https://" in s or "Lane" in s or "Al-Wasīṭ" in s)]
    sources.extend(QURAN_SOURCES.get(slug, []))
    sources = list(dict.fromkeys(sources))
    if slug != "aalam" and not QURAN_SOURCES.get(slug):
        sources = []
    traceable_urls = list(dict.fromkeys(
        url for source in sources for url in re.findall(r"https?://[^\s—]+", source)
    ))
    claim_evidence = []
    if slug == "aalam":
        for source in sources:
            claim_evidence.append({
                "claim": "Arabic lexical form عالم and world/creation senses; the sources do not establish personal-name frequency or gender distribution.",
                "source": (re.search(r"https?://[^\s—]+", source).group(0) if re.search(r"https?://[^\s—]+", source) else source),
                "status": "source_listed_not_independently_rechecked_in_this_pass",
            })
    elif slug in QURAN_SOURCES:
        for source in sources:
            claim_evidence.append({
                "claim": "Textual status of the recorded form, with the limitation stated in the source note.",
                "source": (re.search(r"https?://[^\s—]+", source).group(0) if re.search(r"https?://[^\s—]+", source) else source.split(" — ", 1)[0]),
                "status": "primary_text_reference_listed_not_rechecked_in_this_pass",
            })
    claim_evidence.append({
        "claim": (
            "Modern personal-name frequency, regional gender distribution, and native translation quality"
            if slug == "adem"
            else "Exact personal-name attestation, regional frequency, gender distribution, and native translation quality"
        ),
        "source": None,
        "status": "not_verified_manual_review_required",
    })
    d["evidence"] = {
        "sources": list(dict.fromkeys([*sources, *traceable_urls])),
        "verification_method": "This review reconciled internal form/meaning/translation fields and removed unsupported or placeholder source claims. Except for the listed Qur'anic text references and the two existing Aalam dictionary references, no external lexical source was independently checked in this pass.",
        "claim_evidence": claim_evidence,
        "claim_evidence_status": "SOURCE_LIMITS_RECORDED; PERSONAL_NAME_USAGE_AND_TRANSLATIONS_NOT_FULLY_VERIFIED",
    }

    if patch.get("variant_note"):
        d["name_variants"]["variant_notes"] = patch["variant_note"]
    d["faq"] = [{**item, "a": _answer_faq(d, patch, item)} for item in d.get("faq", [])]
    for node in d.get("structured_data", {}).get("@graph", []):
        if node.get("@type") == "FAQPage":
            node["mainEntity"] = [
                {"@type": "Question", "name": item["q"], "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
                for item in d["faq"]
            ]
        elif node.get("@type") == "DefinedTerm":
            node["description"] = f"{name} — {cm['short_meaning']}. See the record for evidence limits and review status."
    if "seo" in d:
        d["seo"]["description_paragraph"] = cm["primary_meaning"]
        d["seo"]["meta_description"] = f"{name}: {cm['short_meaning']}. Lexical and personal-name evidence are distinguished in this record."
        d["seo"]["canonical_url"] = f"https://nameverse.site/names/islamic/{slug}"
    if "seo_content" in d:
        d["seo_content"]["intro_paragraph"] = cm["primary_meaning"]
        d["seo_content"]["body_summary"] = cm["primary_meaning"]
    return d


def _load_rows() -> tuple[list[dict[str, str]], list[str]]:
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []
    return rows, fields


def _validate_targets(rows: list[dict[str, str]]) -> list[str]:
    by_slug = {row["slug"]: row for row in rows}
    errors: list[str] = []
    for slug in ALL_SLUGS:
        if slug not in by_slug:
            errors.append(f"Manifest missing {slug}")
            continue
        if by_slug[slug].get("status") not in {"PENDING", STATUS}:
            errors.append(f"{slug}: refusing unexpected prior status {by_slug[slug].get('status')!r}")
    return errors


def _check_record(d: dict[str, Any], slug: str) -> list[str]:
    errors: list[str] = []
    if d.get("slug") != slug:
        errors.append(f"{slug}: data slug mismatch")
    if d.get("editorial_validation", {}).get("reviewed_at") != REVIEWED_AT:
        errors.append(f"{slug}: review date missing")
    if d.get("content_quality", {}).get("tier1_verified") is not False:
        errors.append(f"{slug}: tier1 must remain false")
    if d.get("content_quality", {}).get("quality_score") is not None:
        errors.append(f"{slug}: unsupported composite quality score remains")
    if d.get("translation_quality", {}).get("native_review_required") is not True:
        errors.append(f"{slug}: native review flag missing")
    if d.get("popularity", {}).get("score") is not None or d.get("popularity", {}).get("render") is not False:
        errors.append(f"{slug}: unmeasured popularity is not suppressed")
    faq_nodes = [n for n in d.get("structured_data", {}).get("@graph", []) if n.get("@type") == "FAQPage"]
    if len(faq_nodes) != 1 or faq_nodes[0].get("mainEntity") != [
        {"@type": "Question", "name": item["q"], "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
        for item in d.get("faq", [])
    ]:
        errors.append(f"{slug}: FAQPage is not synchronized")
    canonical = d.get("seo", {}).get("canonical_url")
    if canonical != f"https://nameverse.site/names/islamic/{slug}":
        errors.append(f"{slug}: canonical URL mismatch")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows, fields = _load_rows()
    errors = _validate_targets(rows)
    if errors:
        print("Manifest validation failed:\n- " + "\n- ".join(errors))
        return 1
    by_slug = {row["slug"]: row for row in rows}

    if args.write:
        for slug in ALL_SLUGS:
            current = read_json(DATASET / f"{slug}.json")
            updated = _apply_review(current["data"], slug)
            current["data"] = updated
            write_json(DATASET / f"{slug}.json", current)
            row = by_slug[slug]
            if row["status"] not in {"PENDING", STATUS}:
                print(f"Refusing to reclassify already-reviewed record: {slug}")
                return 1
            row["status"] = STATUS
            row["batch"] = BATCH
        with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(f"Reviewed {len(GAP_SLUGS)} early-gap and {len(CONTINUATION_SLUGS)} continuation records.")
        return 0

    for slug in ALL_SLUGS:
        path = DATASET / f"{slug}.json"
        if not path.exists():
            errors.append(f"Missing file {path.relative_to(ROOT)}")
            continue
        record = read_json(path)
        d = record.get("data", {})
        errors.extend(_check_record(d, slug))
        expected = _apply_review(d, slug)
        if expected != d:
            errors.append(f"{slug}: persisted record differs from reproducible review transform")
        if by_slug[slug].get("status") != STATUS or by_slug[slug].get("batch") != BATCH:
            errors.append(f"{slug}: verification-manifest status is not {STATUS}")
    if errors:
        print("Review checks failed:\n- " + "\n- ".join(errors))
        return 1
    print(f"OK: {len(GAP_SLUGS)} gap records and {len(CONTINUATION_SLUGS)} continuation records are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
