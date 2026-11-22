# C271 P19: current inputs stop at a package pin mismatch

## Result

The single independently approved read-only observation stopped at the fifth package in the unchanged seven-package verification lock. The current selected interpreter's `rpds-py` METADATA reports **2026.6.3**; the required version is **2026.5.1**. This is an input-readiness blocker. The product did not raise this package finding through a complete operational plan, and H0 remains unaccepted.

The exact pinned Python, loader and libc files all returned metadata through the selected readers. The libc result uses the explicit 0.1.3 raw metadata primitive. It advances actual-byte evidence beyond P15's historical refusal without changing that refusal or claiming operational dispatch, loader completeness, TLS behavior or host qualification.

## Actual observation

The observation used CPython 3.12.14 on Linux x86-64 with the separately frozen five-variable environment, `-I -S -B`, accepted production source SHA-256 `e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206`, and candidate003. Exact intent, command, hashes, output and outcome are retained in [the observation directory](observation/OBSERVATION-PLAN.json) and [result](observation/attempt001/RESULT.json).

| Check | Observed outcome |
| --- | --- |
| Python, loader and libc fixed file identities | All three match the adopted byte/size/mode pins. |
| Raw ELF metadata readers | All three return metadata; no operational policy admission is claimed. |
| attrs, jsonschema, jsonschema-specifications, referencing | All four METADATA names/versions match the lock. |
| rpds-py | Required 2026.5.1, observed 2026.6.3; retained METADATA SHA-256 `f8be7b17da3980b2c48596941411a43c70ac41b1e2d530aa531f2c15eab2eb1c`. |
| typing_extensions and Pillow | Not read after the first mismatch. |
| Post-read identity/hash checks | All ten match. |
| Attempt outcome | One observation, exit 2, no retry, empty stderr. |
| Forbidden process-operation events and target starts | Zero. The observation itself is one Python process, not zero OS processes. |

No Node, ldd, direct loader command, package/site import, installation, full routine, H1, native/model/hosted execution or main integration occurred. Full dist-info inventories, ordinary-provider lookup compatibility and complete loader/source closure remain unreviewed. N57 remains external review only, never a runtime pass or skip.

## Review and failure preservation

The pre-execution reviewer required three harness fixes: postflight failure must block success, the lock digest must be enforced at its actual read, and package directory enumeration must be bounded before materialization. Candidate001 and candidate002 were never executed and remain retained. Candidate003 was accepted for one raw observation. The first wrapper preparation failed before the reviewer artifact existed; absence of launch intent and attempt directory was confirmed before the first actual invocation. This was not an actual-observation retry. Reviewer evidence-copy races and their corrections also remain retained.

Startup reconciled the confirmed P18 ZIP, separate saved receipt/audit and matching live PR/issue markers. Initial connector text snapshots had one extra trailing newline; exact Git bytes, rather than those transport copies, bind all package sources. These nonmaterial failures remain recorded. Historical C270 ancillary-driver completion, global prior-process termination and P13 difflib completion remain unknown and are not replayed.

The independent retained-artifact audit passed 41 checks with zero failures. It reproduced the mismatch from the saved METADATA text, verified all source/plan/launch identities and accepted the first-blocker disposition. [Outcome review](operational-review/OUTCOME-REVIEW.md). It performed no host reread or product execution.

## Parent and next phase

R01/R02 stay done; R03–R05 remain not_done and P02 remains in_progress. PR274 stays draft/open/unmerged, issue273 stays open, and the retained branch is not deleted. Main stays at `70ca7e68ff95df876f801137369d176fe5b2bab3`. Main-only licensing PR275 remains a future integration obligation.

After final verification and delivery, stop. In a fresh chat, review bounded preparation of a separate environment satisfying the exact seven-package lock, including rpds-py 2026.5.1. Do not change the lock or mutate the shared runtime to erase this evidence. Review exact inputs, destinations and preparation authority before installation; then rebind actual inputs before complete H0 review. H1/full routine and integration remain separate gates.
