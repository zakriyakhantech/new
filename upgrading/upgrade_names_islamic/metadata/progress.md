# Islamic names — nested-record pipeline progress

This file tracks only `upgrading/upgrade_names_islamic`. It is separate from `upgrading/PROGRESS.md` and `upgrading/names_upgraded/islamic`, which belong to a different output pipeline/schema.

| Field | Value |
|---|---|
| Records present | 2,400 |
| Batches completed | 24 |
| Latest batch | 24 — ferhat .. ghadir (100) |
| Next batch | 25 — ghaffar .. guzel (100) |
| Updated | 2026-10-13T02:45:44Z |

## Batch history

| Batches | Range / status | Records |
|---|---|---:|
| 1–20 | Pre-existing curated batches; exact file set confirmed and validated | 2,000 |
| 21 | fahdah .. fareedah — complete | 100 |
| 22 | fareeha .. fateem — complete | 100 |
| 23 | fateema .. ferdous — complete | 100 |
| 24 | ferhat .. ghadir — complete | 100 |

Manifests: [`batch 21`](batches/batch_021.json), [`batch 22`](batches/batch_022.json), [`batch 23`](batches/batch_023.json), [`batch 24`](batches/batch_024.json). Each builder can derive its name list from its curated table when the ignored `work/batch*_src.json` snapshot is absent.

## Quality and review

- The full 2,400-record directory passes `nv_validate.py` with **0 structural failures**.
- The validator checks structure and script shape; it does **not** independently authenticate meanings or origins.
- Batch 21 corrected 54 English glosses and withheld meanings for 6 uncertain/compound forms. Batch 22 corrected 52 glosses and withheld meanings for 2 uncertain forms. Batch 23 corrected 78 glosses, reclassified 2 origins, corrected 6 script forms, and withheld meanings for 10 forms. Batch 24 corrected 11 glosses, corrected 2 script forms, reclassified 1 origin, and withheld meanings for 23 forms that are unverified or are surnames/compounds rather than lexical words.
- Non-English translation drafts still require native-speaker review. Named lexical citations are required before publication.
