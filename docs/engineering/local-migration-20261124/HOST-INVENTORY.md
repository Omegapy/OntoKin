# Host and clone inventory

Taken at 2026-11-24T23:44:19-07:00 (2026-11-25T06:44:19Z), before the migration
changed anything, for REQ-001 and REQ-034 of
[TRD-20261124-E65C6113](../../../TRDs/trd_ontokin-local-development-migration_2026-11-24.md)
(TASK-001 of PLAN-20261125-CB551B16). Every value is a read-only observation of
one machine at that time. Setup decisions in this migration cite this record.

The repository is public. Credentials, the GitHub account name, the configured
author identity, the SSH host alias and absolute machine paths are left out on
purpose; they stay on the machine. "Not observed" means the item was looked for
or considered and no value was established.

## Clone and Git state

| Item | Observed value | Observation |
| --- | --- | --- |
| Clone root | One ordinary non-bare checkout named `OntoKin`, in the owner's project folder on the external volume; its absolute path is kept off this public record | `git rev-parse --show-toplevel` |
| Origin | SSH remote for `Omegapy/OntoKin` through a local SSH host alias that resolves to github.com port 22, for fetch and push | `git remote -v`; `ssh -G` |
| Branch | `main`, tracking `origin/main`; no other local branch; no tag | `git branch -vv`; `git tag` |
| Head | `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774`, tree `812a17de3880f7c152beacccf7b2e690381f9716` | `git rev-parse HEAD HEAD^{tree}` |
| Tracked modifications | None | `git status --porcelain=v2 --branch` |
| Untracked files | 12 files in two directories, listed below; no ignored file | `git ls-files --others --exclude-standard`; `git status --ignored` |
| Stashes | None | `git stash list` |
| Unpublished commits | None: no local branch commit is missing from the remote-tracking refs | `git log --branches --not --remotes` |
| Worktrees | One: the clone itself | `git worktree list --porcelain` |
| Hooks and filters | No active hook, no `core.hooksPath`, no submodule, no configured filter driver, no LFS-tracked file | `.git/hooks`; `git config`; `git lfs ls-files` |
| Case handling | `core.ignorecase=true` (case-insensitive APFS) | `git config --local --list` |
| Object store | 27,674 packed objects in one pack (564.43 MiB), 57 loose objects, no garbage; 18,646 tracked files | `git count-objects -vH`; `git ls-files` |
| Git locks | None | `find .git -maxdepth 2 -name '*.lock'` |

### Untracked files found

| Path | SHA-256 at inventory |
| --- | --- |
| `TRDs/trd_ontokin-local-development-migration_2026-11-24.md` | `12e905a76da826f52e61c1237977a836750ce89260e208ba8553ebc8aeb28d76` |
| `TRDs/INDEX.md` | `8d23c5333f77d46f4f0295211d4d3c5eea6a946f7dd5657e7f8e5acbd5e1d130` |
| `Implementation_Plans/INDEX.md` | Managed by the plan tracker; content changes as progress is recorded |
| `Implementation_Plans/Plan_ontokin-local-development-migration_2026-11-25_CB551B16/` | Nine tracker-managed files: `plan.json`, `PLAN.md`, `TRACEABILITY.md` and six files under `phases/` |

The TRD digest equals the approved revision 3 that the plan cites as SRC-002.

## Divergence from the remote

| Item | Observed value | Observation |
| --- | --- | --- |
| Live remote heads | `main` at `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774`; `work/c271-missing-import-digest-control` at `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`; no other head | `git ls-remote --heads origin` |
| Local main against `origin/main` | 0 ahead, 0 behind; `origin/main` equals the live remote head | `git rev-list --left-right --count` |
| C271 branch against `origin/main` | 89 ahead, 4 behind, merge base `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`; the remote-tracking ref equals the live head | `git rev-list --left-right --count`; `git merge-base` |
| Pending fetch | None | `git fetch --dry-run origin` |

## Local Git authentication

| Item | Observed value | Observation |
| --- | --- | --- |
| SSH read access | Works non-interactively; the read returned both remote heads with exit status 0 | `git ls-remote --heads origin` |
| SSH write access | Not observed; a read does not prove a push. It is observed when the migration branch is first published | None yet |
| GitHub CLI | Signed in to github.com through the system keyring; repository permissions reported as pull, push, maintain and admin | `gh auth status`; `gh api repos/Omegapy/OntoKin` |
| Repository settings | Public; default branch `main`; merged branches are deleted automatically | `gh api repos/Omegapy/OntoKin` |

## Operating system and hardware

| Item | Observed value | Observation |
| --- | --- | --- |
| Operating system | macOS 26.6.2, build 25G83; Darwin 25.6.0 | `sw_vers`; `uname -r` |
| Architecture | arm64 (Apple M3 Ultra, 28 logical cores, 96 GiB memory) | `uname -m`; `sysctl` |
| Build tools | Xcode Command Line Tools with Apple clang 21.0.0 | `xcode-select -p`; `clang --version` |

## Python installations

| Installation | Observed value | Observation |
| --- | --- | --- |
| Homebrew | CPython 3.12.13 (built 2026-03-03, Clang 17.0.0), the only Homebrew Python; `macosx-26.0-arm64`; bundled pip and ensurepip 26.0; OpenSSL 3.6.4; marked externally managed. It provides `python3.12` and is the first `python3` on the interactive PATH | `brew list --versions`; the interpreter's own `sys`, `platform` and `sysconfig` |
| uv-managed | CPython 3.12.11 and 3.11.14, with uv 0.10.7 | `uv python list --only-installed` |
| System | CPython 3.9.6 from the Command Line Tools | `/usr/bin/python3 -VV` |
| CPython 3.13 or 3.14 | Not found | `which -a`; `uv python list --only-installed` |
| pyenv, Conda, Mamba | Not found | `which` |
| Project environment | None: the clone has no `.venv` | `git status --ignored`; directory listing |

## Node installations

| Item | Observed value | Observation |
| --- | --- | --- |
| Node.js | 25.9.0 (Homebrew), the only installation found; no Node.js 22 | `which -a node`; `brew list --versions` |
| npm | 11.12.1 | `npm --version` |
| Version managers | nvm, fnm, Volta and nodenv not found | directory listing |
| Project npm dependencies | None: no `tools/node_modules` | `git status --ignored` |
| Playwright browser cache | Chromium and headless-shell revisions 1223, 1228 and 1234 from other work; whether any matches the pinned Playwright 1.56.1 is not observed here | directory listing |

## Applications

| Item | Observed value | Observation |
| --- | --- | --- |
| Git | 2.50.1 (Apple Git-155) | `git --version` |
| Git LFS | 3.7.1, below the 3.8.1 that [OK-ENG-010](../OK-ENG-010-git-lfs-archive-storage.md) requires only when LFS-selected files are present | `git lfs version` |
| GitHub CLI | 2.86.0 | `gh --version` |
| Claude Desktop | 6.28899.6, with a bundled Claude Code 2.1.330 for its Code tab | `Info.plist`; application support directory |
| Claude Code command line | 2.1.332 | `claude --version` |
| Other agent applications | ChatGPT 26.1120.41243, ChatGPT Classic, Codex 26.707.31123 | `Info.plist`; `/Applications` |
| Browsers and editors | Google Chrome, Visual Studio Code | `/Applications` |
| Docker, OrbStack, Podman, Colima | Not found | `which`; `/Applications`; Spotlight bundle search |
| Blender, Godot, Unreal | Not found | `which`; `/Applications`; Spotlight bundle search |

## Disk and backup

| Item | Observed value | Observation |
| --- | --- | --- |
| Clone volume | External fixed solid-state APFS volume, 3.6 TiB, 2.9 TiB free (22% used); not encrypted | `df`; `diskutil info` |
| System volume | 926 GiB, 611 GiB free | `df` |
| Clone size | 1.5 GiB, of which `.git` is 568 MiB | `du -sh` |
| Time Machine | No destination is configured, and the clone path is excluded | `tmutil destinationinfo`; `tmutil isexcluded` |
| Other sync or backup software | A OneDrive process is running; no OneDrive folder was found in the locations checked, so coverage of the clone is not observed. Backblaze, Arq, CrashPlan, Dropbox, Google Drive and Syncthing processes were not found | process list; directory listing |
| GitHub | Holds all committed and pushed content of both remote heads | `git ls-remote --heads origin` |
| ChatGPT Library | Not observed from this machine; repository records name it as the location of the legacy handoffs | [CURRENT](../../workflow/CURRENT.json) |

## Other activity at the time

| Item | Observed value | Observation |
| --- | --- | --- |
| Main integration lease | Released on 2026-11-20 by `c270-finalization-a2bb67238030`; no owner recorded | [STATUS](../../../STATUS.md#main-integration-lease) |
| Other agent sessions | One other Claude Desktop session has this checkout as its working directory and is idle; no process held a file open under `.git` | session listing; `lsof` |
| C271 | Pull request #274 is an open draft at the C271 head; issue #273 is open | `gh pr view 274`; `gh issue view 273` |
| Other open work on GitHub | No other open pull request; open issues #154 and #134 | `gh pr list`; `gh issue list` |
| R06 handoff and its receipt | Not found on this machine by name; the newest OntoKin handoff archives found are C271 P22 and P28 | Spotlight name search; Downloads listing |
