# P28 recovery input audit

Reviewer: `/root/archive_audit`. Scope: fresh P27 development and P28 early recovery archives, read-only. No product execution, external writes, or prior-host access.

**Result: archive integrity passes; later P28 implementation evidence is absent from these two inputs.** All 1,613 checks passed. ZIP CRC, safe paths, duplicate names, exact inventory, each payload size/hash, extracted bytes, source-manifest identities, P27 recovery mappings, and 81 embedded P27 receipt/terminal recovery records were verified.

| Input | Bytes | Payloads | Source bindings | SHA-256 |
| --- | ---: | ---: | ---: | --- |
| P27 development ZIP | 7,397,736 | 396 | 126 | `d9fdae71a39f343b1fa14a6eb358f780428a1d05af66e85bd9e4c191abe82a77` |
| P28 early recovery ZIP | 8,480,098 | 62 | 42 | `520b24277f2f4a28b5ed96122a477b2438a60905c1a1ae80de39d448426cb15e` |

The P28 early archive snapshots `360c80062e769230199602326fa8de25660df714`, the P27 receipt commit, before P28 product edits or control execution. Its only `recovery/` member is `build_early.py`. It contains no later P28 candidate, executable fixture freeze, test results, or publication payload.

The included P27 terminal record reports verified delivery and released ownership. It binds source `105ac7c5f247fc1a01c1073266763f16e6587757`, receipt commit `360c80062e769230199602326fa8de25660df714`, receipt Library ID `libfile_fde3_f-7615062b8c488191a8365d9faa5b5095_2ab2a24d43748191957f9bcc356b59de`, receipt SHA-256 `614a765b48e90efd1de9b3f5ae102bdf838c834fa8ebcdbc0581baef676c8783`, and terminal comments `7110046284` / `7110052122`. These are retained historical observations; the Director must verify live destinations.

**Next action:** reconcile exact later durable artifacts or Git object identities before repeating any work. A reported test pass alone cannot qualify a reconstructed candidate. If exact later bytes cannot be recovered, preserve that concrete blocker and the uncertain publication identities; do not silently claim completion. R03–R05, P02, H0/H1/full routine, and main integration remain outside this audit.

Detailed executable audit and per-check results are in `audit.py` and `AUDIT.json` beside this report.
