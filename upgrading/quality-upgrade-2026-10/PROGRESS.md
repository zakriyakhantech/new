# NameVerse quality-upgrade progress (2026-10)

**Branch:** `quality-gates/all-name-records`  
**Dataset:** `upgrading/names_upgraded/islamic/`  
**Method:** lexicographic order; sequential batches of 25; file count is not the same as unique-name count.

## Current inventory snapshot

- Branch tree contains **6,592 likely name-record JSON files** after excluding three `PROGRESS_*.json` files.
- This is a filename count only. Unique-name/variant inventory and schema-wide validation remain pending.
- The older `upgrading/PROGRESS.md` contains inconsistent totals (5,471 in slice vs. 6,493 completed); do not use those totals as the current verified inventory until reconciled.

## Batch log

| Batch | Range | Files reviewed | Files changed | Status |
|---|---|---:|---:|---|
| 001 | `aaban.json` – `aadila.json` | 10 | 9 | Committed; structural spot-check passed; source/native review still outstanding where flagged |
| 002 | `aaf.json` – `aaiz.json` | 15 | 15 | Committed sequentially; spelling/canonical/slug checks passed; source/native review still outstanding where flagged |
| 003 | `aakif.json` – `aaliyah.json` | 15 | 15 | Committed sequentially; spelling/canonical/slug checks passed; source/native review still outstanding where flagged |

### Batch 001 notes

- Reviewed: `aaban.json`, `aabid.json`, `aabida.json`, `aabir.json`, `aabish.json`, `aad.json`, `aadam.json`, `aadhil.json`, `aadil.json`, `aadila.json`.
- Removed case-only duplicates from alternate-spelling arrays where present.
- Corrected inconsistent Pashto descriptions in the records edited in this batch and retained native-speaker review flags.
- Preserved each edited record's slug and canonical URL.
- Re-fetched edited records from GitHub and parsed them as JSON; normalized alternate-spelling arrays no longer contain case-only duplicates.
- This batch is **not** a claim that all source URLs, religious/historical claims, translations, or rendered pages have been independently verified.

## Next file

Continue after `aadila.json` with `aaf.json`, then proceed lexicographically. Do not skip records; log unchanged or unresolved records explicitly.


### Batch 002 notes

- Reviewed and updated: `aaf.json`, `aafak.json`, `aafaq.json`, `aafia.json`, `aafiya.json`, `aafreen.json`, `aaftab.json`, `aahil.json`, `aahoo.json`, `aaida.json`, `aaima.json`, `aaina.json`, `aaira.json`, `aaisha.json`, `aaiz.json`.
- Removed case-only alternate-spelling entries; retained the non-case spelling variants.
- Revised Pashto meanings to better align with the record's stated meaning or to explicitly preserve uncertainty where the exact spelling is not verified. These edits still require fluent Pashto review.
- Each updated record was re-fetched and parsed as JSON. The edited records' slugs and canonical URLs were preserved, and normalized alternate-spelling arrays had no case-only duplicates.
- FAQ arrays and FAQPage structured data were not edited in this batch; their parity was spot-checked for the 15 records before editing, but a full post-edit dataset-wide FAQ audit remains pending.

**Total through batch 002:** 25 files reviewed; 24 changed; 1 reviewed with no change. This is only the beginning of the repository-wide pass, not dataset completion.

## Next file

Continue after `aaiz.json` with `aakif.json`, then proceed lexicographically. Do not skip records; log unchanged or unresolved records explicitly.


### Batch 003 notes

- Reviewed and updated: `aakif.json`, `aakifah.json`, `aakil.json`, `aala.json`, `aalaa.json`, `aalam.json`, `aalee.json`, `aali.json`, `aalia.json`, `aaliah.json`, `aalif.json`, `aalim.json`, `aalima.json`, `aaliya.json`, `aaliyah.json`.
- Removed case-only duplicates from alternate-spelling arrays and normalized remaining transliteration variants.
- Revised Pashto meaning/explanation fields to align better with the stated lexical meaning and to preserve uncertainty for ambiguous spellings. Fluent Pashto review remains required.
- Each updated record was re-fetched and parsed as JSON; slug and canonical URL were preserved; normalized alternate-spelling arrays had no case-only duplicates.
- Source claims, transliteration relationships, translations, and deployed HTML are not fully verified by these structural checks.

**Total through batch 003:** 40 files reviewed; 39 changed; 1 reviewed with no change.

## Next file

Continue after `aaliyah.json` with `aalmas.json`, then proceed lexicographically. Do not skip records; log unchanged or unresolved records explicitly.
