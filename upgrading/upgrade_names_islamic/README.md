# Islamic names — nested records

This directory contains nested-record output built with `upgrading/scripts/nv_build.py`. Its local status is tracked in [`metadata/progress.md`](metadata/progress.md); do not confuse it with the separate `upgrading/names_upgraded/islamic` dataset and top-level `upgrading/PROGRESS.md`.

Batches 21 (`fahdah`–`fareedah`), 22 (`fareeha`–`fateem`), and 23 (`fateema`–`ferdous`) are present and validated. Build any batch with:

```bash
python3 upgrading/scripts/build21.py
python3 upgrading/scripts/nv_validate.py out/islamic
python3 upgrading/scripts/build22.py
python3 upgrading/scripts/nv_validate.py out/islamic
python3 upgrading/scripts/build23.py
python3 upgrading/scripts/nv_validate.py out/islamic
```

Each builder can derive its name list from the corresponding curated table when the ignored source snapshot is absent. Generated records go to ignored `out/islamic`; installation into this directory is a separate reviewed step.

Batch 23 also carries a reviewed correction block at the end of `upgrading/scripts/curated23.py`: source glosses judged unsupported or approximate (for example the Fāṭima family, فاطمة, root f-ṭ-m) are replaced with corrected English-only gloss keys, two origins are reclassified, and truncated compounds or unmatched forms carry no asserted meaning.

The validator is structural, not a lexical-authenticity check. Non-English glosses are drafts or deliberately omitted, and require native-speaker review. Add named lexical citations before publication.
