# Local development setup

How to prepare, check and repair OntoKin's development environment on a local
machine. Sessions start from [LOCAL-START-HERE](../../LOCAL-START-HERE.md); this
guide holds the detail. Validation policy is
[OK-ENG-006](../engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md).

Run every command from the top of the checkout or worktree it should act on.

## Prepare the normal environment

```sh
python3.12 tools/bootstrap_local.py --preview
python3.12 tools/bootstrap_local.py
.venv/bin/python tools/doctor_local.py
```

The first command shows what would change and changes nothing. The second creates
`.venv` and installs the `python-verification` profile from the platform's reviewed
lock, with hash enforcement and binary wheels only. A repeat run on a healthy
environment changes nothing. The third reports readiness by profile; exit status 0
means that the selected profile is ready.

Afterwards run project commands through the environment's own interpreter. No
activation is needed, and the `python3` that is first on `PATH` does not matter:

```sh
.venv/bin/python -m ontokin capabilities
.venv/bin/python -m ontokin check docs/language-design/core-v0.1/01-independent-parts.ok
```

## What is committed and what stays local

| Kind | Place |
| --- | --- |
| Interpreter patch, profiles, lock for each platform | [tools/local-environment.json](../../tools/local-environment.json), committed |
| Package pins and locks | [six Agent pins](../../tools/force-agent-verification-requirements.txt), [Linux x86-64 lock](../../tools/native-reader-verification-linux-cp312.lock), [macOS arm64 lock](../../tools/native-reader-verification-macos-arm64-cp312.lock) with its [provenance](../../tools/native-reader-verification-macos-arm64-cp312.provenance.json), committed |
| Environment and its record | `.venv/` and `.venv/ontokin-environment.json`, ignored: exact interpreter, distribution, platform, tools, packages, lock digests and actions |
| Reports of setup runs that changed something | `build/local-environment/`, ignored |
| Worktrees and driver output | Directories beside the clone, outside every checkout |
| Worktrees that the Claude application creates, machine-specific Claude settings | `.claude/worktrees/` and `.claude/settings.local.json`, ignored by `.claude/.gitignore` |

Environments, caches and dependency directories are recreated from the committed
files. They are never committed, archived or copied to another location. The root
`.gitignore` stays byte-identical because the documentation verifier checks it.

## Profiles

Readiness is reported separately for each profile as `ready`, `missing`, `mismatch`,
`unsupported` or `not_checked`. A ready profile says that its tools are present. It is
not task completion, native acceptance or product qualification, and `core` alone is
not enough for the complete test suite.

| Profile | Contents | Established by |
| --- | --- | --- |
| `core` | CPython 3.12.13 in `.venv`, the standard library, Git, optional editable install | Exact implementation, version and distribution; an isolated environment created at this location; a Git checkout; the source package imports |
| `python-verification` | `core`, the six Agent pins and Pillow 13.0.0 | A lock valid for this platform and equal to the pins; exact versions; imports; `pip check`; `tools/check_native_reader_setup.py` |
| `visual-verification` | `python-verification`, Node.js 22 and npm, the npm dependencies of `tools/package-lock.json`, Playwright's Chromium headless shell | Node.js major version; npm; exact dependency versions; the browser revision that the installed Playwright expects |
| `package-smoke` | A clean build environment and a separate clean installation environment | Running the procedure below. The doctor never reports it ready |
| `historical-native` | Whatever the owning experiment's contract names | That contract only. General setup neither prepares nor accepts it |
| `linux-container` | Nothing is configured | A later, separately adopted profile |

Select a profile with `--profile`. The default is `python-verification`. The optional
editable install of `core` proves nothing about the installed package.

## Check an environment

```sh
.venv/bin/python tools/doctor_local.py --json
.venv/bin/python tools/doctor_local.py --output NEW_FILE --portable-paths
.venv/bin/python tools/doctor_local.py --online
.venv/bin/python -m pip check
.venv/bin/python -I -B tools/check_native_reader_setup.py
```

The doctor changes nothing and runs on any Python 3.9 or later, with or without an
environment. `--output` writes the report to a new file; `--portable-paths` replaces
this machine's paths by labels so that a report can be published. Only `--online`
contacts the remote, with `git ls-remote`; it fetches nothing.

## Run the checks

```sh
.venv/bin/python tools/check_local.py --list
.venv/bin/python tools/check_local.py --timeout 14400 --output-dir ../OntoKin-local/checks/NEW_NAME
```

Write driver output **outside the checkout**. The driver retains an isolated copy of
the source, and the documentation verifier scans every non-dot directory of a
checkout, including `build/`. Output left under `build/` would be read as project
documentation. The output directory must be new or empty.

`--timeout` limits each command, not the whole run, and defaults to 900 seconds. The
complete unit suite can need longer, so state it. A timeout is reported as a timeout.
Use no outer shell `timeout`; macOS does not provide that command.

## Work in a second worktree

```sh
git worktree add --no-track -b work/NAME ../OntoKin-worktrees/NAME origin/main
```

Then run the setup commands above in the new directory. Each worktree has its own
`.venv`, created there. Never copy or link one from another worktree: the doctor
reports a copied, moved or shared environment as a mismatch. Two agents never install
into the same environment; a second setup run for the same checkout stops at once. In
the Claude desktop application, turn Worktree mode on deliberately before parallel
editing, and verify the actual checkout path and branch before the first edit.

## Prove the installed package

This is the `package-smoke` profile. It uses new directories outside the checkout.

```sh
python3.12 tools/bootstrap_local.py --profile package-smoke --work-dir ../OntoKin-local/package-smoke/NEW_NAME
```

With `W` as that directory, extract an identified revision, build its wheel in
`build-env`, install only that wheel in `install-env`, and run it from an empty
directory with an absolute input path and nothing of the checkout on the path:

```sh
mkdir W/source W/dist W/run
git archive --format=tar REVISION | tar -x -C W/source
W/build-env/bin/python -I -m pip --isolated install --only-binary=:all: --no-input 'setuptools>=77'
W/build-env/bin/python -I -m pip --isolated wheel --no-build-isolation --no-deps --no-input --no-cache-dir --wheel-dir W/dist W/source
W/install-env/bin/python -I -m pip --isolated install --no-index --no-deps --no-input W/dist/ontokin_reference-0.4.0-py3-none-any.whl
cd W/run
env -i HOME="$HOME" PATH=/usr/bin:/bin W/install-env/bin/ontokin check /ABSOLUTE/PATH/01-independent-parts.ok
```

Record the revision, the build-tool versions, the wheel's size and SHA-256, and the
import locations. `setuptools>=77` is a lower bound, so the version actually used
belongs in the record. Set `SOURCE_DATE_EPOCH` to the commit time to rebuild the same
bytes. The [recorded run](../engineering/local-migration-20261124/PACKAGE-SMOKE.json)
shows all of this. A build failure is a separate packaging fix.

## Visual verification

Prepare this profile only for exporter or viewer work, or for `--full` checks. The
target is **Node.js 22**; other major versions are a mismatch, although the driver's
own preflight accepts Node.js 18 or later. The committed versions are esbuild 0.25.10,
gltf-validator 2.0.0-dev.3.10, Playwright 1.56.1 and Three.js 0.180.0.

```sh
python3.12 tools/bootstrap_local.py --profile visual-verification --preview
python3.12 tools/bootstrap_local.py --profile visual-verification
```

The setup tool does not install Node.js. Install Node.js 22 with the machine's existing
mechanism and, when it is not first on `PATH`, pass it with `--node`. The tool then runs
two separate steps, which can also be run by hand:

```sh
npm ci --prefix tools --ignore-scripts
node tools/node_modules/playwright/cli.js install chromium --only-shell
```

`npm ci` **replaces** an existing `tools/node_modules`. Use it only for first
preparation or deliberate repair, and only when no validator or other agent uses that
directory. The setup tool compares the installed versions first, leaves healthy
dependencies alone, and replaces differing ones only with `--repair-node` and only when
no process uses them. System libraries for a Linux browser are a separate step on
Linux; the commands above add none on macOS.

## Native by default, no container

The native environment is the default for all ordinary editing and for the tests the
host supports. Work does not wait for Docker, and no Docker, Compose or Kubernetes
configuration is committed. Reasons: the reference runs on the Python standard
library; the verification packages have reviewed wheels for macOS arm64 and Linux
x86-64; a persistent checkout with a local environment is simpler to inspect and
repair; and Docker is not installed on the owner's machine.

A later Linux or container profile must state its purpose and carry its own
acceptance, with architecture, emulation, kernel, graphics and timing explicit in its
evidence. An emulated amd64 container on an Apple silicon Mac is never native Linux
qualification. Likewise, a historical profile that binds an exact interpreter, such as
Linux x86-64 CPython 3.12.14, is reproduced only in its own environment; a newer
interpreter never inherits its qualification.

## Troubleshooting

The doctor prints the next exact setup action. The common cases:

| Report | Meaning | Action |
| --- | --- | --- |
| `interpreter: missing` | No environment in this checkout | Run the setup tool |
| `interpreter-missing` from the setup tool | CPython 3.12 is not on the machine | Install it with the existing mechanism, on macOS `brew install python@3.12`, or allow that with `--install-interpreter` |
| `interpreter-mismatch`, or `interpreter: mismatch` | Another patch, implementation or distribution than the specification names. Homebrew can upgrade the patch under an existing environment | Provide the exact interpreter, or adopt another patch through a reviewed change of the specification. Then rebuild explicitly |
| `isolation: mismatch` | The environment was copied, moved, linked or opened to system packages | Review it, then `python3.12 tools/bootstrap_local.py --rebuild` |
| `packages: missing` or `mismatch` | Absent or wrong versions | Run the setup tool; it replaces only those packages |
| `lock: unsupported` | No reviewed lock for this platform or Python series | Report the platform. Never install from another platform's lock or without hashes |
| `lock: mismatch` | A lock, its provenance or a pin was changed | Restore it, or adopt a reviewed change |
| `.venv is in use by process N` | A running process uses the environment | Let it finish; the tool never replaces a used environment |
| Another setup run is changing this checkout | Two setup runs at once | Wait for the first |

Without network access, install from a directory that holds the locked wheels:

```sh
python3.12 tools/bootstrap_local.py --find-links DIRECTORY
```

## Commands run for this guide

Executed on macOS 26.6.2, arm64, with Homebrew CPython 3.12.13, on November 25, 2026.

| Commands | State |
| --- | --- |
| Setup preview, setup, repeat setup, doctor in every form above, `pip check`, native-reader preflight, `capabilities`, `check` | Run |
| `--find-links`, refusal of an incompatible environment, refusal while a process uses it, `--rebuild` | Run in scratch worktrees |
| Driver list and the routine driver with `--timeout` and `--output-dir` | Run |
| `git worktree add` and setup in the new worktree | Run; the migration worktree was made this way |
| Package-smoke procedure | Run |
| `visual-verification` preview | Run; refused because only Node.js 25.9.0 is installed |
| `visual-verification` setup, `npm ci`, Chromium installation, `--repair-node`, `--install-interpreter` | **Not run** on this machine; covered by controlled tests only |
| Everything on Linux x86-64 | **Not run** here |
