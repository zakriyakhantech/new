# Islamic Name JSON Quality Repair — Progress Tracker

- Working branch: `quality-gates/all-name-records`
- Dataset: `upgrading/names_upgraded/islamic/`
- Scope of this pass: improve FAQ answer accuracy and uniqueness; keep FAQPage JSON-LD synchronized; normalize canonical URLs and breadcrumb URLs.
- Safety rule: do not invent meanings, origins, Qur'anic claims, popularity, or translations. Keep uncertain claims explicitly unverified.
- Completed records: **9** (updated one-by-one; see entries below).
  1. `aabid.json` — improved 5 FAQ answers; validated JSON, canonical, breadcrumbs, FAQPage parity, no duplicate questions.
  2. `aabida.json` — improved 5 FAQ answers; validated structure and no duplicate questions.
  3. `aabir.json` — improved 6 FAQ answers; validated structure and no duplicate questions.
  4. `aabish.json` — improved 5 FAQ answers; preserved unverified meaning/origin and corrected misleading Qur'anic FAQ; validated structure.
  5. `aad.json` — improved 5 FAQ answers; clarified Qur'anic historical referent vs modern name usage; validated structure.
  6. `aadam.json` — improved 5 FAQ answers; separated scriptural identification from deeper etymology/popularity; validated structure.
  7. `aadhil.json` — improved 7 FAQ answers; removed awkward duplicate spelling phrasing; validated structure.
  8. `aadil.json` — improved 6 FAQ answers; clarified lexical meaning vs religious status and popularity; validated structure.
  9. `aadila.json` — improved 6 FAQ answers; clarified feminine morphology and separated lexical meaning from popularity; validated structure.
- Validation confirmed for first 6: each parses as JSON, has 10 FAQ entries, FAQPage data matches the FAQ array, no duplicate normalized questions, and canonical/BreadcrumbList are route-consistent.
- Records 7–9 have been edited and FAQPage/canonical/breadcrumb data synchronized; a fresh post-write validation is pending.
- Not completed: remaining files in the Islamic folder have not yet been processed. Meanings and translations have not been comprehensively fact-checked. Update this log after each batch.
