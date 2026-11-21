# C271 P11 independent intake and recovery review

Verdict: **PASS for online continuation, with the declared P09 binary dependency.**
No blocking package-integrity or source-binding finding remains. This is an intake
review, not acceptance of H0, H1, R03–R05, runtime qualification or integration.

## Exact inputs

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| P10 handoff ZIP | 10,556,884 | `42739db560ae8a46706d41ded21038d44a8a8a61ac45d6792374a7e31306c275` |
| Separate P10 terminal receipt | 1,767,981 | `4195824db6585ebeed3f0bef1b933c9b465a6541f9ff155a38767f853c7232f5` |

The archive freezes commit `d07c51e5c75bb4f25928be4008e08ca83bd8df8c`
(tree `5bc1e52aa30968f9c7b009bd64929da470454b93`). The behavioral source is
`fdacc11349079be21bcce755b18ca660df4d96a2`. The separate receipt binds the
published documentary head `e0119f376441fee0fc3956852ac63110ab141011`
(tree `d976520ede52f9227ce2df5bab974d6e1bc2ef79`). Observed main is
`e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`. The frozen checkpoint and
receipt consistently retain draft/open PR274, open issue273 and the unfinished
branch `work/c271-missing-import-digest-control`.

## Independently checked

- All 3,312 ZIP members are safe regular paths with no duplicates or CRC failure.
  Every one of the 3,311 manifest payloads has its exact declared size and digest;
  extraction into a fresh audit directory has the exact declared inventory.
- All 560 source snapshots match the actual Git commit/tree/blob/mode and bytes.
  The 277 omitted frozen-input copies map to 276 exact Git inputs and one explicitly
  local recovery runner. All match their declared bytes.
- All 447 direct recovery files match their map. The 14,578 fixture entries map
  consistently to 2,287 exact blobs, covering 9,895 regular files and 304,413,776
  logical regular bytes. Symlink text, hardlink groups and the declared FIFO are
  represented as data. No special filesystem object was created or followed.
- The 15,320-entry declared unique-artifact inventory has valid retention or
  reconstruction mappings. The compressed canonical focused manifest decodes
  exactly to its retained 6,959,716-byte raw record.
- The terminal receipt's 80 compressed blobs decode correctly and recover all
  107 late files (12,243,092 logical bytes): 99 were absent from the frozen archive
  and eight replace older evidence. They are restored inertly under `receipt_late/`.
- The receipt's 20 repository files are exactly the full `d07c51e5…` to
  `e0119f37…` Git delta; each equals its published Git bytes. All are under `docs/`.
  The execution-to-freeze delta is also documentary only. The core receipt equals
  the canonical published `P10-DELIVERY.json`; referenced package verification,
  package review and receipt review hashes match the published files.
- The inspector bytes are identical at execution, frozen and receipt commits:
  `0c2ef54a227e2e05a7eb1f71a4fedd934399aa27d98ec7a3845f93a4dbfbb612`.
  Prompt member bytes match their separately saved identities in the receipt.

## Recovery implications and limits

Preserve both the ZIP and terminal receipt. The ZIP alone omits unique late audit,
save, publication and verification evidence by design; the receipt carries those
bytes. `fresh_extract/` is a mechanically reproducible extraction of the ZIP.
`receipt_late/<relative_path>` is reproducible from
`late_evidence.files[*].relative_path` and the corresponding SHA-keyed
`late_evidence.blobs` entry. These two directories need not be recursively embedded
again if their exact external source identities and reconstruction instructions
are retained. The independent audit scripts, logs, original failed checker result,
corrected result and this report are new evidence and must be preserved.

The exact selected Python fixture is **external to P10**. It is P09 member
`recovery/h0_work/selected-python.bin`, 30,894,944 bytes, SHA-256
`fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`.
The containing P09 archive has SHA-256
`906cde26c8ddca52c68ff87c9836e28feabdb132fc8dd130ce3b46e7f9851c56` and
Library ID `libfile_fde3_f-6ce009b09ccc8191955ae8cd95d781be_2ab2a24d43748191957f9bcc356b59de`.
Obtain and verify those bytes before a future check requiring that exact input.
The P10 package accurately discloses this dependency.

The old P10 workspace is unavailable; checking its declared inventory cannot prove
that no original file was omitted from that inventory. This reviewer did not repeat
the remote Library save/readback or re-observe GitHub: the supplied saved bytes and
the Director's startup observations are the intake boundary. No product tests,
runtime programs, Node, `ldd`, original seven, full routine, runtime preparation,
Git mutations, main integration or publication were performed.

The preserved `$ORIGIN/../lib` refusal remains a blocker. H0/H1 are unaccepted,
R03–R05 remain not done, and parent C271 stays blocked. Historical C270 completion
and global prior-process termination remain unestablished.

## Audit attempts and evidence

The first checker incorrectly assumed every frozen-input alias must be Git-backed.
Its single failure concerned the explicitly local saved runner. `audit_followup.py`
corrected that assumption and rechecked all 277 aliases without altering the package.
`REVIEW-RUN001.json` and `RUN001.stdout.json` preserve the original result. Several
exploratory reads produced truncated output; they were replaced with bounded reads
and complete mechanical checks, as recorded in `REVIEW.json`.

`REVIEW.json` holds all final pass/fail claims and exact identities. `COMMANDS.json`
records data-only Git inspection commands. `RUN001.*` and `RUN002.*` preserve outputs.
The reviewer is `/root/intake_audit`; writes were confined to this assigned audit
directory. No current unknown write or active audit process remains.
