# Islamic Name JSON Quality Repair — Progress Tracker

- Working branch: `quality-gates/all-name-records`
- Dataset: `upgrading/names_upgraded/islamic/`
- Total individually reviewed/edited so far: **31 records** (partial; not the full dataset).
- Scope: FAQ answer accuracy and uniqueness, FAQPage JSON-LD parity, canonical and breadcrumb URLs, and cautious correction of meaning/form mismatches.
- Safety rule: do not invent meanings, origins, Qur'anic claims, popularity, or translations. Keep uncertain claims explicitly unverified.

## Completed records

1. `aaban.json` — corrected gender FAQ to match the record's unknown gender classification; synchronized visible FAQ and FAQPage structured data.
2. `aabid.json` — improved 5 FAQ answers.
3. `aabida.json` — improved 5 FAQ answers.
4. `aabir.json` — improved 6 FAQ answers.
5. `aabish.json` — improved 5 FAQ answers; preserved unverified meaning/origin and corrected misleading Qur'anic FAQ.
6. `aad.json` — improved 5 FAQ answers; clarified Qur'anic historical referent vs modern name usage.
7. `aadam.json` — improved 5 FAQ answers; separated scriptural identification from deeper etymology/popularity.
8. `aadhil.json` — improved 7 FAQ answers; clarified transliteration.
9. `aadil.json` — improved 6 FAQ answers; clarified lexical meaning vs religious status/popularity.
10. `aadila.json` — improved 6 FAQ answers; clarified feminine morphology.
11. `aadilah.json` — improved 6 FAQ answers; clarified feminine morphology and evidence limits.
12. `aaf.json` — improved 9 FAQ answers and corrected a Latin/Arabic mismatch: Aaf had been equated with عائشة (Aisha/Aaisha). Meaning, origin, root, gender, and translation marked unverified/provisional.
13. `aafak.json` — improved 6 FAQ answers; clarified lexical sense of آفاق.
14. `aafaq.json` — improved 9 FAQ answers; clarified that آفاق is plural of أفق and removed unsupported popularity inference.
15. `aafia.json` — improved 9 FAQ answers; refined lexical gloss and separated it from popularity/scriptural claims.
16. `aafiya.json` — improved 9 FAQ answers; refined lexical gloss and separated it from popularity/scriptural claims.
17. `aafreen.json` — improved 9 FAQ answers; clarified Persian origin and meaning of آفرین.
18. `aaftab.json` — improved 9 FAQ answers; clarified Persian origin and meaning of آفتاب.
19. `aahil.json` — improved 9 FAQ answers and downgraded confidence because Arabic أهل (“family/people”) does not by itself establish the exact Latin spelling Aahil as a name form.
20. `aahoo.json` — improved 9 FAQ answers; clarified Persian origin and lexical meaning of آهو.
21. `aaida.json` — improved 9 FAQ answers; clarified the feminine Arabic form عائدة and its lexical meaning.
22. `aaima.json` — improved 9 FAQ answers and downgraded confidence because the Latin spelling Aaima does not conclusively establish the intended Arabic form عائمة.
23. `aaina.json` — improved 9 FAQ answers; clarified Persian/Urdu “mirror” meaning and avoided incorrectly labelling the word Arabic.
24. `aaira.json` — improved 9 FAQ answers and removed contradictory unsupported glosses; meaning, origin, root, and translations remain unverified.
25. `aaisha.json` — improved 9 FAQ answers; removed unsupported “female helper” gloss and distinguished the Arabic lexical meaning from the historical bearer.
26. `aaiz.json` — improved 9 FAQ answers; clarified Arabic عائذ as “one who seeks refuge/protection.”
27. `aakif.json` — improved 9 FAQ answers; clarified Arabic عاكف and avoided unsupported popularity/scriptural claims.
28. `aakifah.json` — improved 9 FAQ answers; clarified feminine Arabic عاكفة and its lexical sense.
29. `aakil.json` — improved 9 FAQ answers; refined Arabic عاقل gloss and corrected the Arabic translation’s gender/meaning.
30. `aala.json` — improved 9 FAQ answers; downgraded confidence because Arabic عالية does not clearly match the exact Latin spelling Aala.
31. `aalaa.json` — improved 9 FAQ answers; clarified علاء as a lexical term related to elevation/eminence and kept gender/popularity claims provisional.

## Validation

- Records `aafaq`, `aafia`, `aafiya`, `aafreen`, `aaftab`, `aahil`, `aahoo`, `aaida`, `aaima`, `aaina`, `aaira`, `aaisha`, `aaiz`, `aakif`, and `aakifah`, `aakil`, `aala`, and `aalaa` were re-fetched after saving and validated: JSON parsing succeeded, FAQPage parity passed, duplicate-question count was zero, and canonical/BreadcrumbList were present and route-consistent.
- These 18 records have 9 FAQ entries each. No filler questions were added just to reach 10.
- The first 9 quality-repair records were also validated after edits for JSON validity, FAQPage parity, no duplicate normalized questions, and canonical/BreadcrumbList consistency. `aaban` and `aadhil` had separate checks/corrections before this log was created.
- Structural validation does not prove that every semantic claim is independently sourced. Translation fields marked for native review are not represented as native-verified.

## Still outstanding

- Remaining Islamic files have not yet been processed.
- Meanings, etymologies, and translations have not been comprehensively checked against independent primary/lexical sources.
- Continue in small batches, re-fetch after each write, validate, and update this log.
