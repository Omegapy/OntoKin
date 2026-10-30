# C076 independent integration review

**Passed within the observed scope; no integration blocker found.** This read-only review inspected saved integration receipts, exact immutable Git objects, and the completed merge-focused receipts. It performed no product test execution and no remote writes or new remote lookup.

## Verified integration

- Lease `d344cb35845a2a03fd7251780d1cb22363442191`, tree `bc89e2d76c662d7726b3012a56d6185cdab73ca3`, has the exact C075 baseline as its sole parent and changes only `STATUS.md`. Its bounded owner/expiry and incoming evidence identity match preparation and acquired-lease records.
- Actual merge `bb9322f013d71b90c154a909e1e76c7651eb4995`, tree `d18802d043d2a151944d6e0ac74b76fc72a4635e`, has the ordered parents `[lease, 89e9b7222fc2a0ba66eb49020940e6895a4fde40]`. The verified raw commit bodies agree with both saved GitHub commit records and local Git objects.
- The merge tree is exactly the incoming evidence tree with the lease's `STATUS.md`. It matches the tree calculated before merging. The merge occurred at 19:19:29 UTC, inside the 19:18:46–19:48:46 UTC lease.
- Saved readback identifies main at that exact merge and PR #74 as merged/closed. Its branch list contains only main and the unchanged history archive. The removed work head is retained as the merge's second parent.

## Candidate and historical preservation

All **4,071 eligible candidate files** retain exact Git blob identities and modes at the merge. The only excluded paths are `STATUS.md` and the current C076 engineering-record directory. The equality digest is `2406c94f31db3ac4a805bf20da4cfaec1b0352710903ad7ac2ad8b548db076ef`.

All **3,990 baseline paths** remain present; all **975 protected old tests, examples, workflows, schemas and language-design paths** retain bytes and modes; all **64 frozen C076 contract/fixture paths** retain bytes and modes. No removed baseline or changed protected/frozen path was found.

## Finished resulting-main receipts

The exact-merge runner completed all five steps successfully at **19:20:06 UTC**: **80 new unit tests**, **43 original source cases / 694 assertions**, **55 holes cases / 308 workflow assertions**, documentation checks, and complete input eligibility. All five saved log sizes and hashes match their summary. The holes workflow records **62 exchanges / 60 durable requests**, 62 schema-validated exchanges, and 17,594 operations for its repaired export. All 19 delivered GLB byte identities match the recorded artifact hashes, and their saved geometry results report passed.

The complete 4,093-file before/after acceptance source inventories are byte-identical and agree with the immutable merge's source bytes. Candidate blob digests were reused only under matching immutable Git blob IDs from the earlier fully byte-verified author-provenance index; added or changed merge blobs were read and hash-verified separately.

## Limits and next action

This is a review of captured remote responses, not a fresh remote observation. Raw Git identities were verified; the provider's OpenPGP verification claim was not independently revalidated. The CAS preparation, success response, actual lease parent and observed remote head agree, but this review did not replay the CAS request. Focused merge checks do not imply another full regression execution or release acceptance. Candidate destination evidence is reusable through complete input equality; this review does not claim a new browser, Khronos or visual validation run.

The actual merge still contains the live integration lease. The coordinator should publish the verified integration outcome and release the lease, then complete final-state verification and handoff. `integration-review.json` preserves exact source identities, checks, and byte hashes for every reviewed receipt/log/artifact.
