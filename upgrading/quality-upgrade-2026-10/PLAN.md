# NameVerse repository-wide quality upgrade plan

**Branch:** `quality-gates/all-name-records`  
**Dataset:** `upgrading/names_upgraded/islamic/`  
**Goal:** Improve every existing name record without changing route identity or inventing facts.

## Scope and counting rule

The current branch tree contains 6,592 JSON files in the Islamic folder excluding the three `PROGRESS_*.json` files. This is a filename-based inventory, not yet a verified unique-name count. Before completion, a manifest must classify every JSON as a name record, metadata, malformed, duplicate/variant candidate, or other.

## Priority order for each record

1. **Identity and route safety:** `name`, `slug`, filename, canonical URL, schema version, and required shape must be preserved.
2. **Core meaning:** verify the original-script lexical form, short meaning, long explanation, language, root/morphology, and confidence. Distinguish a word's dictionary meaning from a name's religious/cultural use.
3. **Evidence:** check each source URL and confirm that it supports the exact claim. A URL listed in JSON is not automatically verified evidence. Do not invent sources or claim verification that did not occur.
4. **Religious and historical claims:** Qur'an, hadith, prophets, companions, and historical bearers need specific evidence. Otherwise remove the unsupported claim or mark it unresolved.
5. **Translations:** align each language's meaning with the verified core meaning. Flag languages needing fluent-speaker review; do not label unreviewed text as native-verified.
6. **FAQs and structured data:** remove duplicate or repetitive questions, keep answers factual, and synchronize FAQ arrays with Schema.org FAQPage data.
7. **Spelling variants and duplicates:** remove case-only duplicates such as `Aabid` / `aabid`; retain meaningful transliteration variants; never merge separate records automatically.
8. **SEO and rendering:** preserve canonical URLs, make titles/descriptions accurate and distinctive, and avoid keyword stuffing or unsupported popularity claims. JSON alone cannot verify deployed HTML.
9. **Scores and publication flags:** scores must reflect evidence and unresolved issues; populated fields are not proof of accuracy. Keep manual-review flags where appropriate.

## Batch execution

- Process files in lexicographic filename order, in sequential batches of 25.
- For each file: read current branch version; edit only grounded issues; parse the resulting JSON; check identity/canonical preservation; check normalized spelling duplicates; check FAQ/structured-data parity; reread the committed version.
- Commit sequentially on this branch only. Never write to `main`.
- Update the manifest and batch report after each completed batch. Record unchanged files as reviewed, not upgraded.
- Keep a separate status for `changed`, `reviewed-no-change`, `needs-evidence`, `needs-native-review`, and `blocked`.
- Do not claim that a batch or dataset is fully verified merely because structural checks pass. Human/native review and source verification remain explicit when outstanding.

## First fields to improve

Identity spelling variants; core meaning and etymology consistency; religious-status cautions; English/Urdu/Pashto translation alignment; FAQ and FAQPage parity; source-claim status; canonical URL preservation; and honest validation flags.

## Definition of done

Every in-scope file has a manifest status, each factual claim is either supported by checked evidence or explicitly unresolved, structural checks pass, possible duplicates are reported for review, and all native-speaker/deployment checks still needed are clearly listed. No promise of absolute certainty.
