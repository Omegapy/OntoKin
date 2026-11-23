# C271 P22 preparation requirements

**Startup verdict:** The exact historical inputs and current receipt predicates are identified. This is a nonexecutable requirements record. No preparation plan or launch is approved here.

The complete identities, 24 dependency mappings, source inventory members, schemas and acceptance predicates are in `PREPARATION-REQUIREMENTS.json`; `READSET.json` distinguishes full reads from targeted source/data inspection.

## Exact inputs

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| P05 Node archive | 45,186,132 | `100ae976555b388472c3e875aeda67bd7d8c9229a968a11661fb852624adaeb5` |
| C195 archive | 2,611,764 | `b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9` |
| Node member | 126,951,512 | `acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa` |
| Node SOURCE.json | 1,349 | `fc4302a6bef50ba5417bceb97d518d6905fff52d4472b9b3e1caa4e22ac0849c` |

The saved Node locator is `libfile_fde3_f-d11430d85e8481918f39a176ca9513e8_2ab2a24d43748191957f9bcc356b59de`, version 0, `/OntoKin/OntoKin_C271_P05_Node_Candidate_2026-11-20.tar.gz`. The Director owns retrieval.

The C195 archive is present at `OntoKin/docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz`; this worker verified its complete-file digest, 2,611,764-byte size, mode 0644 and one hard link. This is not a new full-member audit. The retained P09 inventory records 730 regular members and 42,685,553 expanded bytes. Exactly 24 files map from `c195-validation/receiving/<relative>` to the same dependency-relative names; the other 706 targets remain null. The immutable C199 manifest pins all 24 SHA-256/size pairs. Every selected dependency member is mode 0644.

The Node inventory records two regular members, 126,952,861 expanded bytes, `bin/node` mode 0755 and `SOURCE.json` mode 0644. Both archives contain no directory members, so required target directories and their modes must be frozen explicitly.

## Source and installation evidence

The unchanged preparer is `tools/prepare_current_host_readback.py`, SHA-256 `fd4da23dde3cd75a95c3f5edc071028e5884da62932c32cba4be928e72f87bb3`. Its provider SHA-256 is `2a8144624ea00f3f350a6b7f482c993665b4049b363b93bc399ed0cd7a14ba78`; the current inspector SHA-256 is `e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206`. These match P21's recorded sources.

Freeze one clean ordinary Git checkout and one canonical source inventory. The exact source object contains root, commit, tree and the inventory descriptor. Both installation plans and the later H0 plan must use that **entire same object**, including the inventory's absolute path, hash, size and mode. A source-file hash alone is insufficient. An ordinary `.git` directory supports the later inspector; a linked-worktree gitfile does not.

Plans use `ontokin.current-host-readback-install/0.1.0`, with purposes `selected-node` and `retained-dependencies`. Each binds the archive, full member inventory, complete target files and necessary directories, root mode, selected destination, source object and fresh report path. Plans/inventories/indexes must be sorted compact ASCII canonical JSON with no trailing newline because the later inspector enforces exact canonical serialization.

Only actual `INSTALLED_EXACT` or `ALREADY_PRESENT_EXACT` reports satisfy the receipt predicate. `DRY_RUN_READY` does not. Both require passed=true and zero Node/ldd/checker counts. Each separate index uses `ontokin.current-host-readback-inspection-installation/0.1.0` and exactly schema, plan and report descriptors. Preserve the original reports; never relabel historical source fields.

## Smallest preparation boundary

1. Confirm the Director's early recovery save and recover/authenticate the exact archives.
2. Freeze clean source plus complete canonical source inventory.
3. Freeze two exact plans, external fresh destinations, report/preflight/publication/index/log paths, selected interpreter/environment and external expected plan digests.
4. Independently review those exact plans and all source/input/destination bindings.
5. Invoke each unchanged preparer once: apply for absent destinations, no-apply only for exact existing trees. Stop at the first failure or unknown; preserve evidence and reconcile before any later attempt.
6. Independently verify actual successful reports, source/archive equality, complete destination trees/modes and canonical receipt indexes, then stop before H0/H1.

The preparer imports ctypes and unchanged project helpers, performs five bounded read-only Git subprocesses, and uses `ctypes.CDLL(None)` plus libc `renameat2(RENAME_NOREPLACE)` when applying an installation. These are required mechanics of the unchanged tool and must be stated in the reviewed launch boundary. No Node, ldd, checker, recovered JS, third-party Python package, npm/pip, direct-loader or H0 public-inspector invocation is needed.

## Host and remaining gates

No H0-qualified current host is established. The selected Node build is only v24.22.1; validator remains 2.0.0-dev.3.10, Three.js remains 0.186.1/revision 186, and the exact 564-byte module loader remains unchanged. The unrelated general tools lock cannot substitute. Apply requires Linux and available libc atomic no-replace publication. The later H0 Python/profile and seven-package pins are recorded in JSON for context; preparation does not import those seven distributions.

This worker performed only data/source reads, JSON projection and complete-file hashing. No source product was imported or executed, no installer ran and no target process started. Global startup, source freeze, publication, canonical state and saving remain Director-owned. Next action: Director supplies the concrete plan and confirmed early-save receipt for independent review.

