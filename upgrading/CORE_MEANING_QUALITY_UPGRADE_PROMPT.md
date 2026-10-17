# NameVerse Core Meaning Authenticity Upgrade — Master Agent Prompt

## Mission
Audit and improve the core meaning and etymology of every eligible name record in this repository, across every religion, language, and dataset folder. Work in small, resumable batches until every record has either been reviewed or explicitly marked as needing research. Never claim completion without a full inventory and a reconciled report. Accuracy is more important than length or SEO prose.

## First inspect the repository
Inspect the tree, schema, existing upgrade/finalisation scripts, tests, and progress tracking before changing anything. Discover record directories instead of assuming a single religion. Exclude indexes, templates, manifests, and non-record JSON. Preserve paths, slugs, IDs, schema versions, and unrelated fields.

## Fields in scope
Where present, review `data.core_meaning.short_meaning`, `primary_meaning`, `literal_meaning`, `meaning_explanation`, `meaning_confidence`; `data.etymology.primary_language`, `lexical_form`, `transliteration`, `root`, `root_transliteration`, `morphology`, `etymological_meaning`, `etymology_explanation`, `etymology_confidence`, `false_etymology_warning`; and existing evidence/source fields. Correct translations/FAQs only when they repeat a demonstrably wrong core claim and the correction is supported. Do not rewrite unrelated fields.

## Evidence rules
For each record, separate: (1) correct original-script form, (2) lexical attestation, (3) direct dictionary meaning, (4) morphology/root, (5) attestation as a personal name, (6) gender usage, and (7) religious/historical claims. Evidence for one does not prove the others.

Prefer reputable dictionaries, academic references, linguistic corpora, primary texts, and specialist historical sources. For Arabic, use suitable references such as Hans Wehr for modern usage and Lane's Lexicon or other reputable classical dictionaries for historical forms. For Persian and other languages, use appropriate authoritative dictionaries and academic references. Record direct, claim-relevant source URLs and concise evidence notes using the existing schema. A search-results page, generic homepage, AI answer, or unsourced baby-name list is only a research lead, not proof. Never fabricate sources, quotations, root derivations, name-bearers, religious status, popularity statistics, or source URLs. If research is unavailable, mark the claim unverified and add it to the research queue.

## Field standards
- `short_meaning`: concise direct gloss, normally a few words; do not merge unrelated senses.
- `primary_meaning`: readable, evidence-based explanation of the best-supported lexical meaning; identify language/form when known; separate literal, contextual, figurative, and interpretive meanings.
- `literal_meaning`: direct lexical gloss, or explicitly state that the exact meaning is unverified. Do not call “historical Arabic name form” a literal meaning.
- `meaning_explanation`: explain lexical evidence, morphology, semantic range, and limitations in distinct prose. Do not repeat the primary meaning with trivial wording changes.
- Etymology: assign roots, patterns, morphology, and gendered forms only when evidence supports the exact form. Never infer roots from spelling resemblance alone. Do not invent a feminine form.
- Confidence: use only existing schema enums. HIGH requires strong direct evidence for the exact form and claim; MEDIUM means evidence is useful but a material detail remains uncertain; LOW/unverified means the form, meaning, or derivation is not adequately established. Confidence follows evidence, not writing quality.
- Religious boundaries: do not label a name Qur'anic, Biblical, Vedic, prophetic, a companion's name, scripturally prescribed, or religiously recommended without a direct, verifiable source. “Not found in checked sources” is not proof that no source exists; describe search limits honestly.
- If only personal-name attestation is supported, say that and leave the precise lexical meaning unresolved. Never fill every field with plausible prose just because the schema contains it.

## Duplication and contradiction checks
Detect generic boilerplate, repeated sentences across unrelated names, circular explanations, original-script/transliteration mismatch, suspiciously reused roots, contradictions between core meaning and translations/FAQs, and confidence unsupported by evidence. Repetition is acceptable only when the underlying fact genuinely is the same. Never “fix” duplication by swapping in another unverified meaning.

## Safe resumable workflow
1. Record baseline commit and inventory eligible records.
2. Process deterministic batches of 25–100 records, adjusted to runtime/tool limits.
3. Maintain a committed progress manifest with total, reviewed, corrected, unchanged/verified, needs-research, errors, last completed path, batch ID, and evidence status.
4. On restart, reconcile the manifest with actual repository files before continuing.
5. Parse and validate each JSON before editing. Preserve all unrelated keys and values. Never replace a whole record with a partial AI response.
6. Keep Git history and auditable diffs; never delete original datasets or silently overwrite data.
7. On ambiguous/conflicting evidence, preserve uncertainty and queue for review.
8. Do not claim tests were run unless they were actually run; do not claim all names were processed if any batches failed or were skipped.

## Required QA tooling
Build or improve a script compatible with the actual repository runtime/schema and run it across every eligible record. It must:
- Parse JSON and report invalid files.
- Validate schema-required fields and confidence enums.
- Flag empty/placeholder meanings, duplicated boilerplate, slug/name mismatches, suspicious script/transliteration pairs, and contradictions.
- Flag HIGH confidence without direct claim-relevant evidence and flag generic/search-result URLs as insufficient.
- Flag religious/scriptural claims lacking direct evidence.
- Detect overly duplicated core fields conservatively; treat heuristic results as review candidates, not proof.
- Test that edits to core meaning preserve unrelated fields.
- Include positive/negative fixtures: supported Arabic word, Persian lexical item, uncertain historical name, folk etymology, fabricated-source example, and boilerplate duplication.
- Produce machine-readable JSON/CSV plus a human-readable report.

## Per-record process
Identify exact form and existing claims; inspect sources; classify VERIFIED, PARTIALLY_VERIFIED, NEEDS_RESEARCH, or CONTRADICTED; edit only what evidence supports; ensure fields are distinct and consistent; run record/schema checks; commit batch; update progress; continue until all records have a disposition. Then rerun the full audit and reconcile report counts to the inventory.

## Deliverables
1. This master prompt.
2. Tested audit/upgrade script.
3. Durable progress manifest.
4. Machine-readable report per record: disposition, fields changed, evidence URLs, confidence, unresolved questions.
5. Final counts: discovered, reviewed, corrected, unchanged, flagged, failed, and needs human research.
6. Git diff demonstrating that unrelated fields and routes/slugs were preserved.

## Definition of done
Every eligible record is processed or explicitly queued for research; JSON and schema checks pass; tests have actually run; reports reconcile to the inventory; unresolved cases are transparent. Never promise “100% accurate.” Promise evidence-led corrections, reproducibility, and honest uncertainty.
