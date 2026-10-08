# Islamic names — v2

The `islamic/` directory contains the second-pass JSON records. Work is intentionally processed **one source name per batch**, with a validation, commit, and push before moving to the next source name.

## Batch 001

- Source entry reviewed: `aaban`
- Output: [`islamic/aaban.json`](islamic/aaban.json)
- Named lexical source: Dehkhoda Dictionary entry for آبان, which identifies it as the eighth month of the Persian solar year.
- Name-use and gender are not established by that dictionary entry; gender is left unknown.
- Non-English renderings are marked as drafts requiring native-speaker review. The record is not marked ready for publication.

## Workflow

`metadata/progress.json` records the next source cursor and batch number. Build the next single-name batch only after the current one has been reviewed and pushed:

```bash
python upgrading/scripts/build_names_v2_batch.py --batch 1
python upgrading/scripts/nv_validate.py upgrades-namesv2/islamic
```

The builder enforces one source entry per batch and refuses to overwrite an existing batch manifest or record. It distinguishes an emitted JSON page from an alias decision or a source hold. Holds are not conclusions that a name does not exist. Original source JSON files are never deleted or edited.

## Evidence and review policy

- Named references in each JSON record support only the claims listed under `evidence.source_references`.
- Dictionary evidence for a lexical meaning does not establish that the spelling is a common given name, its gender distribution, popularity, or religious suitability.
- Non-English translations require qualified native-speaker review; they are not marked verified.
- Merge only explicit same-name/transliteration variants with matching script forms and origin. Keep a ledger in `metadata/alias_ledger.csv`.
- Keep unsupported forms in `metadata/source_holds.csv` for later evidence review.
- `nv_validate.py` checks structure and script shape; it is not an authenticity check.
