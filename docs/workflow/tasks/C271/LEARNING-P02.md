# C271 P02 scoped verification lesson

The required routine driver copied a fixed directory/root-file inventory. At source `88bc8b51b3963b7072375edac6400b6e6a4532e4`, that inventory omitted five tracked instruction files. Its initial workspace record already reported their deletion; the isolated documentation checker then reported 21 missing links to those same files. The complete-checkout checker passed. This is a demonstrated workspace-preparation defect for this candidate, not evidence that the documentation gate may be ignored.

The next bounded repair should establish that every required instruction target survives workspace preparation, with a focused check that fails on the observed omission. The required full driver still needs a complete passing run. Its 900-second timeout has no final unittest footer, so a parser value of zero is not a test-execution count. Retain the original log, exit status, timing and environment limits when choosing a justified completion plan.

No copy repair, timeout change, dependency adjustment or behavioral replay was performed in this phase. Frozen control expectations and per-source resource limits remain unchanged. The initial targeted workflow lookup for `isolated workspace` found no existing lesson; this note records only the demonstrated local finding.

Evidence: `docs/engineering/localized-repair-c271/finalization-20261120/verification/DOCUMENTS-FAILURE-INSPECTION.json`, `verification/PARTIAL-UNIT-LOG-ACCOUNTING.json`, `verification/RESULTS.json` and `verification/RAW-EVIDENCE.zip`.
