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

### Batch 001 notes

- Reviewed: `aaban.json`, `aabid.json`, `aabida.json`, `aabir.json`, `aabish.json`, `aad.json`, `aadam.json`, `aadhil.json`, `aadil.json`, `aadila.json`.
- Removed case-only duplicates from alternate-spelling arrays where present.
- Corrected inconsistent Pashto descriptions in the records edited in this batch and retained native-speaker review flags.
- Preserved each edited record's slug and canonical URL.
- Re-fetched edited records from GitHub and parsed them as JSON; normalized alternate-spelling arrays no longer contain case-only duplicates.
- This batch is **not** a claim that all source URLs, religious/historical claims, translations, or rendered pages have been independently verified.

## Next file

Continue after `aadila.json` with `aaf.json`, then proceed lexicographically. Do not skip records; log unchanged or unresolved records explicitly.
