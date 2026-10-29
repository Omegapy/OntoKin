# C061: independent-reader setup attribution and finite axial-reuse NO-GO

**Decision: stop this candidate.** The four authorized attribution requests are complete. P11 never entered the proposed axial-derivative path during reader setup. L03 spent only 376 operations there. Under the explicitly unchanged downstream behavior of this isolated candidate, even deleting all 376 would leave a source-derived lower bound above the 100,000-operation cap. No runtime optimization was selected or implemented.

This is a diagnostic checkpoint. Both original recordings still fail. The successful audits establish observation integrity for these executions; they do not accept the retained bytes as recordings or close a release gate.

## Read in this order

1. [Checkpoint and decision](CHECKPOINT-061.md): measured costs, the conditional lower bound, and limits of the conclusion.
2. [Handoff](HANDOFF-061.md): actual source identity, recovery limits, publication state and continuation instructions.
3. [Next task](NEXT-TASK.md): a separate proposed scope, not an active worker or scheduled job.
4. [Machine-readable decision](decision.json), [documentation gate](documentation-gate.json), and [remote publication receipt](publication.json).
5. [Evidence manifest](evidence-manifest.json) and [verification script](verify_evidence.py): exact archive parts and every raw member, including unsuccessful requests and negative controls.

The evidence archive contains the complete 491-file materialized execution input, its explicit 2,890-file omission list, actual commands/stdout/stderr, both original control/capture pairs, independent audits, two deliberately damaged evidence inputs and their rejections, review notes, and preparation/source-binding records. The final documentation-gate and publication receipts are separate named files beside this README because they were produced after the measurement archive was frozen.

## Exact identities

| Role | Identity |
| --- | --- |
| Repository | `Omegapy/OntoKin` |
| Main observed at activation and after measurement | `b37b39102aea67eb81bd9e38518352403a844e99` |
| Explicit unmerged C060 dependency | `00533b953ed345cbf5fa13eaa56aafa3a2f052a8`, draft PR #58 |
| Executed C061 tooling commit | `bd5a09618c123a0b1d3339df3a944cfd6ed63b56` |
| Executed tree | `037157a58442ba1956597d32e1e540802f9ed896` |
| Branch | `work/reach-reader-setup-20261028-c061` |
| Owner | `interactive-reach-reader-setup-20261028-c061-7of9-b4f2` |

The executed commit adds only `tools/capture_reach_reader_setup.py` and `tools/audit_reach_reader_setup.py` to C060. All 65 materialized runtime files are unchanged. The archive preserves the exact tool bytes and original source commit. Evidence publication commits follow the executed commit and are identified separately in `publication.json` and the final Issue #26 handoff.

## Actual results

| Measurement | P11 | L03 |
| --- | ---: | ---: |
| Original control process exit | 1 | 1 |
| Capture process exit | 1 | 1 |
| Final shared count, including refused tick | 100,001 | 100,001 |
| Reader-entry shared count | 61,415 | 54,988 |
| First-key-entry shared count | 84,586 | 72,173 |
| Reader setup operations | 23,171 | 17,185 |
| Generic checkpoint charges within setup | 13,121 | 8,900 |
| Axial-derivative calls / inclusive operations | 0 / 0 | 4 / 376 |
| Entered keys / all supplied keys | 37 / 52 | 154 / 178 |
| Independent audit | Passed: 381,009 assertions | Passed: 677,251 assertions |

All four requests used the original inputs and shared request budget. Controls and captures agree on the complete work maps, original exception graph/product frames and retained reader-input bytes. The failed product processes exit 1; the independent evidence audits exit 0. Neither elapsed-time neutrality nor speedup is claimed.

The two negative audits intentionally exit 1: a duplicated setup event and a checkpoint/category mismatch are each rejected for the intended reason. Exact original setup files were restored and hash-verified. These are offline auditor checks, not additional product requests. The conditional second four-request round was not used.

## Preserved blockers

The initial unchanged documentation check failed with 17 local links: twelve historical archives and five links to four omitted historical directories. All 108 tracked files in those four directories were then recovered and verified against their immutable Git blobs. The historical archive bytes remain unavailable through this executor's connection; no placeholders, altered links or fabricated LFS pointers were substituted. The final actual gate result is in `documentation-gate.json`.

No main integration lease was acquired. C060 remains an unmerged prerequisite, and this checkpoint is prepared as a draft dependent PR. The historical 24/28 corpus outcome remains historical; C061 did not rerun the full corpus, unit suite, destination validators or visual review. P11, P16, P23 and L03 remain unresolved at the release level. M1 remains rejected, C035 remains held, and LFS payload migration remains unexecuted.
