# Islamic names — nested records

This directory contains nested-record output built with `upgrading/scripts/nv_build.py`. Its local status is tracked in [`metadata/progress.md`](metadata/progress.md); do not confuse it with the separate `upgrading/names_upgraded/islamic` dataset and top-level `upgrading/PROGRESS.md`.

Batches 21 (`fahdah`–`fareedah`), 22 (`fareeha`–`fateem`), 23 (`fateema`–`ferdous`), and 24 (`ferhat`–`ghadir`) are present and validated. Build any batch with:

```bash
python3 upgrading/scripts/build21.py
python3 upgrading/scripts/nv_validate.py out/islamic
python3 upgrading/scripts/build22.py
python3 upgrading/scripts/nv_validate.py out/islamic
python3 upgrading/scripts/build23.py
python3 upgrading/scripts/nv_validate.py out/islamic
python3 upgrading/scripts/build24.py
python3 upgrading/scripts/nv_validate.py out/islamic
```

Each builder can derive its name list from the corresponding curated table when the ignored source snapshot is absent. Generated records go to ignored `out/islamic`; installation into this directory is a separate reviewed step.

Batches 23 and 24 also carry reviewed correction blocks at the end of `upgrading/scripts/curated23.py` and `curated24.py`:

- Batch 23: source glosses judged unsupported or approximate (the Fāṭima family فاطمة / f-ṭ-m, the f-w-z victory family, the f-y-ḍ generosity family, the faḍl family) are replaced with corrected English-only gloss keys, two origins are reclassified, six source script forms are corrected, and truncated compounds or unmatched forms carry no asserted meaning.
- Batch 24: gloss keys that did not match the reviewed note are re-keyed (Farhād, فروغ forough, fuzail/Fuḍayl, gamze, fiza, ghadi), four rows recorded without a gloss are given their reviewed sense (fusun, galawezh, galila, gawdat), two script forms are corrected, one origin is reclassified (galawezh is Kurdish, not Arabic), and rows with no lexical meaning (including the surname gaddafi and the personal name firnas) carry none.

The next batch is 25 (`ghaffar`–`guzel`).

The validator is structural, not a lexical-authenticity check. Non-English glosses are drafts or deliberately omitted, and require native-speaker review. Add named lexical citations before publication.
