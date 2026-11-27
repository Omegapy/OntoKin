# W1 notes: inputs, starts and limits

Worker W1 of C271-P36, gate MR, stage S2. This was a read-only assignment from Director
`c271-p36-14f7f8b219db`. I worked in a fresh context, with no earlier project history.

## What I read

The candidate is `d3b622d61745259c3477bc94be0fb4da05c23c56`. I read it from the branch ref file and
from the worktree's `HEAD` file; no Git command ran. Every file is labelled as in the report.

- **The governing files:**
  - `AGENTS.md`, `ROLE.md`, sections 4 and 5 of `docs/workflow/PROTOCOL.md`, and
    `docs/workflow/templates/WORKER.md`;
  - the MR plan and `PHASE.json`;
  - sections 4 to 9 of the adopted contract;
  - MI's `OUTCOME.json`, especially `for_later_gates`, and D-18 to D-21 of `DIRECTOR-DECISIONS.md`;
  - MH's portable `host/observe-001/HOST.json`, `python-inventory-001.json`, `observe-001.environment.json`
    and the command record.
- **The code:**
  - `tools/check_local.py` in full, with `tools/storage_identity.py`, `tools/doctor_local.py` and
    `tools/bootstrap_local.py`;
  - the six step entry points and their conformance modules;
  - the 0.2.0 provider, the facade, the observer, both supervisors and `format_check`;
  - every test module with a start site, and every library function those tests call.
- **The framework's standard library,** for `platform.py` (when it starts `uname` and `file`),
  `sitecustomize.py`, `venv` and `ensurepip`.
- **Main's baseline records** under `<local>/checks/main-8e847c15-*` (read only). I read the resolved-run
  summary and searched both baseline workspaces for bytecode: there is none.
- **The Director's** `workers/WORKERS.md` and `director/run/run_once_p36.sh`, read as data.

`raw/read-files.sha256.txt` holds the SHA-256 of 59 key files. Among them:

| File | SHA-256 |
| --- | --- |
| `docs/engineering/localized-repair-c271/macos-routine-p36/MR-PLAN.md` | `0e78bf60234e5f21bda17bb9b75cd1c0a111f676197b1a7d7b86f82ec34f706e` |
| `docs/engineering/localized-repair-c271/macos-routine-p36/PHASE.json` | `042cc9bfc8e97650a156c9a61b5a2ca3e2c4676483a6a0a883ec35f80b52cfb5` |
| `docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md` | `42db98dc6099ee605b0963f3734f7bff2d68c019ff6c00a0ee97bd753c03fdc9` |
| `tools/check_local.py` | `4c55033d51bdd33700f6d8a847b3ed44e6b4f7f6489bf11b5f497279a5a4cb70` |
| `tools/doctor_local.py` | `acf4947bd6d753ddb0a305f551fe93553c5bb43c7f094f22f287d30f9dc9e24b` |
| `prototypes/static_tray_v01/current_host_readback_v02.py` | `d34ea2f98cf77188750b7819f0b5418d4811d0bfcd8612fdd71be58210f59071` |
| `prototypes/static_tray_v01/supervisor_darwin_v01.py` | `bd4a5e3fcdfb5367994bfeeb93d211dd627b830017b17f607cd94d71ade2bd2b` |
| `tests/test_static_tray_readback_v01.py` | `6295e0442ba7e7a1d1236fb5d9148e97ed92cc4db3e77dcd7b2993af5ef0f662` |
| `tests/test_local_checks.py` | `ce58b59ef72364266ee2919c48f2f9c12eefc946e65afd79f07dc42ab8aad9d5` |
| `tests/test_doctor_local.py` | `d7de67e3588d3034085088d5353db53dec992aec4db1ddc7cc176dfbcd9bba88` |
| `tests/test_bootstrap_local.py` | `148a4ed514a2e03b010ef4ce21e72aabbb86e1859e0b7ac23022c2a00f0eee34` |
| `<framework>/lib/python3.12/platform.py` | `f5ff83f15c841792be42709a6710dc8d7a9f72791c1ae4cad719b1fb0abe0a05` |
| `<framework>/lib/python3.12/sitecustomize.py` | `5ff5a6f63e9a711957ed3dc09ac44010adc8baa1c79e76ce1d3ba08f9d8f8c46` |

## What I started

| Program | Count | Purpose |
| --- | ---: | --- |
| `zsh`, the tool's shell, one per command | about 100 | to run the commands below |
| `python3 -I -S -B`, the framework interpreter on `PATH` | about 55 | my scripts and `-c` or stdin one-liners that read files |
| `ls`, `cat`, `sed`, `grep`, `wc`, `find`, `head`, `tail`, `cut`, `sort`, `uniq`, `awk`, `tr`, `mkdir`, `shasum` | many | listing and reading |
| `stat` | about 470 | most of them through `find -exec`, for bytecode dates |
| `rm` | 3 | only on my own files: one scan output before a rescan, and `START-INVENTORY.json` twice before regenerating it |

- Every `python3` start carried `-I -S -B`.
- One `python3` run, the first import-graph build, was too slow. I stopped it after two minutes through
  the tool's task stop; it had written nothing.
- **I started none of these:** Git, Node, `ldd`, `codesign`, `otool`, the observer, `tools/check_local.py`,
  `doctor_local.py`, `bootstrap_local.py`, or any unit test.
- **I wrote nothing** outside `<local>/c271-p36/workers/W1-inventory/`. The worktree, the prepared trees
  and the evidence were not opened in Finder.
- **A self-check after the work:** `<framework>` still holds 414 `.pyc` files in 37 `__pycache__`
  directories, and none of them is newer than the worker log. The `.venv` holds 0 `.pyc`, and the
  worktree holds no `__pycache__`.

## My scripts (in `scripts/`)

| Script | What it does |
| --- | --- |
| `scan_starts.py` | AST scan of start, lookup, `ctypes`, environment and patch sites (outputs `raw/scan-code.json` and `raw/scan-extra.json`) |
| `import_graph.py` | the static repository import closure of each test module and each step entry point (`raw/import-graph.json`) |
| `module_level_calls.py` | the calls made at import time by each test module (`raw/module-level-calls.json`) |
| `pyc_presence.py` | cached-bytecode presence and header freshness for every `.py` of a tree (`raw/pyc-framework-stdlib.json`) |
| `stdlib_closure.py` | an over-approximating standard-library closure that follows every import, function bodies included (`raw/stdlib-closures.json`) |
| `stdlib_closure_toplevel.py` | the module-level closure that the report uses (`raw/stdlib-closures-toplevel.json`) |
| `build_inventory_json.py` | writes `START-INVENTORY.json` from the established entries |

`raw/step-required-tests.json` lists the tests that the construction, surface and impulse steps run in
process. I took it from their manifests.

**Three notes for a portable copy.**
- Both raw scans first held the string literals of the scanned code that look like program names or
  absolute paths. Some of those name other software or the package manager. I removed them, and only
  their counts remain.
- `scan_starts.py`'s search-term list names generic macOS developer-tool commands such as `xcrun`. If a
  public copy must name none, drop that list from the copy.
- `raw/read-files.sha256.txt` uses the `<framework>` label for the files outside the worktree.

## Limits

- **Static only.** These are not established:
  - run-time import tracing;
  - computed imports;
  - Git's own child processes;
  - exact Git counts per test.
- **The closure model.** The standard-library closures follow module-level code and class bodies, and
  resolve Windows branches as on macOS. I reviewed function-level imports only on the executed paths;
  they are cached too, except AIX-only `_aix_support` and `ensurepip/_uninstall`.
- **The framework's bytecode census** is a reading of 2026-11-27. M0 observes the trees again.
- **`PATH`.** I did not locate the other Node.js installation. I checked only whether `/usr/bin/node` and
  `/bin/node` exist, and neither does. For `git-lfs` and `python3.12`, I checked `/usr/bin` and `/bin`,
  and `git-lfs` also in the bound Git's exec path; none is there. Starts by name under another `PATH`
  are stated as conditional.
