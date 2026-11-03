# v9 source-checked name specs

One small JSON file per name (`<tradition>/<slug>.json`). `scripts/v9_upgrade.py`
verifies it against its cited sources and builds the full super-2.0 record.

Rules
- Only facts that appear in a cited source go into a spec. No invented meanings,
  people, dates, popularity or religious status.
- Every entry in `claims` names a `source` id and 2–4 `terms` that must occur in
  that source page. If any term is missing the record is not written.
- Sources: Wikipedia / Wiktionary (fetched through their public APIs) and other
  pages that permit automated reference checks. Sites whose robots.txt disallows
  automated agents (e.g. behindthename.com) are not fetched.
- Translations are short renderings of the cited meaning and stay flagged for
  native-speaker review.
- Numerology/lucky fields from the old record are carried over and stay labelled
  interpretive.

Order of work: `../V9_FAMOUS_QUEUE.json` (most famous first). Progress:
`../V9_UPGRADE_TRACKER.md`.
