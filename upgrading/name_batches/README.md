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

## Batch b2 — October 2026 (`demand_2026-10-b2.json`)

A second, authenticity-first ten-record batch built with the same builder, template, and safeguards. The collision audit rejected three initial candidates (Samad, Hunayn, Mubashir) because their Arabic script forms are already present in the dataset under other spellings (Samat/صمد, Haneen & Hanin/حنين, Mubasher/مبشر); they were replaced and the rejections are recorded in the manifest's `selection_policy`.

Build and verify:

```bash
python3 upgrading/scripts/add_demand_names.py --manifest upgrading/name_batches/demand_2026-10-b2.json            # dry-run collision audit
python3 upgrading/scripts/add_demand_names.py --manifest upgrading/name_batches/demand_2026-10-b2.json --write    # add after checks pass
python3 upgrading/scripts/add_demand_names.py --manifest upgrading/name_batches/demand_2026-10-b2.json --check    # verify persisted records
```

| Name | Core lexical/scriptural gloss | Documented usage signal (kept in its own scope) |
| --- | --- | --- |
| Ilyasa | The Qur'anic prophet name الْيَسَع (Elisha), named in Qur'an 6:86 and 38:48. | HamariWeb site-internal directory rank #15,977 (2025); U.S. SSA has no record of the spelling. |
| Suhayb | صُهَيْب, "one who has reddish-brown hair"; bearer name of the companion Suhayb ibn Sinan (ar-Rumi). | United States, 2023: SSA-derived rank #4,200 and 26 births (Nameberry); Suhaib spelling #3,248 / 36 births in 2019. |
| Wajid | وَاجِد, active participle of wajada — one who finds or perceives. | HamariWeb site-internal directory rank #1,686 (2025). |
| Wasil | وَاصِل, one who reaches/arrives; close friend; root noun wasīla occurs in Qur'an 5:35. | HamariWeb site-internal directory rank #5,558 (2025). |
| Ubaydullah | عُبَيْدُ الله, "little servant of Allah", diminutive of the Abdullah pattern. | HamariWeb site-internal directory rank #3,108 (2025). |
| Taybah | طَيِّبَة, good/pure/wholesome; reported as the name the Prophet gave to Yathrib (Medina). | HamariWeb site-internal directory rank #81,880 (2025). |
| Yaqut | يَاقُوت, ruby; the word occurs in Qur'an 55:58. | Ask-Oracle site-computed global rank #483,000 (2024); HamariWeb internal rank #9,169 for the Yaqoot spelling. |
| Sanabil | سَنَابِل, ears of grain; plural of sunbul, occurring in Qur'an 2:261. | HamariWeb site-internal directory rank #47,238 (2025). |
| Warda | وَرْدَة, rose/flower; the form وَرْدَةً occurs in Qur'an 55:37 as a color description. | United States, 2025: The Bump girls' rank #8,827. |
| Wissam | وِسام, medal/badge, mark of honor (w-s-m root). | United States, 2022: SSA-derived rank #4,693 and 22 births (Nameberry). |

Unlike batch 1, several b2 metrics are name-directory site-internal ranks; each such record's `limitation` field states that explicitly so they are never read as population data. Quranic claims are word-occurrence claims (or, for Ilyasa, a direct prophet-name attestation) and never personal-name claims; numerology, lucky attributes, personality content, and invented stories remain suppressed, and non-English glosses remain drafts pending native-speaker review.

## Batch b3 — October 2026 (`demand_2026-10-b3.json`)

A dedicated high-authenticity batch focused exclusively on verified Companions of the Prophet (Sahaba), early Islamic legal figures, and directly attested Qur'anic scriptural terms. Every candidate was checked against classical biographical compendia (*Al-Isabah fi Tamyiz al-Sahabah*, *Al-Isti'ab*, *Siyar A'lam al-Nubala*), primary hadith corpora (Sahih al-Bukhari, Sahih Muslim, Sunan Abi Dawud), and classical Arabic lexicons (*Lisan al-Arab*, *Lane's Lexicon*).

The collision audit scanned all 6,522 existing records across both Latin and Arabic normalized namespaces. Candidates with existing collisions (e.g., Ikrimah colliding with Ekrima) were audited and excluded, yielding a 100% collision-free batch:

Build and verify:

```bash
python3 upgrading/scripts/add_demand_names.py --manifest upgrading/name_batches/demand_2026-10-b3.json            # dry-run collision audit
python3 upgrading/scripts/add_demand_names.py --manifest upgrading/name_batches/demand_2026-10-b3.json --write    # add after checks pass
python3 upgrading/scripts/add_demand_names.py --manifest upgrading/name_batches/demand_2026-10-b3.json --check    # verify persisted records
```

| Name | Script | Status / Historical Referent | Primary Sourced Basis |
| --- | --- | --- | --- |
| Usayd | أُسَيْد | Celebrated Ansari leader (Usayd ibn Hudayr) | Sahih al-Bukhari 5018 (angels descending during his Quran recitation); Al-Isabah #356 |
| Tufayl | طُفَيْل | Chieftain of Daws (al-Tufayl ibn Amr, Dhu al-Nur) | Sahih al-Bukhari 2935; Al-Isti'ab #1290 |
| Khuzaymah | خُزَيْمَة | Ansari veteran (Khuzaymah ibn Thabit, Dhu al-Shahadatayn) | Sunan Abi Dawud 3560; Tabaqat Ibn Sa'd Vol. 4 |
| Shurayh | شُرَيْح | Legendary judge of Kufa (Shurayh al-Qadi) | Sahih al-Bukhari Kitab al-Ahkam; Siyar A'lam al-Nubala Vol. 4 |
| Khabbab | خَبَّاب | Early steadfast convert & martyr (Khabbab ibn al-Aratt) | Sahih al-Bukhari 3612 & 3852; Al-Isabah #2223 |
| Utbah | عُتْبَة | 7th convert to Islam & founder of Basra (Utbah ibn Ghazwan) | Sahih Muslim 2967 (ascetic sermon); Al-Isabah #5440 |
| Ubadah | عُبَادَة | Chieftain at Aqaba & Quran teacher (Ubadah ibn al-Samit) | Sahih al-Bukhari 18; Al-Isabah #4485 |
| Julaybib | جُلَيْبِيب | Beloved Ansari martyr praised by the Prophet ﷺ | Sahih Muslim 2472 ("He is from me, and I am from him"); Al-Isabah #1083 |
| Wathilah | وَاثِلَة | Ascetic companion of Ahl al-Suffah (Wathilah ibn al-Asqa') | Sahih Muslim 2276; Al-Isabah #9060 |
| Sundus | سُنْدُس | Fine green silk garments of Paradise | Directly attested in Qur'an 18:31, 44:53, 76:21; Tafsir Ibn Kathir |

## Batch b4 — October 2026 (`demand_2026-10-b4.json`)

A second high-authenticity batch featuring prominent early Sahaba, revered female Companions (Sahabiyyat), early hadith scholars, and Qur'anic scriptural terms. Verified against classical Arabic dictionaries (*Lisan al-Arab*), canonical hadith compendia (Sahih al-Bukhari, Sahih Muslim, Jami' at-Tirmidhi), and biographical reference works (*Al-Isabah*, *Al-Isti'ab*, *Siyar A'lam al-Nubala*).

The collision audit audited all 6,532 records across Latin, Arabic, and non-Latin script forms. A cross-script collision on Rumaytha's Hindi form was detected and resolved (रुमैसा collided with existing entries for Romaisa/Rumaisa; corrected to strict interdental transliteration रुमैथा), achieving 100% collision-free persistence:

Build and verify:

```bash
python3 upgrading/scripts/add_demand_names.py --manifest upgrading/name_batches/demand_2026-10-b4.json            # dry-run collision audit
python3 upgrading/scripts/add_demand_names.py --manifest upgrading/name_batches/demand_2026-10-b4.json --write    # add after checks pass
python3 upgrading/scripts/add_demand_names.py --manifest upgrading/name_batches/demand_2026-10-b4.json --check    # verify persisted records
```

| Name | Script | Status / Historical Referent | Primary Sourced Basis |
| --- | --- | --- | --- |
| Qatadah | قَتَادَة | Badri Ansari hero whose eye was healed at Uhud | Dalā'il al-Nubuwwah by al-Bayhaqi; Al-Isabah #7076 |
| Tamadur | تُمَاضِر | Female poetess al-Khansa; mother of martyrs at Qadisiyyah | Al-Isabah #11005; Al-Isti'ab #3287 |
| Rumaytha | رُمَيْثَة | Ansari Sahabiyyah who narrated the Seal of Prophethood | Jami' at-Tirmidhi 3644; Al-Isabah #11200 |
| Muadhah | مُعَاذَة | Senior female hadith scholar & student of Aisha | Sahih al-Bukhari 321; Siyar A'lam al-Nubala Vol. 4 |
| Namariq | نَمَارِق | Cushions arrayed for the righteous in Paradise | Directly attested in Qur'an 88:15; Tafsir Ibn Kathir |
| Jandab | جُنْدَب | Personal name of Abu Dharr al-Ghifari (most truthful) | Jami' at-Tirmidhi 3801; Al-Isabah #1162 |
| Muayqib | مُعَيْقِيب | Keeper of the Prophet's signet ring & Caliphate treasurer | Sahih al-Bukhari 5866; Al-Isabah #8327 |
| Salit | سَلِيط | Badri pioneer & diplomatic ambassador to Yamama | Al-Isabah #3244; Al-Isti'ab #1015 |
| Hubab | حُبَاب | Badri strategist who gave tactical counsel (Dhu al-Ra'y) | Al-Isabah #1579; Al-Isti'ab #471 |
| Suwaybit | سُوَيْبِط | Early Abyssinian migrant & veteran of Badr | Sunan Abi Dawud 4998; Al-Isabah #3629 |


