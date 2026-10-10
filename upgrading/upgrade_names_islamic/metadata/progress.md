# Islamic names — nested-record pipeline progress

This file tracks only `upgrading/upgrade_names_islamic`. It is separate from `upgrading/PROGRESS.md` and `upgrading/names_upgraded/islamic`, which belong to a different output pipeline/schema.

| Field | Value |
|---|---|
| Records present | 2,100 |
| Batches completed | 21 |
| Latest batch | 21 — fahdah .. fareedah (100) |
| Next batch | 22 — fareeha .. fateem (100) |
| Updated | 2026-10-10T04:33:32Z |

## Batch history

| Batches | Range / status | Records |
|---|---|---:|
| 1–20 | Pre-existing curated batches; exact file set confirmed and validated | 2,000 |
| 21 | fahdah .. fareedah — complete | 100 |

Batch 21's manifest is [`batches/batch_021.json`](batches/batch_021.json). The builder now works without the ignored source snapshot and validates the batch names against `curated21.CUR`.

## Quality and review

- The full 2,100-record directory passes `nv_validate.py` with **0 structural failures**.
- The validator checks structure and script shape; it does **not** independently authenticate meanings or origins.
- Batch 21 replaced 54 glosses that conflicted with their own curation notes and withheld meanings for 6 uncertain/compound forms.
- Non-English translation drafts still require native-speaker review. Named lexical citations are required before publication.
