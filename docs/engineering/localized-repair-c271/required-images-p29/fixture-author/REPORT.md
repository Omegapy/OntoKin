# Independent fixture candidate 004

**Verdict:** ready for independent byte review. All 116 adopted P27 IDs and literal expectations remain unchanged.

The retained focused attempt passed 115 obligations and failed RI-L08. Its inherited RTLD setup attempted `uname -p` through `platform.platform()` only to record metadata. The outer guard blocked launch. Ten supplemental methods ran; 51 RTLD runtime methods were unrun. This failure remains preserved without relabeling.

After reviewer confirmation, candidate 004 adds `INHERITED-METADATA-STUB.json`. Only RI-L08 replaces that recording leaf during its nested suite with “Synthetic P29 RI-L08 metadata; host not probed.” The adapter observes one zero-argument call, exact recorded value, and restoration. All process/checkpoint guards, 61 nested IDs, old tests, commands, cohort and production remain unchanged.

**Checks:** 660 passed; zero failed. The freeze binds 116 payloads and 24 companions. All 111 unaffected prior payloads are byte-identical. Byte and AST comparison permits only the metadata constant, inherited-method wrapper and manifest hash in the adapter. `CANDIDATE004-ADAPTER-DIFF.json` retains the exact diff.

Frozen identities:

- `controls/FREEZE.json`: 31,746 bytes; SHA256 `69065e25738c81ab88cd502edc7069b3b005ba6ae4a67181c30c83f950aa54d5`.
- Adapter: 50,181 bytes; SHA256 `92ed832d2f78509cc60185b5bbfd9da0ff563f595561f5a2cc46e5ff515581a7`.
- Fixture manifest: 21,200 bytes; SHA256 `e98978fe2df14a8862aa7065952068012e2825dc612c5b6c70a939c0376865a5`.

Candidate 003 and all companions remain in the 140-member `fixture-revisions/CANDIDATE003.zip`, SHA256 `56f59a7cab4d8d552a9ccd3ea763e4dad9c187f9a263e2b68e746be0ff6801f1`; eight author files are preserved under `reviews/fixture-author/candidate003/`.

This worker ran no product code. Candidate 004 requires independent acceptance and saved recovery before execution. No P27 design blocker was found; the original P28 597-test claim remains unverified.
