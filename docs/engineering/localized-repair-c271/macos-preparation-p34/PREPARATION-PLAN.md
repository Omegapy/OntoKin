# C271-P34: preparation plan of gate MP

Director `c271-p34-ec1a7de2360d`. This plan carries out gate MP of the adopted contract
`ontokin.current-host-readback/0.2.0`, as amended by P33-AMENDMENT-001 (design revision 4),
under the [phase declaration](PHASE.json).
- **Contract sources:** [CONTRACT](../macos-contract-design-p31/CONTRACT.md) sections 3, 4, 6, 11
  and 12, and [AMENDMENT-001](../macos-implementation-p33/AMENDMENT-001.md).
- **Obligations from MI:** those that gate MI carried to MP
  ([MI's outcome](../macos-implementation-p33/OUTCOME.json), `for_later_gates.MP`).
- **Excluded:** nothing here observes, qualifies or integrates. M0, M1 and the freezing of the
  Python installation inventory belong to MH.

## 1. Inputs and their pins

| Input | Source | Size | Pin |
| --- | --- | ---: | --- |
| Node archive `node-v24.22.1-darwin-arm64.tar.gz` | `https://nodejs.org/dist/v24.22.1/`, owner-approved download | 53,062,778 bytes | SHA-256 `89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7` (contract section 3) |
| C195 archive `recorded-evidence.tar.xz` | committed at `docs/engineering/ownership-recovery-c195/evidence/` | 2,611,764 bytes | SHA-256 `b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9` |
| Seven wheels | `files.pythonhosted.org`, owner-approved download; URLs and sizes in the lock's [provenance](../../../../tools/native-reader-verification-macos-arm64-cp312.provenance.json) | 5,447,056 bytes in all | SHA-256 of each wheel in [the macOS lock](../../../../tools/native-reader-verification-macos-arm64-cp312.lock) |

**Signature check.** The Node release's signature check is not performed. It would need
`SHASUMS256.txt` and its detached signature, and neither is an approved download.
`NODE-SOURCE.json` therefore records `not_performed`, with that reason. Contract section 3 makes the
adopted pin the trust anchor and the signature check optional evidence. D-02 concerns a `failed`
check only.

## 2. Places

Every path below is named relative to the clone; the records name them the same way.

| Place | Use |
| --- | --- |
| `../OntoKin-local/c271-p34/downloads/node/` and `…/downloads/wheels/` | New, empty directories for the two downloads |
| `../OntoKin-local/c271-p34/plans/` | The exact plans, with absolute paths |
| `../OntoKin-local/c271-p34/receipts/` | The preparer's fresh report files and other exact receipts |
| `../OntoKin-local/c271-macos/` | The parent of both prepared trees. It is created empty, on the volume of the stage, so that staging and `renamex_np` stay on one volume. |
| `../OntoKin-local/c271-macos/node-v24.22.1-darwin-arm64/` | The task-specific Node runtime, absent until publication: exactly `{bin/node, NODE-SOURCE.json}` |
| `../OntoKin-local/c271-macos/reader-c195/` | The reader tree, absent until publication: exactly the 24 pinned files |
| the worktree's `.venv` | Prepared in place (contract section 4) |

**Path-portable copies.** The preparer's plans and receipts must hold absolute paths, but records
leave machine paths out. The exact files therefore stay beside the clone. The repository receives
path-portable copies, in which the labels `<clone>`, `<worktree>` and `<local>` replace those
roots, together with the SHA-256 of each exact file.

## 3. The .venv procedure

The setup tool (`tools/bootstrap_local.py`) installs through the environment's own pip, so its
route would leave pip in `site-packages`. M0's exact package rule refuses that (D-21): every
`site-packages` file must be owned by one of the seven `RECORD` files. The worktree's `.venv` was
created without pip and its `site-packages` is empty. MP installs the seven wheels with the pip of
the interpreter installation itself, Homebrew's Python 3.12 (pip 26.0). It targets the `.venv`
through pip's `--python` option, which installs into that environment without installing pip
there:

```sh
PYTHONDONTWRITEBYTECODE=1 <homebrew python3.12> -I -B -m pip --python <worktree>/.venv/bin/python \
  --isolated --disable-pip-version-check install --no-input --no-deps --only-binary=:all: \
  --require-hashes --no-compile --no-index --find-links <downloads>/wheels \
  -r tools/native-reader-verification-macos-arm64-cp312.lock
```

- **Hash enforcement** stays on (`--require-hashes`), from the committed lock. The install runs
  offline (`--no-index`), from the verified downloads only.
- **No bytecode:** `--no-compile`, `-B`, and `PYTHONDONTWRITEBYTECODE=1`. The last one is needed
  because pip starts the `.venv` interpreter without `-I`.
- **Framework unchanged:** the observer's `python_inventory` is computed before and after the step.
  Its framework part must be identical, and only the planned files may be added to the `.venv`.
  This is a preparation check, not M0.
- **The doctor:** its `python-verification` profile includes a `pip check`. With no pip in the
  `.venv`, that check cannot run, and the doctor will report it as not checked. The readiness of
  the `.venv` rests instead on the doctor's package and import checks, the native-reader
  preflight, and the early package check of section 5. M0 at MH decides.

## 4. Workers

Actual Claude Code subagents in fresh contexts, with the session's model. Neither makes a Git
write, downloads anything, or starts Node, `ldd` or `codesign`.

| Worker | Role | Writes |
| --- | --- | --- |
| W1 | Independent preparation author. It wrote none of the implementation. It freezes the inventories, the Node executable's binding, the exact `NODE-SOURCE.json` bytes and the two plans from the contract, before any extraction, and confirms the official archive's member names and modes (D-06). | `../OntoKin-local/c271-p34/plans/` only |
| W2 | Independent reviewer. It reviews the plans and the `.venv` procedure before execution, and later the receipts, trees and `.venv`. | `../OntoKin-local/c271-p34/reviews/` only |

## 5. Steps

1. **Declare and push** this plan and its declaration.
2. **Download (Director).** Exactly the two approved downloads, each over HTTPS into its new,
   empty directory.
   - Each file's SHA-256 is computed before anything else reads it: the archive against the
     adopted pin, each wheel against the lock. A mismatch refuses, and the bytes are kept as
     evidence.
   - A download record holds the URL, start and end times, HTTP status, size and digest.
3. **Freeze (W1).** Reading archive headers and member bytes is allowed; nothing is extracted to
   disk.
   - **Node archive:** the complete member inventory under the rules of the preparer's
     [interface note](../macos-implementation-p33/interfaces/W2-PREPARER.md), section 3; the
     digest, size and mode of `bin/node`, read from its member's bytes; a check that the header is
     a thin arm64 `MH_EXECUTE`.
   - **`NODE-SOURCE.json`:** its exact bytes, computed from the note's section 4, independently of
     the implementation.
   - **C195 archive:** its member inventory and the 24-file mapping to the pinned dependency
     inventory.
   - **Plans and expectations:** the two `install/0.2.0` plans, with their portable copies and
     digests, and the expected `.venv` result.
4. **Review the plans (W2)** before execution. Mandatory findings are resolved and re-reviewed.
5. **Bind the commit.** Commit and push the reviewed plans (portable copies, digests, review). That
   commit is the preparing checkout's bound commit B (D-17).
6. **Prepare (Director),** from a clean checkout at B. Before each run, check that `git status`
   is empty and that HEAD is B (I-03).
   - **The two plans:** `.venv/bin/python -I -S -B tools/prepare_current_host_readback.py --plan P
     --plan-sha256 D`, once as a dry run (`DRY_RUN_READY`), then with `--apply`.
   - **The `.venv`:** the procedure of section 3.
   - **Audit:** every command runs under a Python audit hook that records its process starts, with
     program and arguments only, never the environment.
7. **Verify (Director).**
   - **Receipts:** states, and zero Node, `ldd` and checker starts.
   - **Trees:** each destination read back as exactly its plan.
   - **Preparer source:** the receipt's `preparer_source` compared with B's files (I-03 records the
     limit: four files, not the whole import closure).
   - **`.venv`:** an early package check, the observer's `verify_packages` on the observed
     inventory; the doctor, started with a non-existent Node; the native-reader preflight,
     `.venv/bin/python -I -B tools/check_native_reader_setup.py`.
   - **Records:** the workflow check, the documentation verifier and a scoped whitespace check.
8. **Review the results (W2).**
9. **Close.** Outcome records with portable copies, push, read back, one comment each on PR274 and
   issue273.

## 6. Obligations carried by MP

| Obligation | Where MP meets it |
| --- | --- |
| D-02: a `failed` signature status is a mandatory finding | Not performed and recorded, section 1 |
| D-06: the official archive's member names and modes | W1 at step 3; a refusal is a finding, not a reason to weaken the rule |
| D-17: MP's plan binds the preparing checkout's commit, and its review checks `preparer_source` | Steps 5 to 8 |
| I-03: `preparer_source` names four files | Step 6, the clean checkout at B; the limit is recorded |
| M0's exact package rule | Section 3, and step 7's early package check |
| W3's F4: no interpreter run without `-B` before M0 | Section 3; every MP command uses `-B`. The rule continues until MH has frozen the inventory and run M0. |

## 7. Changes after plan review 001

The fresh-context review [PLAN-REVIEW-001](reviews/PLAN-REVIEW-001.md) accepted the plans, the
expectation and the `.venv` procedure. It raised nonmandatory findings P-01 to P-10, and no
mandatory one. It also accepted the Director's addition of `--no-cache-dir`. All ten findings are
adopted. This section supersedes the parts of sections 3 and 5 that it names.

- **The plans and their digests (P-07).** The preparer runs exactly these reviewed files, each
  passed by its recorded digest, never by one recomputed at run time:

  | Plan | SHA-256 |
  | --- | --- |
  | `node-install-plan.dry-run.json` | `869b6414d42f6ced4ee4ad017ceff7cc63c33b563fcdffcc5999cebebae01d48` |
  | `node-install-plan.json` | `1fee042d5e3c809a89d4975df40f69d7a27e88abf9ba58d8cf91ca16795c5ff1` |
  | `reader-install-plan.dry-run.json` | `a81897783b9df86bb216eb5c371a1191de0a89762e6cd88360c8cc7b7fecf10e` |
  | `reader-install-plan.json` | `ff5a95da6d349e0bd6ea1d2c79fc02757de48ac9cbb89dc59737b67c6d7a71c8` |

  Each dry-run plan differs from its plan only in `report`, because every preparer run needs an
  absent report path (W1's F1). The portable copies are in [plans/](plans/).
- **The bound commit (P-06).** B is the commit that adds these records.
  - It descends from `6d08e026`, against which the review validated the plans.
  - It changes none of the preparer's ten-file import closure: the four `preparer_source` files,
    `errors.py`, `format_check.py`, `lock.py`, `supervisor.py` and the two package `__init__`
    files.
  - It changes neither the C199 manifest, nor the C195 archive, nor the lock or its provenance.
  - Before and after each run, HEAD is B, `git status --porcelain -uall` is empty, and
    `git status --porcelain --ignored` shows only `.venv/`.
- **The `.venv` command (P-03, P-10, `--no-cache-dir`).** It runs from the worktree root, with
  umask `022`, under this declared environment and no other variable:

  ```sh
  env -i HOME=<fresh empty directory> PATH=/usr/bin:/bin TMPDIR=<resolved> LANG=C.UTF-8 LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 PIP_CONFIG_FILE=/dev/null \
    <homebrew python3.12> -I -B -m pip --python <worktree>/.venv/bin/python --isolated \
    --disable-pip-version-check install --no-input --no-deps --only-binary=:all: --require-hashes \
    --no-compile --no-cache-dir --no-index --find-links <downloads>/wheels \
    -r tools/native-reader-verification-macos-arm64-cp312.lock
  ```

  - **Why the bytecode variable (P-10):** pip's `--python` reruns the base installation's pip
    under the `.venv` interpreter, without `-I`, `-E` or `-B`. `PYTHONDONTWRITEBYTECODE=1` is
    needed because that child runs without `-B`. It takes effect because the child also runs
    without `-I` and `-E`.
  - **Configuration:** `PIP_CONFIG_FILE=/dev/null` keeps pip from reading any configuration file.
  - **Recorded:** the receipts record the variable names, pip's version and a digest of the
    installing pip's files.
- **The exact result (P-05).** The `.venv`'s added entries must equal
  [venv-expectation.json](plans/venv-expectation.json) exactly, and nothing else in the `.venv`
  may be added, removed or changed. The additions are:
  - 291 `site-packages` files: 270 by their wheels' SHA-256 and size, pip's `INSTALLER` and
    `REQUESTED` by digest, and the seven rewritten `RECORD` files by name;
  - their directories;
  - `bin/jsonschema`.
- **In place of `pip check` (P-01).** A metadata-level check reads the `Requires-Dist` of the
  seven installed `METADATA` files. Each requirement that applies on Python 3.12, without an extra,
  must be met by the installed pins.
- **The doctor's expected result (P-01, P-02).** It runs with a minimal `PATH` and an absent
  `--node` path, and its JSON report is kept.
  - **Ready:** lock, packages, imports and native reader.
  - **Not checked:** pip check, and so the `python-verification` profile; exit status 1.
  - **Rebuild advice:** the doctor advises a rebuild with the setup tool. It is deliberately not
    followed, because that route installs pip (D-21).
  - **The absent Node path:** the doctor makes one attempt to start it, which fails before any
    image runs. The audit records it as a failed attempt on a non-existent path, not a Node start
    (A7).
- **The audit's limit (P-04).** The hook sees the starts of the audited process, among them pip's
  one start of the `.venv` interpreter. Starts by that child are outside it. By reading pip 26.0,
  that child starts nothing for this offline, binary-only, no-dependency install: packaging's
  `mac_platforms` starts an interpreter only when it reports macOS 10.16, and this one reports
  26.6.2.
- **The audit wrapper (P-08)** leaves `sys.path` as `-I` sets it.
- **Retention (P-09).** M0 binds each plan's archive again by path, SHA-256, size and mode (the
  observer's `_install_receipts`). So both archives stay unchanged at their paths until MH:
  - the Node archive, with mode `0o444` and one link;
  - the committed C195 archive.

  Contract section 7's `.DS_Store` rule applies to the prepared trees once they are published, so
  the trees are not opened in Finder.
