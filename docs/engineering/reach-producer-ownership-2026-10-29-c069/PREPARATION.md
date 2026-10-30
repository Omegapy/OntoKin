# C069 recovery and preparation

The six uploaded C068 metadata files were read from their provided local copies. Each matches its canonical file in the recovered original C068 packet. The prior packet and ZIP were available at the earlier workspace's delivery location. The unchanged C068 verifier was freshly run against both; it returned zero with empty stderr. [Receipt](preparation/c068-verification.json) and [actual command](preparation/c068-verification-command.json) retain this execution.

The verified baseline is main `7c0bf98e48a641e30627b7fd261b6713d79e223c`, tree `a53acdaa3a65c8863a027ee407e1f291ffe4ae24`: 3,663 source files, 622,197,405 bytes, no omissions. Original ZIP: 476,328,864 bytes / 3,694 members / SHA-256 `7ee6edca85ac33944b08c8eda0d48e1cc8d21d7bcee35ff30d2ee50e4e01a09b`. The source index has SHA-256 `0105e7e2b355cb55dcc3ed4dceee8208c9927bbc183cb31ea274cf1de84151c8`.

## Actual failures retained

1. A local Git clone of the prior reconstructed checkout failed because the historical lease tree `b3b59d5db360e3ba5cf692d9d6fcc176169b3e37` was absent. [The failed attempt](preparation/clone-attempt.txt) is recorded. This concerns incomplete local Git history; it is not evidence of remote GitHub corruption or missing frozen source bytes.
2. The initial source-snapshot `git add` respected ignore rules and omitted 152 previously tracked payload paths. Its tree did not match the baseline, so recovery stopped. [The discrepancy](preparation/index-recovery.json) preserves every omitted path and failed tree. Recovery then wrote every source-index blob without filters and rebuilt the Git index using each original mode/path/blob. The resulting tree exactly matched the verified baseline; the real final raw commit was hash-checked and installed with an explicit shallow boundary. No synthetic substitute commit was used.

No source file or historical evidence was discarded. The new checkout is complete source with exact current commit identity, not a full-history clone. Future candidate/lease/merge/publication raw objects and their actually available trees are retained separately.

## Coordination and execution boundary

[Initial live state](preparation/initial-live-state.json) confirms current main, the unchanged history-only archive branch, zero open PRs and completed listed historical workflows. The actual C068 closure is [Issue #26 comment 6511535756](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6511535756); it releases the remaining C068 scope/window. The new C069 scope is [comment 6511706076](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6511706076), preserved [locally](preparation/scope-comment.md).

Only source analysis, standard-library byte/AST checks, relevant documentation checks and packet verification are selected. These operations do not run product code or upgrade historical runtime evidence. Original C067 packet verification remains a fact retained in the C068 receipt; C067's original C066 packet/ZIP unavailability and verified C066 source recovery remain historical facts with their original meanings.
