# P17 startup reconciliation

**P17 startup reconciliation passed.** This audit found no mandatory integrity defect in the handoff, extracted files, saved terminal receipt, or saved terminal audit. Current-session readbacks and the live PR/issue checkpoints confirm P17 partial delivery complete. This does not establish a new early-recovery checkpoint.

## Verified identities

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| P17 handoff ZIP | 20,868,218 | `b13e30cc0c8f7aeb702d31221742e2ed022e4b4d811c5bdad1e5c1909ed5589e` |
| P17 Delivery Receipt | 9,722,465 | `57dc3dbdf127c64cf49725962e2a62d9962430c1bb69395ef7550013e5d38fdf` |
| P17 Terminal Audit | 2,246,699 | `a290eff77f6798b4af7d278ee10f8477cacc0940fc35bfd45e2de0ee212d5153` |

All 813 ZIP entries have safe, unique paths and valid CRC. The 812-row SHA-256 manifest exactly covers the payload, excluding only itself. Every extracted file matches the archive. All 80 source rows and 717 recovery-map rows bind to the exact file inventories, lengths and SHA-256 values. All 80 source Git blob hashes also match.

The receipt contains 71 valid embedded files (7,263,411 raw bytes), including 22 exact repository source blobs. The audit contains 82 valid embedded files (18,513,406 raw bytes), including exact copies of all 71 receipt files. Canonical base64, compressed hashes where applicable, exact decompression, raw sizes and raw hashes all pass. The audit review identity binds to the preserved passing review. Its 13,613 historical assertions were not rerun.

## Revision and pending-state reconciliation

- Observed main: `70ca7e68ff95df876f801137369d176fe5b2bab3`.
- Source checkpoint: `4770a5ea7027ea25d64ef0c339ca360e367dc0cd`, parent `4d259aff76af30381c0796f1527740f76cca1d9a`.
- Receipt checkpoint: `8dc78c0a0ba6b69f502d35e0bbd1727c3c2ab7e8`, parent equal to the source checkpoint.

The source-time `save_pending`, final package review, and receipt-publication fields describe earlier freezes. Later receipt evidence confirms the core ZIP and matching prompt saves and exact readbacks, and retained publication evidence confirms the receipt commit. Only those matching pending fields are superseded. The source records must remain intact.

The terminal receipt and audit froze before their own saves/readbacks and the final PR274/issue273 refresh. The Director confirms these supplied files are current-session saved-file materializations. Their measured hashes match both the expected identities and the completion markers in the live PR274 and issue273 snapshots. Both checkpoints name the saved receipt and audit at version 0 with exact readbacks confirmed. Those later observations supersede the terminal pending fields: P17 partial delivery is complete. The live main and retained branch identities also agree with the authentic checkout, as independently reported by the Director.

## Boundaries

P17 remains an accepted design: 41 controls, 22 images and 63 fixtures; no implementation or runtime qualification. C271 remains blocked and incomplete; R01/R02 are done, R03–R05 are not done, P01 is done and P02 remains in progress. Prior observations show zero statuses and zero workflow runs; no CI pass is claimed.

The 2,508 derivative exclusions have valid declared source bindings. One original source archive is external to this package; omitted derivative bytes were not recursively restored. This is an online continuation handoff, not a complete offline restoration.

No recovered code ran. No Git commands, external calls, repository mutations or implementation changes occurred. All writes remain under the audit directory. A bounded phase declaration and confirmed new early recovery remain prerequisites for technical continuation.
