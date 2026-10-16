# NameVerse repository-wide consistency upgrade

## Scope

The canonical editorial workspace remains `upgrading/names_upgraded/`. The separate `upgrades-namesv2/` tree is audited as a separate dataset; do not merge the two schemas or copy records between them without an explicit migration plan. Preserve filenames, slugs, routes, schema versions, and NameVerse-compatible field shapes.

## Weakest fields to address first

1. **Claim-level evidence:** Every important lexical, etymological, gender, historical, and religious claim needs a source that directly supports that claim. A URL by itself is not verification.
2. **Translation quality:** Keep provisional translations clearly marked for fluent/native review. Do not imply professional or native verification that has not happened.
3. **Cross-field consistency:** Align `data.name`, `identity.display_name`, `slug`, meaning fields, language/origin, translations, FAQ answers, and structured data. Potentially valid aliases are review items, not automatic renames.
4. **Verification/render flags:** Low-confidence or unsupported records must not be marked Tier 1 or have manual review disabled. Unverified sections should not be rendered as established fact.
5. **FAQ and structured data:** Keep FAQ questions/answers in the page record and FAQPage JSON-LD synchronized. Remove duplicated or contradictory questions only after reviewing their content.
6. **Popularity, numerology, personality and stories:** Do not manufacture data. Mark unsupported information as unmeasured/interpretive/unverified and keep it hidden from factual output.
7. **Scores and progress counts:** Scores must state their basis and must not stand in for evidence. Progress totals should be generated from manifests rather than hand-edited.

## Run the consistency audit

Report-only mode (recommended first):

```bash
python scripts/nameverse_repo_consistency.py
```

To scan a specific dataset root:

```bash
python scripts/nameverse_repo_consistency.py --root upgrading/names_upgraded
```

To scan both current data trees explicitly:

```bash
python scripts/nameverse_repo_consistency.py \
  --root upgrading/names_upgraded \
  --root upgrades-namesv2 \
  --report nameverse-consistency-report.json
```

After reviewing the report, the optional conservative repair mode can lower contradictory verification flags and hide uncertain sections:

```bash
python scripts/nameverse_repo_consistency.py \
  --root upgrading/names_upgraded \
  --root upgrades-namesv2 \
  --apply-safe-fixes \
  --report nameverse-consistency-report-after-fixes.json
```

Safe-fix mode deliberately does **not** invent meanings or sources, rewrite translations, delete FAQs, rename files/slugs, merge variants, or certify accuracy. Review the diff and rerun the audit after applying it. The JSON report records issue codes by file.

## Editorial batches

After the structural pass, edit name content in sequential batches of 25–50 records:

- verify the original script, transliteration, lexical meaning and morphology;
- check each important claim against a relevant source;
- distinguish dictionary meaning from personal-name attestation, religious status, cultural use and popularity;
- review every translation and mark unreviewed languages honestly;
- reconcile core meaning, translations, FAQs, SEO text and structured data;
- run JSON parsing and schema/route checks;
- record changed files, evidence, unresolved claims and possible aliases in a progress manifest.

Do not label all records “verified” simply because automated checks pass. Linguistic and historical accuracy still requires claim-specific evidence and qualified review.
