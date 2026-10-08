# -*- coding: utf-8 -*-
"""Small, source-backed v2 curation overlay.

Add one reviewed name at a time. These entries are deliberately separate from the
legacy 100-name curation batches and must not be inferred from the source page alone.
"""

GLOSSES = {
    "persian_month": {
        "en": "Aban; eighth month of the Persian solar calendar",
        "ur": "آبان؛ فارسی شمسی تقویم کا آٹھواں مہینہ",
        "fa": "آبان؛ هشتمین ماهِ تقویم خورشیدی",
        "hi": "आबान; फ़ारसी सौर कैलेंडर का आठवाँ महीना",
        "ps": "آبان؛ د فارسي لمریز کال اتمه میاشت",
        "ar": "آبان؛ الشهر الثامن في التقويم الفارسي الشمسي",
    },
}

# Fields: Arabic, Urdu, Persian, Hindi, Pashto, gloss key, origin, gender,
# lexical/morphology note, Quranic note, confidence, editorial/source note.
CUR = {
    "aaban": (
        None,
        "آبان",
        "آبان",
        "आबान",
        "آبان",
        "persian_month",
        "Persian",
        "Unknown",
        "Persian calendar month name; no additional root analysis asserted.",
        "Not assessed as a Quranic personal name.",
        "high",
        "Dehkhoda Dictionary defines آبان as the eighth month of the Persian solar year. This supports the lexical/calendar meaning only; name-use and gender are not established by that entry.",
    ),
}
