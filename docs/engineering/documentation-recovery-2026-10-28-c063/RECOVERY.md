# Recovering exact repository bytes

The blocker was a byte-transfer limitation in the previous partial checkouts. The files remained in the authoritative Git tree. C063 recovered their exact bytes without changing repository history or replacing them with Git LFS pointers.

## Working route

1. Read a GitHub **directory** through the authorized Contents API at the exact commit. Its file entries provide the path, byte count, Git blob SHA and an authenticated `download_url`.
2. Retain the returned URL privately and use it promptly for an ordinary HTTPS download. Do not print its credential-bearing query or commit it to evidence.
3. Verify both the declared byte count and `SHA1("blob " + decimal_length + NUL + file_bytes)` against the original Git blob SHA. Record a separate SHA-256 for the recovered content.
4. Keep failed attempts. If a supplied link stops working, fetch fresh directory metadata and retry a small batch. In this run, 1,094 links in the initial large batch returned HTTP 404. A refreshed link recovered one selected file and five batches of at most 220 files recovered the other 1,093. Expired or stale links are a plausible explanation; their provider-side cause was not directly established.
5. Compare the final file set, every blob and mode, and the reconstructed complete Git tree against the immutable source inventory. Source completeness and history completeness are separate claims.

This route differs from asking a text-only connector to decode a binary archive. It also avoids assuming that Git transport already has credentials. The raw URLs are short-lived transfer capabilities, not durable evidence URLs. Durable evidence uses commit permalinks and content identities.

One planned 220-file retry returned exit 0 but its retained per-file ledger contained only 196 entries. The complete source inventory independently verified all 220 payloads. To close the individual receipt gap, the remaining 24 were downloaded again to a separate evidence directory using fresh links; their bytes matched the already verified checkout and all 24 new receipts were retained. The cause of the incomplete retained ledger was not established. No missing execution record was fabricated.

## Exact checkout and failed setup attempt

All 3,458 C062 file blobs were verified against the complete, nontruncated Git tree. Original tree objects and the packet's verified raw commit were installed into a native Git object store; the shallow boundary is explicitly the original C062 commit. No synthetic commit was substituted for that source identity.

The first native-checkout cleanliness check rejected two untracked temporary files left in the recovery workspace. Their identities and [disposition](recovery/local-temporary-files.json) are retained, along with [the original setup error](recovery/native-setup-initial.stderr). They were moved outside the repository without changing any tracked source. The final native checkout was clean. The physical cause of those leftover temporary files was not established.

The C062 handoff and its complete C061 predecessor were verified before recovery. The standalone verifier checked packet membership, content identities, raw commits, full trees, source bindings, retained reviews and predecessor evidence. This did not turn the predecessor's failed documentation receipt into a pass. The new [documentation command](checks/documentation-command.json) independently records the successful execution against the complete source.

## Reproduction

Use an authenticated complete checkout of the identified revision, then run:

```bash
python3 -B docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

To reproduce the bounded C062 calculation without a product request:

```bash
python3 -B docs/engineering/reach-recording-validation-2026-10-28-c062/c062_ancestry_cost_screen.py docs/engineering/reach-recording-validation-2026-10-28-c061
```

Historical C060/C061 auditors bind their original absolute source and evidence paths. Retain their original receipts; do not rewrite paths and call that a reproduced audit. C062's historical `run_checks.py` also belongs to its original executor layout. The commands above invoke the portable calculation and unchanged checker directly.

Recovering ordinary Git payloads does not complete LFS upload, hydration or migration. Follow the separate adopted storage contract for that work.
