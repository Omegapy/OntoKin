# P16 tag-design startup dependency map

Worker: `/root/tag_design`. Current state: paused for Director-confirmed early recovery release.

## Required dependencies

1. Director confirms the new early recovery ZIP save and permits substantive P16 work. The worker does not repeat global startup or delivery.
2. The P15 first-refusal records bind the inert libc capture (SHA-256 `9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92`) and unchanged reader (SHA-256 `a8274d56076562a91d26b3cdd2f614fce6fd509733e4939b225dff2ddca09db4`). They establish only the recorded tag refusal; the later flags predicate was not reached.
3. After release, inspect the already retained exact glibc source archives, source/package provenance, and all definitions and consuming code for numeric tags `0x70000000`, `0x70000001`, `0x70000003`. Primary ABI material is needed only if the exact retained source cannot support the finite compatibility conclusion. No new semantics have been investigated at startup.
4. Any proposal must use a separately versioned opt-in, retain default/legacy parser behavior, original controls, all pins/limits, and the P13 external source-completeness boundary. Frozen inert fixtures and independent expectations may describe only the approved future seam.
5. Root owns independent review routing, adoption, canonical records, publication and delivery. This worker owns only this scratch directory.

## Source locations identified for after-release review

- `incoming/p15/recovery/session/source-provenance/downloads-attempt001/`: exact `.dsc`, upstream tarball and Debian source tarball plus source pins.
- `incoming/p15/recovery/session/source-provenance/`: source manifest, retained review/provenance reports.
- `incoming/p15/recovery/session/h0-static-admission-attempt001/`: inert input capture and first-refusal evidence (exact filenames to be selected from manifest after release).
- Adopted P05/P07/P11/P13 designs and P15 blocker records in the retained checkout; exact read identities in `STARTUP-READSET.json`.

## Stop boundary

No production/test implementation, product parser execution, current-host H0/H1, Node/ldd, original-seven/full routine, installation, native/model work, main integration or parent closure. No Git/index, canonical-record or Library writes. The next worker action requires Director release.
