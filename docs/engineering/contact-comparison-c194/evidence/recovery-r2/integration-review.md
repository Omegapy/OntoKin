# Independent C194 integration review

The reviewed C194 recovery scope passes after one narrow extractor correction. The complete source runtime, tests, tooling, language contracts and hosted workflows remain unchanged from observed main `ee7dc2b71710dc8963b01ab6db68a1c75e22c27a`. Of 13,570 historical tracked files, only the three navigation/status documents change; all 13,567 others are preserved. New preparation and comparison files are confined to C194. Final committed-candidate review and actual integration remain separate steps.

## Portability defect and correction

The first actual extraction failed with `Unexpected archive directory: preparation/builds/ok-G/store/.staging`. Three legitimate empty directory entries occur in the original preparation/first-validation archives. The initial extractor derived its permitted directories only from file parents, so it rejected these empty entries. The failed log and original helper remain preserved. No partial destination was published.

The reviewed correction permits and skips safe, mapped empty directories while rejecting file/directory ancestor collisions. It changes neither archive nor file-manifest bytes. The original traversal, root, link, member, duplicate, file-set and content-hash checks remain. The successful actual extraction verified **1,038 files and 77,154,823 uncompressed bytes** across the three unchanged archives.

## Fresh relocated recorded replay

The portable replay passed **1,755 integrity, receipt and numerical assertions** covering **16 recorded construction artifacts**, **10 original saved-scene replay receipts**, and **30 original image identities with visual-review receipts**. The independent mapping reader reproduces bounds of **0.07451646802035088 mm** and **0.116442262620993 mm**, within the unchanged 0.2 mm limit.

These are assertions, not unit-test counts. The separate evidence reviewer reports 3,925 integrity/consistency assertions; those are also not unit tests. The inherited failed legacy driver and supplemental tail, 4,239 passing methods, and thirteen torque methods not run retain their original disposition.

No native construction, saved-scene resimulation, author dispatch, or receiving-application execution occurred in this review. Existing visual observations were checked through exact retained receipts and image hashes; this reviewer did not perform a new visual inspection. Execution used CPython 3.12.14, Linux x86_64, and NumPy 2.3.5.

The JSON report identifies helper/log/output hashes, actual scope and remaining publication gates. The extraction and replay reports, exact failed and successful logs, and historical-scope receipt accompany it.
