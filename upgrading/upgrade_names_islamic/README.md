# Islamic names — nested records

This directory contains the nested-record output built with `upgrading/scripts/nv_build.py`. Its local status is tracked in [`metadata/progress.md`](metadata/progress.md); do not confuse it with the separate `upgrading/names_upgraded/islamic` dataset and top-level `upgrading/PROGRESS.md`.

Batch 21 (`fahdah` through `fareedah`) is present and validated. Build it with:

```bash
python3 upgrading/scripts/build21.py
python3 upgrading/scripts/nv_validate.py out/islamic
```

`build21.py` can derive the name list from `curated21.CUR` when the ignored `work/batch21_src.json` snapshot is absent. Generated records are written to ignored `out/islamic`; installation into this directory is a separate reviewed step.

The validator is structural, not a lexical-authenticity check. Non-English glosses are drafts or deliberately omitted, and require native-speaker review. Add named lexical citations before publication.
