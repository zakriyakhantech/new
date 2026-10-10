# Islamic names — nested records

This directory contains nested-record output built with `upgrading/scripts/nv_build.py`. Its local status is tracked in [`metadata/progress.md`](metadata/progress.md); do not confuse it with the separate `upgrading/names_upgraded/islamic` dataset and top-level `upgrading/PROGRESS.md`.

Batches 21 (`fahdah`–`fareedah`) and 22 (`fareeha`–`fateem`) are present and validated. Build either batch with:

```bash
python3 upgrading/scripts/build21.py
python3 upgrading/scripts/nv_validate.py out/islamic
python3 upgrading/scripts/build22.py
python3 upgrading/scripts/nv_validate.py out/islamic
```

Both builders can derive their name lists from the corresponding curated table when the ignored source snapshot is absent. Generated records go to ignored `out/islamic`; installation into this directory is a separate reviewed step.

The validator is structural, not a lexical-authenticity check. Non-English glosses are drafts or deliberately omitted, and require native-speaker review. Add named lexical citations before publication.
