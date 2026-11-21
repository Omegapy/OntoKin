# Exact receipt metadata correction — accepted

The actual correction changes only `CURRENT.snapshot_date` from `2026-11-21` to `2026-11-21T17:16:40.093675+00:00`. Corrected CURRENT SHA-256 is `7828773e75dfce43b6cad490e79dd827b9a2d699713ae97de4a740d4d83d2636`.

A read-only Git object lookup confirmed that root's retained preimage equals the file at published receipt commit `be159c31db3ef26f66adbcb641e326e2b6ebc198`. Both the parsed comparison and exact-byte string replacement confirm the single-field scope. The corrected literal supplies the explicit zero UTC offset required by the unchanged checker. All seven failed-check files match their preserved repository evidence copies.

This accepts the exact metadata correction for root's subsequent publication and required repository checks. No checker execution, retest, canonical edit or Git mutation was performed by this reviewer. The saved archive/prompts, accepted implementation/oracles, parent status and later-phase restrictions remain unchanged. The earlier rule review is preserved; this addendum binds the concrete correction.
