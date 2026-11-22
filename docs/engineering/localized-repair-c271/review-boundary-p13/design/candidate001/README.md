# P13 candidate001: review completeness and runtime admission

This candidate chooses an **independent-review-only gate** for the completeness of the actual loader's search-suffix inventory. Runtime continues to check bound bytes and observable facts. It receives no approval flag and makes no source-completeness decision.

Read [DECISION.md](DECISION.md), then [CONTROL-CONTRACT.md](CONTROL-CONTRACT.md). [CONTROL-MAPPING.json](CONTROL-MAPPING.json) accounts for every original P11 case; [BOUNDARY-CONTROLS.json](BOUNDARY-CONTROLS.json) specifies the finite static controls for this clarification. [INPUTS.json](INPUTS.json) and [SOURCE-EVIDENCE.json](SOURCE-EVIDENCE.json) bind the source evidence. The candidate is frozen by [CANDIDATE-MANIFEST.json](CANDIDATE-MANIFEST.json); the author check is [author-validation-attempt001.json](../author-validation-attempt001.json).

The original 97 P11 expectations and all 131 fixtures stay unchanged. P13 explicitly changes N57's future applicability: its old runtime-refusal oracle remains historical evidence, and its unresolved source-completeness obligation becomes an external review gate. The other 96 cases retain their original future runtime oracles. No original case is recorded as passed here.

This is a design proposal pending independent review and a separate Director adoption record. It is not implementation, an operational plan, actual-loader evidence, H0/H1 acceptance or parent completion. The 16 MiB document reader and source ceilings of 100,000 operations and 30,000 ms remain unchanged.

The author reads and hashes 145 available candidate004 payloads, 29 supporting files and all 131 fixtures. The manifest's remaining payload, `REVISION-004.diff`, stays an explicitly identified external historical archive member; P13 neither copies nor recreates it. Recorded historical file modes remain in the original manifests. This work does not restore modes or claim a complete offline materialization.

Author: `/root/design_author`. Independent review, adoption, canonical task state, publication and delivery are Director-owned. Stop after this design/control checkpoint; any implementation requires a separately selected phase.
