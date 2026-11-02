# Recovery and preservation disposition

The supplied `OntoKin_C089_Unified_Handoff_2026-11-02_v2.zip` is the input
authority for C090. Its exact size is 444,719,689 bytes and SHA-256 is
`bd65a53e3a74dea29a540830b8bedddba6c9fd20bf6ac5c93e1b2114fc619ff8`.
The C089 root README and next-task document were read before recovery or edits.

The independent recovery reviewer inspected the supplied archive-mode helper
and its common implementation before execution. Recovery streamed the held ZIP
through its manifest, exact member/mode/byte/hash/CRC checks, independently
decodable native packs, source inventory, native objects/commit bodies, exact
refs/shallow boundaries and full Git integrity check. It required fresh output
paths, refused symlinks/existing destinations and disabled repository execution
configuration/hooks. It used neither network nor project runtime execution.

The actual C090 opening recovery passed in 30.756574 seconds. It restored all
10,847 source files / 670,403,081 bytes, 210 captured commits, exact references
and both disclosed shallow boundaries at source
`655097f016af17434b9b26fae22491f5f302aa18`, tree
`358c2a696c14a27b9e7dcaa68cd35cbad3cd79df`. The original sealed archive remained
unchanged. The complete command/result is preserved as
`evidence/opening/C089-RECOVERY.json` in the standalone C090 handoff.

This result does not reclassify older attempts. C088's original complete
workspace recovery remains failed, while its separately verified source/native
recovery passed. The first C089 directory-based recovery also remains failed at
its strict final inventory, with an unexpected file that was an exact prefix of
the base pack; the cause remains unestablished. The separately reviewed C089 v2
archive-input route passed and is the unchanged route used here. See the exact
[C089 disposition](../finite-torque-review-2026-11-02-c089/RECOVERY-DISPOSITION.md)
and prior provenance retained in the new handoff.

The current checkpoint contains complete tracked source and every captured
native Git object, including original tracked evidence and the author/review
branch history. Its two native packs are the unchanged C088 base plus a complete
non-thin delta for subsequent objects. It does not recursively include older
sealed handoff ZIPs, dependency installations or every transient test workspace.
Current selected preflight raw responses, actual SQLite/artifacts, failures,
input identities and independent-reader results are retained separately in this
handoff and indexed by exact content/mode manifests. Exclusion of reproducible
temporary directories is not a claim that every historical workspace recovered.

The C090 sealed package identity, actual final source/ref/native inventory and
fresh archive-mode recovery are closing observations made after integration.
The package's manifest and CHECKPOINT.json define its content. A build pass is
not a recovery pass; require the separately executed fresh recovery receipt.
None of these storage checks releases torque or changes a product gate.
