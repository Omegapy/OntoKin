# Independent evidence capture and recovery review

The reviewed packaging tools pass all 46 bounded actual cases. The capture source SHA-256 is `bcd2dfb0fe43c191bc4ac08382d42735b4da34ae8625ea2ab700487edeb8baa4`; the recovery source SHA-256 is `f7be315c10fc4c3af98a34ec3f0fb48933a72241daa5e56f6b5ab1b5a8aad6ee`. The independent reviewer is the runtime agent; the root agent authored these tools. The companion JSON binds all cases, source hashes, review findings and sealed raw fixtures.

## Verified behavior

A fresh independent Git repository and small input set exercised binary content, NUL bytes, exact CRLF/UTF-8 text, a non-ASCII path, an empty file and ordinary modes 0640, 0600, 0644, 0751 and 0444. The original file bytes, complete ordinary modes, independent SHA256, native blob SHA1 and exact native tree membership were checked during capture and after recovery. The fixture product source HEAD, index bytes and source content remained unchanged across every case. No original OntoKin source, original execution evidence or reviewed tool was edited by the reviewer.

The capture tool now opens ancestor directories without following links, hashes ordinary inputs through file descriptors, records original full modes and identities, and repeats the complete selected membership/stamp admission before commit and before publishing its separate archive ref. Its private 0700 native index directory prevents a predictable temporary-index link from redirecting writes. The archive tree contains the exact original files plus one reserved native index blob; that blob binds all ordinary file modes as well as path/body identities, counts, totals, source parent and scope.

Recovery admits strict native counts and hashes, verifies the exact archive commit/tree/ref and sole source parent, checks full native header/body identities for the source and archive commits, all relevant trees and embedded index, then requires complete tree membership equality. It writes to fresh nofollow destinations, streams each native blob while calculating both full SHA256 and native SHA1, checks the external manifest remains unchanged, and performs a complete final destination inventory and file fingerprint pass before publishing success.

The unchanged shared helper is `handoff_common.py`, SHA-256 `38d84de5e3662efcd47519517da38e8fef841744d50cdafe4246652c0e2273ab`. The earlier strict source-recovery implementation has not been weakened or edited.

## Preserved findings and actual replay

The first version accepted a linked ancestor in a nested include, silently omitted a file added after enumeration, accepted inconsistent archive commit/source/ref metadata and floating counts, and permitted a different ordinary mode because the native tree only bound the executable bit. Separate actual tests also showed an already-restored file could change before the next native batch request, an extra output could appear, and a dangling predictable index link could redirect a write. All 11 original unexpected acceptances are retained rather than reclassified.

After those corrections, one coherent native-authority witness remained: changing a copied loose embedded-index object under its old object name, and updating the external mode/hash fields consistently, produced a success report with the wrong original mode. Git's blob read did not itself verify that old native name. The final decoder explicitly hashes the full native header and body, and this witness now refuses. Equivalent tree and commit body mutations were already rejected by native Git in the earlier revision; the final decoder rejects them directly through the same explicit identity check. No hypothetical tree/commit acceptance is claimed.

The final run covers the original 40 cases, three late-output/index-link cases and three coherent native-authority cases: two valid controls and 44 expected refusals. Every outcome matches its expectation. The original existing report sentinel remains untouched; every late output-change case refuses without a success report. A first test preparation error attempted to write a read-only copied Git object; that failed attempt remains retained, and the later fixture explicitly adds owner-write permission before its deliberate corruption. The product tools were not changed to accommodate the test.

## Exact fixture retention and scope

The small test workspaces intentionally contain Git control directories and symlink fault inputs, which the ordinary evidence capture tool should not traverse. Each complete workspace is therefore retained as a regular-file `FIXTURE-WORKSPACE.tar.gz` with a `FIXTURE-ARCHIVE.json` inventory. Every file body and ordinary mode, directory mode, path membership and link target/mode was independently checked against the archive before moving the redundant unpacked copies outside the evidence capture root. Actual reports, manifests, driver text and logs remain directly readable beside each archive. No unique failure, native object or test input was omitted.

These fixture archives are opaque review data. The evidence decoder restores their exact archive-file bytes; it does not unpack their deliberate link fixtures or Git control data into product source. The archival Git commit itself must never be checked out or merged into the product branch.

This approval applies to the exact listed tool bytes and bounded cases. A full-size capture, native pack generation and fresh complete evidence recovery still need their own actual receipts. It adds no torque acceptance, main-merge or GOAL-completion claim.
