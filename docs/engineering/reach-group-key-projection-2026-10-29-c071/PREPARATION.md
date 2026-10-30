# C071 preparation and evidence boundaries

The original C070 ZIP was recovered and verified before the C071 source scope was declared. Its exact identity is 476,567,959 bytes / SHA-256 `e34a81693866eafb7d170bd943a124afc813aa8904f1d4497be544fe7c9ece4d`. The unchanged original verifier passed against both the extracted packet and ZIP, exit 0 with empty stderr. Its fresh receipt hash is `ac197ac7d878dbf9bd2075fe0242becabb1b22a5de1dce771d9a4002723c5a88`, matching the original external C070 verification receipt.

All 3,749 tracked source files / 622,661,283 bytes were recovered, with zero omissions. Tree `a124d1acfa4e7c5f6c140e592d594036a2eed2ca` and actual raw commit `ff71faa05503245b553621ba390cad080276e732` are preserved. All six uploaded metadata files are byte-identical to that packet. Exact receipts, command, streams and upload comparisons are under [preparation](preparation/).

Fresh C070 verification retains historical C069/C068/C067 packet and ZIP verification, and the distinct C066 original-packet unavailability with complete-source recovery. This does not rerun or relabel those historical executions or audits.

## Resolved setup failures

The default `git ls-remote` failed to reach the configured network proxy. Source recovery instead used the authenticated repository connector for live state and the complete original packet for local source. The current Library helper likewise initially failed before materialization on a hosted tools-list network request. Its identical authorized transfer succeeded after approved network escalation, with no partial result or warnings. Original failure and successful transfer records are retained; no credentials or signed URLs are copied into the repository.

An initial `update_ref` call attempted to create the new branch and received HTTP 422 because that operation required an existing reference. The purpose-built branch creation succeeded from the exact observed baseline and the resulting reference was read back. No existing reference was overwritten or force-moved.

The first local Git index reconstruction used `git add --all`, which respected ignore rules for 152 historical tracked `.log` paths. Its tree assertion therefore failed at `33f8f6eb443fdaf3c0398f4d37344360e46d1589`. The exact inventory difference contained those missing paths and no changed or extra blobs. Adding only those manifest-listed paths with `-f` reconstructed the required tree. No original source bytes or modes changed. [The recovery record](preparation/checkout-recovery.json) and [exact difference](preparation/checkout-initial-index-difference.json) preserve the failure and correction.

The working checkout uses the actual raw baseline commit and an explicit shallow boundary. It is not a full-history clone and no synthetic commit substitutes for remote identity.

## Static derivation history

The costs reviewer first authored a standalone retained-clock screen. Its exact script and identity are preserved in `preparation/derive_speed_projection_screen-first.py` and `preparation/first-helper-identity.json`; initial execution provenance is limited to what that record actually retained.

The expanded source-bound derivation passed its first run. One ordering assertion was then tightened to compare the late source-speed read against the actual destination rotation outward-rounding assignment. The final revision passed twice with byte-identical output. The prior successful revision, every actual executed script, command, stdout and stderr remain under [validation](validation/). No failed derivation run occurred during that extension.

The final derivation records 84 source bindings, 20 definition records and 52 named checks. All 65 current runtime files match C060. It verifies nine ordered C060 archive parts and the assembled archive, two selected unvalidated GLB members, actual binary32 clocks and all 2,082 certificate identities. This selected retained-byte inspection is not a rerun of the historical archive auditor or product requests, nor certification of the GLBs' numerical claims.

## Publication boundaries

The source review, actual published-candidate documentation check, resulting-merge check, final-main check, portable packet verification and delivery are separate events. Pending roles are marked pending until executed. The final frozen packet necessarily precedes its external verification, delivery outcome and explicit scope-closing Issue #26 comment.

All preparation failures above are resolved setup outcomes. No runtime implementation, product import/request/suite, native trigonometry, generated mesh or hosted job ran in C071. Historical 24/28 failed status and all remaining acceptance obligations retain their meanings.
