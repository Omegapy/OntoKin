# C271 P20 environment preparation gate review

Reviewer: `/root/environment_review`. Source branch/head supplied by the Director: `work/c271-missing-import-digest-control` at `4bf7cb0023d1747be16c8752795819dd9a0cca37`.

## Decision

A separate, isolated Python verification environment is a viable candidate for this phase. **No installation or concrete command is approved by this preliminary review.** Early saved recovery, exact input and installer identities, destinations and commands remain the next review gate. The Director owns those decisions, all Git/canonical changes and delivery.

The accepted boundary is preparation and static identity evidence for the unchanged seven-package lock, or the first concrete blocker. Complete operational H0, H1, host qualification, original-seven/full-routine evidence, integration and parent closure remain later work. C271 R03–R05 remain unmet.

## What the source establishes

P19 observed `rpds-py 2026.6.3`, while the unchanged lock requires `2026.5.1`. Four earlier package versions matched; `typing_extensions` and `Pillow` were not read after the first failure. That failed readiness result must remain unchanged. [S1]

P07 requires the inspection author and later qualification to use the **same resolved Python executable**. Its inspection launcher uses `-I -S -B`; distribution metadata comes from explicit approved paths, with no site-directory injection or package import. The later ordinary provider must independently agree through `importlib.metadata`. Package version agreement alone does not authenticate every installed package byte or qualify the host. [S2, S3]

P11 fixes the actual selected Python to SHA-256 `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`, 30,894,944 bytes and mode `0o755`, under ordinary direct-main invocation. Its canonical subject and ancestors must remain nonsymlink paths. A task-local venv alias that resolves to that unchanged canonical file is structurally compatible with the provider's `Path(sys.executable).resolve()` comparison; copying or replacing the selected interpreter, changing its origin or switching builds is not the proposed route. Actual alias and environment behavior still need verification. [S3, S4]

The seven required wheel hashes are already frozen in `tools/native-reader-verification-linux-cp312.lock`. It includes `attrs 26.1.0`, `jsonschema 4.26.0`, `jsonschema-specifications 2025.9.1`, `referencing 0.37.0`, `rpds-py 2026.5.1`, `typing_extensions 4.16.0` and `Pillow 13.0.0`. The six-line force-agent requirements file is not a substitute. [S5]

P05's exact 24-file Node readback dependencies and safe preparer are distinct from these seven Python verification distributions. Preparing this Python environment does not install or qualify the Node/validator/Three.js inputs. No Node or loader execution is needed for this bounded phase. [S6, S7]

## Minimal candidate approach

1. Confirm early saved recovery and freeze the concrete preparation record. Bind the actual current canonical Python and its aliases, existing installer/bootstrap identity, exact argv/environment/cwd, input lock and wheel hashes, external fresh destination and evidence paths.
2. Obtain only the seven lock-matching compatible wheels. A wheel-only, hash-required, no-dependency acquisition avoids source build hooks and unreviewed additional dependencies. Missing or mismatched artifacts are a blocker; preserve the result without changing pins or silently retrying.
3. Create an isolated venv using the unchanged selected Python, with symlinks, without system site packages and without implicit pip bootstrap. Install the reviewed wheels using a separately identified existing installer, `--no-index`, exact wheel directory, `--no-deps` and hash requirements. The precise command syntax and installer behavior remain subject to the concrete review.
4. Read actual installed `METADATA`, `WHEEL`, `RECORD` and the complete relevant `.dist-info` inventories as data. Record exact paths, names/versions, modes, hashes and native extension file identities. Do not import `rpds`, Pillow or the other installed distributions; do not run wheel scripts, native extensions, `ldd`, a loader, product helpers or a checker.
5. Independently review the actual prepared-input evidence, preserve every attempt, and stop. Preparation success is not ordinary-provider metadata agreement, operational-plan admission or H0 acceptance. Those require later exact input rebinding and review.

`venv` and installer execution are preparation processes that must appear honestly in the plan and results. A “zero process starts” claim would be incorrect for this route. Zero target/Node/ldd/native starts is a separate, narrower claim.

## Required concrete-plan checks

The next review must resolve the installer's real executable or Python bootstrap, source/version, subprocess behavior, configuration files and network/index provenance. A clean environment alone is not proof that a package manager ignored configuration. Bind the actual flags and startup behavior instead of importing an ambient site merely to find pip.

All destinations must be outside Git and shared runtimes, task-owned and absent before use. Bind their ancestors and fresh output paths. No overwrite, deletion, in-place repair or forced rename is authorized. Preserve partial state and reconcile an uncertain outcome before a later attempt. Installed directories are not committed or included as runtime trees in source archives; retain exact artifact identities and reproduction evidence. [S6]

The post-install reader should expose the limits of its result: all seven exact names/versions and metadata/file identities are static evidence. Native files may be hashed as data. Their presence does not establish compatible loading or scientific behavior. Python startup hooks, `.pth` files and unexpected extra distributions must be disclosed; executing them is not part of this review.

P03 recorded a task-specific CPython 3.12.14/Linux x86-64 environment with all seven pins. This is historical feasibility evidence only. It establishes neither a surviving environment nor current wheel availability. [S8]

## Source support and read coverage

Exact source snapshots and SHA-256/size records are in `READSET.json` and `sources/`. Both 344-line C271 task records were fully read. Source and contract coverage below is deliberately limited to the preparation boundary; no full H0 source audit is claimed.

- **S1:** `docs/engineering/localized-repair-c271/actual-input-p19/PHASE-OUTCOME.json`; its retained observation plan and operational review.
- **S2:** `docs/engineering/localized-repair-c271/host-inspection-p07/HOST-INSPECTION-DESIGN.md`, sections 1–4, with `ADOPTION.json`; `QUALIFICATION-PLAN.md`, sections 1–3.
- **S3:** `prototypes/static_tray_v01/current_host_readback_v01.py`, `_python_pins` and relevant `_verify_host` body; `current_host_inspection_v01.py`, `_check_author_runtime`, `_check_author_host_bindings`, `_check_metadata`.
- **S4:** `docs/engineering/localized-repair-c271/loader-path-p11/design/candidate004/DECISION.md`, with P11 `ADOPTION.json`.
- **S5:** `tools/native-reader-verification-linux-cp312.lock` (SHA-256 `a7f17491000c2e139ccc5d213ca0e8a6f917e5befb4b878fef29f5ff72ae780f`).
- **S6:** `docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md`, sections 1–5, with `ADOPTION.md/json`.
- **S7:** P07 `QUALIFICATION-PLAN.md`, H0–R stage boundaries.
- **S8:** `docs/engineering/localized-repair-c271/validation-recovery-20261120/PHASE-OUTCOME.json`, `python_pins` record.

No installer, product/probe/checker, recovered script, seven-package import, Node, ldd, direct-loader or native/model operation was executed by this reviewer. The only writes are this owned review directory. Source revision and clean-checkout facts are Director-supplied; this worker made no Git or remote calls.
