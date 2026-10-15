# NameVerse repository-wide quality upgrade protocol

Target dataset: `upgrading/names_upgraded/` (all religions and name categories).

## Non-negotiable rules
1. Process every name JSON recursively. Never silently skip a file; record every path and status in a progress manifest.
2. Preserve file names, slugs, route identity, schema version, required keys, existing URLs, and compatible data shapes.
3. Never invent a meaning, language, root, historical attribution, Qur'anic/Hadith claim, popularity statistic, usage claim, or translation.
4. Treat source text, source URLs, and model-generated confidence as unverified until checked. A URL is not evidence unless the cited page supports the specific claim.
5. Separate lexical meaning from famous bearers, religious significance, cultural use, and modern naming interpretations.
6. If evidence is inadequate, use the schema's existing uncertainty representation, lower confidence, set manual review required, and remove any contradictory verified/Tier-1 status. Do not replace uncertainty with a guessed meaning.
7. Distinguish a spelling/transliteration variant from a genuinely different lexical form. Never merge or delete entries automatically; create a variant-review report.
8. Translations must be accurate, idiomatic, and reviewed by a fluent speaker where possible. Do not translate an unverified claim as if it were fact.
9. FAQ answers must agree with the record's verified facts. Avoid repetitive template questions and unsupported SEO claims. Keep FAQ arrays and FAQPage structured data synchronized exactly.
10. Quality and SEO scores are outputs of evidence-based checks, never proof of accuracy. No record may be labeled fully verified just because its fields are populated.

## Required workflow
- Inventory all JSON files first and save a manifest with path, slug, original checksum, status, issue list, and last reviewed timestamp.
- Work in small sequential batches of 25–50 records; never skip files, overwrite newer work, or claim a batch complete before validation.
- For each record, verify the original-language spelling and transliteration; lexical meaning and morphology; language/origin; gender/usage evidence; religious/history claims; every translation; every FAQ; source relevance; duplicate/variant risk; and SEO text.
- Cite the specific sources supporting each factual claim in the existing evidence schema. Prefer dictionaries, primary texts, reputable encyclopedias, and reliable language resources. Record the exact source URL and what it supports.
- If sources conflict, explain the conflict and lower confidence. If no source is available, mark unresolved and require manual review.
- Reconcile contradictions across core_meaning, etymology, language, origin, translations, FAQ answers, structured data, verification flags, and score fields.
- Validate JSON parsing and required schema fields after each record. Verify FAQ schema parity, no duplicate FAQ questions, no blank translation fields, and no broken internal references.
- Run a dataset-wide duplicate/variant report across all categories and religions. Do not automatically delete/merge records; recommend canonical relationships for review.
- After each batch, produce a report listing changed files, verified claims and their sources, unresolved claims, possible variants, translation-review needs, and validation results.
- Only mark a record complete when evidence supports its claims. Otherwise label it unresolved/manual-review-required and move on only after recording that status.
- Keep all changes on a dedicated branch and review the diff before merging to the default branch.

## Definition of done
Every JSON file is inventoried and has a documented status; all verifiable claims have claim-specific evidence; contradictions and structural issues are fixed; likely variants are reported; translations and FAQs are checked; unresolved facts remain explicitly uncertain; and automated validation passes. Do not promise 100% factual certainty where evidence cannot establish it.
