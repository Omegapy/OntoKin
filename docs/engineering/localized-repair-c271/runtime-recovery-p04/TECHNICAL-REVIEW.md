# Independent P04 technical review

**Accept the scoped negative recovery evidence. C225 remains unqualified and R03 remains unaccepted.** The investigator found no authenticated historical Node executable in the inspected sources. The evidence does not establish global unavailability or complete historical source closure.

## Reviewed identities and verification

Investigator: `/root/runtime_recovery`. Reviewer: `/root/github_reconcile`. Investigation source reads began at published branch `6d4324e8fd835351da2db165bf0907a3bf1916bc`; the Director's later documentation-only bootstrap is `e7962d64cad08b52fb32cf4cf34c3f77e1337156`. This review does not replace the later final-source/publication review.

The frozen investigator `ARTIFACTS.json` has SHA-256 `3852e7a267d091caf6ba7231c0db614a1db8822ce7ae4f14b5b56dc7217cbe05`. All 2,094 listed files were independently rehashed and their byte counts checked, totaling 138,041,982 bytes. The manifest stayed unchanged during the audit. The review also checked source methods and preserved error dispositions. All 678 technical evidence predicates passed; these are evidence inspections, not product tests.

The reviewer independently authenticated the cached C262 ZIP against its declared 532,260,846-byte identity and SHA-256, compared its complete central-directory inventory, and queried the isolated Git object database. Its 18,208 objects and 14,104 blob sizes exactly match the investigator inventory. Every unique blob has one corresponding request and a full-read size/digest record. No stored blob has the required Node size.

For the split archives, the reviewer read the original manifest Git objects, independently rehashed 413 declared part occurrences, checked declared order/offsets, recomputed each assembled archive identity, and checked the actual assembled caches. Forty-three manifest declarations cover 35 unique archives; duplicate declarations are not presented as additional archives. The report's 37,798 additional archive-member observations reconcile with the two passes.

The two unresolved thin packs and the additional author-history bundle were independently parsed at the pack/header level. Their SHA-1 trailers, object counts, payload lengths and delta-result lengths match the retained reports. This verifies the stated size evidence; it does not materialize missing bases or prove the contents of unresolved delta-derived objects.

## Current host and negative-search scope

The independent current-binding audit rehashed the six pinned source files and ten runtime/configuration files and checked all ten aliases. All six source pins and all aliases match. Nine runtime files match; Node alone differs. Both historical preparation destinations are absent without symlinked path components. The approved C225 helper is unchanged.

The local searches record 522,972 regular-file observations, not unique physical inodes. Five named candidates were hashed; none matches the required 126,939,688-byte executable and SHA-256 `61ab14cd750fc24d5db53490ec5fc40f756e4b6e136b78cf7004265471d9bd1d`. Candidate selection checked exact size independently of filenames. The initial scan's 373 errors were classified as broken symlinks; the supplement records 16 more and three inaccessible directories. Those access limits were retained, with no bypass.

The initial archive inspection's `complete_within_scope:false` and original errors remain preserved. Thirty-five split-prefix errors were reconciled with declared, authenticated archive assemblies. Remaining limits include five incomplete ZIP prefixes, one incomplete XZ source, missing Git delta bases, one header-only bundle record, and unmaterialized delta content in the supplemental author bundle. No small delta result, archive prefix, filename or hash-shaped record is treated as a recovered executable. Excluded/unmounted/deleted/remote sources remain outside the search.

An exact executable recovered at a different path would still be only artifact recovery. Unchanged C225 qualification requires its original absolute path, exact modes/aliases and the remaining preparation closure. No runtime replacement, namespace change or guard bypass was performed.

## Acceptance and next action

The evidence supports a truthful partial handoff at this blocker. It supports no C225 preparation pass, full-routine pass, R03 acceptance, integration, parent closure, H22/C260 qualification or whole-product claim. No Node, `ldd`, helper, product/native test or full routine was launched by the investigator or this reviewer. The investigator records no active process or unknown write at its freeze; historical global process uncertainties remain outside that statement.

`CURRENT-HOST-QUALIFICATION-PROPOSAL.md` is an unimplemented, unadopted recommendation for a later phase. It preserves historical C199/C225 source/pins/refusal evidence and requires a separately versioned operational decision, actual host bindings, exact method/transitive-predicate mapping, required refusal controls, and truthful default-discovery inventory before any full routine. A supplemental passing host suite or replacement manifest cannot clear the original hardcoded methods.

That proposal was authored by this reviewer and has no independent adoption approval. The Director and a later independent review must assess the actual operational design. P04 implements none of it. Final canonical record checks, publication, package review and confirmed saved delivery remain Director-owned gates.

## Evidence files

`TECHNICAL-REVIEW.json` retains the detailed checks and exact manifest identity. `CURRENT-BINDINGS-REVIEW.json` contains direct current-file observations. `EARLY-PACKAGE-AUDIT.json` and `EARLY-PACKAGE-REVIEW.md` establish the early package's integrity and saved-receipt boundary. `REVIEW-ATTEMPTS.json` preserves the initial static-audit parser error and early-package checker false positive; neither changed project bytes or the archives. The investigator's own fragment-checker failure and parser/import errors remain in its frozen evidence manifest.

Use the review `ARTIFACTS.json` for the frozen technical evidence payload. Exclude the two early extraction directories, which are duplicate inspection copies.
