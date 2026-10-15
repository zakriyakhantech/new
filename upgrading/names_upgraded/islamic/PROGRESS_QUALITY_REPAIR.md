# Islamic Name JSON Quality Repair — Progress Tracker

- Working branch: `quality-gates/all-name-records`
- Dataset: `upgrading/names_upgraded/islamic/`
- Scope of this pass: improve FAQ answer accuracy and uniqueness; keep FAQPage JSON-LD synchronized; normalize canonical URLs and breadcrumb URLs; correct obvious meaning/form mismatches when evidence in the record contradicts itself.
- Safety rule: do not invent meanings, origins, Qur'anic claims, popularity, or translations. Keep uncertain claims explicitly unverified.
- Completed records: **12**, edited individually.
  1. `aabid.json` — improved 5 FAQ answers.
  2. `aabida.json` — improved 5 FAQ answers.
  3. `aabir.json` — improved 6 FAQ answers.
  4. `aabish.json` — improved 5 FAQ answers; preserved unverified meaning/origin and corrected misleading Qur'anic FAQ.
  5. `aad.json` — improved 5 FAQ answers; clarified Qur'anic historical referent vs modern name usage.
  6. `aadam.json` — improved 5 FAQ answers; separated scriptural identification from deeper etymology/popularity.
  7. `aadhil.json` — improved 7 FAQ answers; removed awkward duplicate spelling phrasing.
  8. `aadil.json` — improved 6 FAQ answers; clarified lexical meaning vs religious status and popularity.
  9. `aadila.json` — improved 6 FAQ answers; clarified feminine morphology and separated lexical meaning from popularity.
  10. `aadilah.json` — improved 6 FAQ answers; clarified feminine morphology and evidence limits.
  11. `aaf.json` — improved 9 FAQ answers and corrected a major internal mismatch: the record had equated Latin spelling “Aaf” with Arabic عائشة (Aisha/Aaisha). Meaning, origin, root, gender, and translation are now marked unverified/provisional instead of inheriting claims from Aisha.
  12. `aafak.json` — improved 6 FAQ answers; clarified the lexical sense of آفاق and separated it from personal-name popularity.
- Validation: records 1–9 were validated after edits: valid JSON, FAQPage parity, no duplicate normalized questions, canonical and breadcrumb URLs present and route-consistent. Records 10–12 were also validated after edits; FAQPage parity is true, no duplicate questions, and canonical/breadcrumb are present. Their existing FAQ counts are 9 (not 10), and this pass did not add filler FAQs just to force a fixed count.
- Not completed: remaining files in the Islamic folder have not yet been processed. Meanings/translations have not been comprehensively checked against independent primary/lexical sources. Update this log after each batch.
