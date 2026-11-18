# Surviving workspace reconciliation

Read-only inspection on 2026-11-18. The coordinating agent supplied live GitHub main `7818de1f17e379df50680cb94347ce86bcabb8a5`. This audit did not contact or mutate GitHub, alter either old checkout, or run product tests. `AGENTS.md` in both checkouts was read before inspection.

## Current surviving checkout

`/workspace/scratch/b4cbf4ea8454/OntoKin`

- Local `main` and `HEAD`: `7818de1f17e379df50680cb94347ce86bcabb8a5`.
- Tree: `4c916307ffd26f4bc17435d3a73cbdbc5a50301e`.
- Tracked state clean; no nonignored untracked files. Thirteen ignored files are Python bytecode caches.
- One worktree, the checkout above. Local C264 work branch remains at `82c998eb17a12cc0dfa04bad45fe728e82764704`; its history is included in current main. No other-ref commits are absent from current main.
- Local remote-tracking refs are stale: `origin/main` still points to `bbe30e2f5863d743bd2393466341511b4924ad9d`; `origin/HEAD` and a C264 remote-tracking branch point to `82c998eb17a12cc0dfa04bad45fe728e82764704`; a C263 tracking branch points to `727cc298cd9862f53684061a34e9e41a8ec8cd06`. They are historical local observations, not evidence that these branches exist remotely now.
- This is a shallow repository. A reachable-object scan from current main found 15,421 objects, no missing objects, and no object-store alternates. It is suitable as a seed for current development, but does not establish complete historical graph retention.
- All eight distinct commits in this checkout's reflogs are ancestors of current main.

## Older surviving checkout

`/workspace/scratch/c3681d8a01ea/OntoKin`

- `HEAD` is the C264 branch `work/c264-required-browser-handoffs` at `82c998eb17a12cc0dfa04bad45fe728e82764704`.
- Tracked state clean; no nonignored untracked files; one worktree.
- Current main commit `7818de1f17e379df50680cb94347ce86bcabb8a5` is absent from its object store.
- Local `main` is `bbe30e2f5863d743bd2393466341511b4924ad9d`; C263 and C264 local branches survive. Use the newer checkout as the seed.
- All ten distinct commits in the older checkout's reflogs are available in the newer checkout and are ancestors of current main.

## Safe continuation

Create a new isolated checkout by cloning the newer local repository with `--no-hardlinks`, retain its shallow boundary, and explicitly select the observed main SHA. A local clone copies objects without changing the source checkout. Verify the resulting `HEAD` and tree against the GitHub-pinned values before editing. Do not infer remote branch state from copied tracking refs. No unpublished code was identified inside either inspected checkout; session files elsewhere were outside this audit's scope.

## Actual execution capability

- Terminal commands and local Git reads succeeded.
- Runtime: Linux 6.18.57 x86-64, glibc 2.41.
- Primary interpreter: `/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3`, CPython 3.12.14. `python3.12` resolves in the same runtime.
- Additional interpreter: `/usr/bin/python3.13`, CPython 3.13.5.
- Python 3.11 was not found on PATH.
- No product test, native application, external model, or hosted workflow was executed by this inspection.

## Inspection commands

With `GIT_OPTIONAL_LOCKS=0`, read-only `git rev-parse HEAD`, `git status --porcelain=v1 --untracked-files=all`, `git for-each-ref`, `git worktree list --porcelain`, `git cat-file -t`, `git log`, `git rev-parse --is-shallow-repository`, `git rev-list --objects --missing=print`, and `git ls-files --others --ignored --exclude-standard`. Python versions were queried with `--version`.
