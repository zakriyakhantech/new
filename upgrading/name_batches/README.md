# Demand-informed Islamic-name batch — October 2026

This directory contains the ten-record curation manifest used by the standalone `super-2.0` builder in `upgrading/scripts/add_demand_names.py`.

## Scope and safeguards

- The builder uses `upgrading/names_upgraded/islamic/aabid.json` as the architecture template and preserves its outer `schema_version`/`success`/`data` structure, exact `data` keys, and nested object-key shapes. The older `nv_validate.py` targets a different record shape and is not used for this batch.
- Before adding a record, it checks canonical names, filenames/slugs, identity spellings, Romanized variants, lexical forms, pronunciation script forms, and localized name/script forms against the main dataset. Latin comparison ignores case, punctuation, and diacritics. Arabic comparison ignores vowel marks/tatweel and normalizes common letter variants. Other writing systems retain their marks to avoid false collisions.
- It refuses to overwrite an existing non-identical file. Re-running `--write` is safe for records that exactly match the manifest.
- Meanings, linguistic origin, name usage, scriptural status, and popularity are separate claims with separate sources. Name-site root labels are not accepted without lexical corroboration.
- Popularity measures remain source-, place-, category-, metric-, and year-specific. QuranicNames percentages are relative visitor-search interest over the preceding three months described by that site's page; they are not birth shares. U.S. SSA-derived births/ranks and Turkish registrations are not combined into a global score. Every record has `popularity.score: null`.
- Non-English glosses and script renderings are editorial drafts; native-speaker review is still required. Numerology, lucky attributes, personality claims, and invented name stories are suppressed.

## Selected batch

| Name | Core lexical/contextual gloss | Documented usage signal (kept in its own scope) |
| --- | --- | --- |
| Yusra | Ease or facility; related root senses are kept distinct. | United States, 2025: SSA-derived rank #1,021 and 246 births, displayed by Nameberry. |
| Yumna | Right side/right hand; related good-fortune or blessing senses. | United States, 2025: SSA-derived rank #3,384 and 46 births, displayed by Nameberry. The page is labelled AI-written and is used only for the popularity figure, not etymology. |
| Samiha | Generous, magnanimous, gracious; forgiving/forbearing. | QuranicNames visitor audience, 2026: overall search rank #20, 62% relative interest. |
| Sariya | Night-travelling party; also a cloud or rain arriving at night. | QuranicNames visitor audience, 2026: overall #27 / 50%; Qur'anic-names list #19 / 53%. The source's S-R-A label is rejected; the lexical form is checked under س ر ي. |
| Abyan | Clearer, more evident, or more eloquent (comparative, not superlative). | QuranicNames visitor audience, 2026: unisex list #26 / 6% relative interest. Gender distribution is not quantified. |
| Tasmir | The verbal noun تَثْمِير (taṯmīr): making fruitful/productive or increasing. | QuranicNames visitor audience, 2026: overall #15 / 64%; Qur'anic-names list #11 / 69%. “Tasmir” is retained as the searched spelling but is not strict transliteration of ث. |
| Salwa | Consolation/comfort; also quail in classical and Qur'anic vocabulary. | United States, 2025: The Bump reports girls' name rank #4,860 (no birth count shown). The record uses lexical root س ل و, not the questionable S-L-A label on a name site. |
| Salsabil | A spring named Salsabil in Qur'an 76:18; deeper etymology is uncertain. | United States, 2025: SSA-derived rank #10,764 displayed by Nameberry; it is uncommon in that U.S. dataset. |
| Alparslan | Turkish compound: alp (“hero/brave”) + arslan (“lion”). | Türkiye, 2025: 7,651 boys, rank #1, reported from Interior Ministry data; Türkiye, 2024: official NVI count 8,304, rank #1. |
| Duru | Turkish word-name meaning “clear, lucid”; “pure” is a related gloss. | Türkiye, 2024: rank #10 / 3,389 in a secondary reproduction of official data; United States, 2025: SSA-derived rank #7,998 / 13 births as reported by a secondary source. |

These are evidence signals used to select a batch, not proof that all ten are globally “most in demand” or “most searched.” The source populations and measurement methods differ and are deliberately not ranked against one another.

## Build, test, and verify

From the repository root:

```bash
python3 upgrading/scripts/add_demand_names.py                 # dry-run collision audit
python3 -m unittest upgrading/scripts/test_add_demand_names.py -v
python3 upgrading/scripts/add_demand_names.py --write          # add only after checks pass
python3 upgrading/scripts/add_demand_names.py --check          # verify all ten persisted records
```

The builder has no third-party dependencies and makes no network calls. Source URLs, claim-level support, and limitations are committed in the manifest; generated record evidence is flattened into the existing `evidence.sources` format.
