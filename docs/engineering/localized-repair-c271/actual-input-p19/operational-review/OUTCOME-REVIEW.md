# C271 P19 independent actual-input outcome review

Reviewer: `/root/operational_review`.

## Verdict

**Accepted as a correctly stopped, blocked input-readiness observation.** The first new blocker is the fifth package pin: the retained `rpds-py` METADATA reports `2026.6.3`, while the unchanged authoritative lock requires `2026.5.1`. The actual observation stopped with exit code 2. It did not inspect the last two packages' metadata, install a dependency, substitute an input or continue to H1.

The Python, loader and libc raw readers returned metadata for the exact pinned current input bytes. This is useful evidence beyond P15's historical tag refusal, but it is not operational policy dispatch, complete loader-selection proof or H0 acceptance. The earlier refusal and all frozen historical expectations remain unchanged.

There are no mandatory findings in the retained outcome. Technical work must remain stopped. Documentary verification, publication and verified partial delivery may proceed under the Director's existing scope.

## Exact acceptance and execution identities

The executed source and plan match the separately accepted candidate003:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Observation script | 12,873 | `c14b171df87d47dbd78d6a73946c72c32add8891d6d52b0a7e1da697cdd1e287` |
| Observation plan | 2,707 | `946fd14dc1022ddb1e9cc4d8f22a0c0a2746efb3b0b9c08db62cd70c17945aab` |
| Production inspection source | 196,305 | `e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206` |
| Authoritative seven-pin lock | 779 | `a7f17491000c2e139ccc5d213ca0e8a6f917e5befb4b878fef29f5ff72ae780f` |
| Retained failed rpds-py METADATA | 4,147 | `f8be7b17da3980b2c48596941411a43c70ac41b1e2d530aa531f2c15eab2eb1c` |

The source module and lock were independently hashed again as repository files, without reopening recorded host inputs. Both remain byte-identical to their accepted source identities at `2f791017c6559bfd47937b32b1862cfe98a81551`. The plan discloses documentary worktree changes and makes no clean whole-tree claim.

`LAUNCH-INTENT.json` binds the exact plan, independent approval and wrapper hashes. The wrapper source contains one subprocess invocation, no shell and no retry loop. Its argv, cwd and five-variable environment match the plan. The child uses the exact selected Python with `-I -S -B`. Inner intent and result bind the accepted script and production source. Raw stdout/stderr hashes agree with `LAUNCH-RESULT.json`; stderr is empty. Outer execution completed in approximately 0.534 seconds, with the inner observation reporting approximately 0.462 seconds, within the 60-second limit.

## Independently reproduced package finding

The reviewer read and hashed all five retained METADATA files as data. Python's standard-library email-header parser independently extracted their Name and Version fields; it did not reuse the observation's regex parser, import packages or inspect current site-packages. The immutable lock supplied the expected names, order and versions.

| Lock order | Package | Required | Retained METADATA | Finding |
| --- | --- | --- | --- | --- |
| 1 | attrs | 26.1.0 | 26.1.0 | Name/version match only |
| 2 | jsonschema | 4.26.0 | 4.26.0 | Name/version match only |
| 3 | jsonschema-specifications | 2025.9.1 | 2025.9.1 | Name/version match only |
| 4 | referencing | 0.37.0 | 0.37.0 | Name/version match only |
| 5 | rpds-py | 2026.5.1 | 2026.6.3 | First mismatch; stopped |
| 6 | typing_extensions | 4.16.0 | Not inspected | Unmet |
| 7 | Pillow | 13.0.0 | Not inspected | Unmet |

Each retained file's byte count and SHA-256 matches its observation record. The fifth row exactly equals `first_blocker.details`; its category is the harness's `InputBlocker / PACKAGE_METADATA_PIN_MISMATCH`. It is an input-readiness finding, not an observed `HostInspectionError` from the production inspector. A newer version is not accepted as the unchanged exact pin.

There are exactly five saved METADATA artifacts and five package-result rows. The last two package metadata paths are absent from the retained artifacts and from the post-read set. The directory-name scan necessarily preceded selection; “not inspected” here means their METADATA contents were not read or checked. No broader package-byte, dependency-resolution, import-compatibility or full dist-info qualification follows from the first four matches.

## Raw metadata and preservation evidence

The retained identity records match the fixed Python, libc and loader byte counts, SHA-256 hashes and `0o755` modes. Their selected-process map rows have matching recorded inodes and devices. This review checks the retained witnesses; it does not reopen `/proc` or independently rerun the host observation.

All three metadata rows retain the expected nine-field shape and explicit raw-primitive scope:

- Selected Python: `_read_origin_elf_metadata` returned its actual interpreter, six needed names including `libc.so.6`, and raw `$ORIGIN/../lib` RPATH.
- Loader: the conservative `read_elf_metadata` returned metadata without a needed dependency.
- Selected libc: `_read_libc_static_tls_elf_metadata` returned metadata under the private `/0.1.3` metadata rule, including its loader needed-name.

The recorded relation is intentionally limited to the actual Python needed-name and interpreter/mapped-file witnesses. It explicitly leaves complete loader selection unproved. No caller-created operational policy, fake complete plan, source-completeness approval or `STATIC_READY` was produced.

All ten final file identity/hash rechecks passed: the three selected images, production source, pin lock and five consumed METADATA files. `postflight_failures` and process-operation-attempt lists are empty. The observation records zero child/target starts. The precise execution denominator is one Python observation process, with no guarded child/target operation attempted inside; this is not an OS-wide claim that no other process ran.

## Preserved prelaunch failure and review corrections

The first outer-wrapper attempt failed its `review.is_file()` assertion before writing `LAUNCH-INTENT.json` or reaching `subprocess.run`. The Director recorded absence reconciliation before the later invocation in `state/OPERATIONS.json`. The reviewer inspected that record, the exact wrapper ordering and the later single launch/result/attempt evidence. This is a completed nonproduct preflight failure; it is not a retried product observation or an unresolved child.

Candidate001's three review findings, candidate002's remaining enumeration issue, candidate003's acceptance and the reviewer's copy-provenance race/correction remain preserved. None was an executed observation attempt. The accepted run consumed candidate003 once.

## Independent audit and limits

`audit_retained_outcome.py` produced `OUTCOME-AUDIT.json`: **41 retained-artifact checks passed; zero failed**. These are evidence/source/data checks, not product tests. The audit verifies identities, approval and launch linkage, command/environment, exact five-file package evidence, independent headers, first-blocker/order, raw-reader labels, selected-map consistency, complete ten-file recheck set, unchanged source/lock and explicit unmet gates.

The audit ran only on saved artifacts and repository source/lock bytes. It did not import production, rerun the observation, reopen host binaries, read the last two package metadata files, execute Node/ldd, install packages or invoke a full operational plan.

H0 remains unaccepted; H1 remains unapproved. Full source/runtime/loader/metadata closure, actual origin nonselection and independent operational-plan review remain required. N57 remains an external review obligation, without a runtime pass or skip. The original seven, full routine/R03, main integration/R04 and final parent closure/R05 remain unmet.

The next technical action belongs to a fresh bounded phase after this phase's verified partial delivery: review a concrete way to prepare the unchanged seven package pins for the selected interpreter while preserving the fixed runtime, source contracts and consumer lookup behavior. The first mismatch is not permission to alter the lock, patch shared packages, change interpreter inputs or repeat H0 in this chat.
