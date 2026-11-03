# Candidate03 inherited surface-agent failure: independent retained-state review

## Finding

The original surface-agent build failed, and its retained SQLite store is internally inconsistent. This review reproduced `SQLITE_CORRUPT` while opening only private byte-exact copies. The cause is **not established**. No original database was opened through SQLite, no repair or workload replay was performed, and no product, test, or inherited harness file was changed.

The complete original 34-role invocation remains failed. Its `surface-agent-build` role failed; the dependent format and browser roles were blocked. A separately approved fresh execution can add diagnostic and visual evidence without changing those outcomes.

## Exact retained evidence

The original tree is `c092-validation/candidate03-full-local/artifacts/surface-agent`. It contained **718 ordinary files totaling 9,946,854 bytes**. Every file was inventoried with its relative path, bytes, SHA-256, POSIX mode, device, inode, modification time and change time; directories were also inventoried. The complete tree and original log matched before and after both inspection passes and again at review closure. Access time was intentionally excluded because reading a file can update it.

The only observed database was `service-store/surface-program-agent.sqlite3`, **3,641,344 bytes**, mode `0644`, SHA-256:

`38bd71434609437073463cac4799266b128fa21d7ab5d6c6c6af933b507933d5`

There were no WAL, SHM or rollback-journal companions in the original tree at inventory time. This establishes their absence in the retained state; it says nothing about whether such files existed during the failed process.

A retained copy and a separate inspection copy were created and independently verified. Only the latter was opened, with SQLite URI `mode=ro&immutable=1` and connection-local `PRAGMA query_only=ON`. SQLite 3.53.1 was the actual inspection engine. The inspection copy remained byte/mode/stat-identical afterward. No journal checkpoint, recovery, VACUUM, REINDEX, write transaction, writable-schema operation, or source service import occurred.

The exact original 5,256-byte log is copied to `surface-agent-build.original.log`. Its SHA-256 is `bb83bfe4523984f958787a5458a7ab4b48022100a429a13d400ca627c2f044cd`.

## Failure and copied-state diagnostics

The log contains **15 retrieved fixture records**, ending with `held-out-3`. Request `surface-workflow-0283` for project `surface-workflow-held-out-4` invoked `surface.mesh_page` with count 7. Its request file exists and its response file is absent. The traceback reaches `AgentStore.request` while committing the task's terminal state, and the indexed `SELECT` raises `sqlite3.DatabaseError: database disk image is malformed`.

Both `quick_check(100)` and `integrity_check(100)` raise `SQLITE_CORRUPT` in the private copy. The identical failed lookup also raises it when explicitly forced to avoid the index. The initial `fetchall()` calls recorded the exceptions. A second streaming pass retained the diagnostic rows emitted before the terminal exception; it did not replace the original attempt.

The file and its header agree on **889 pages of 4,096 bytes**, with no partial trailing page. The whole-database `dbstat` scan reports the following corrupted references:

| Tree | Corrupted references |
| --- | ---: |
| `requests` | 25 |
| `sqlite_autoindex_requests_1` | 1 |
| `artifacts` | 1 |
| `sources` | 2 |
| **Total** | **29** |

Of these, **27 reference pages beyond the retained file**, through page **1063**. The other two are present pages **885 and 886**, for which the integrity diagnostic reports second references. Their actual page bytes and hashes are retained in `SQLITE-PAGE-DIAGNOSTICS.json`. The integrity scan also emits `wrong # of entries in index sqlite_autoindex_requests_1`. These observations establish that the retained page/reference state is inconsistent. They do not establish which write, process, storage layer or library caused it.

The request table's forward scan returns rows through sequence 242 and then fails. Some index-backed counts and selected metadata remain readable; successful partial queries are not evidence that the store is healthy.

## Source scope and attribution limits

The actual Candidate03 source pin is `68898e9b73efd20b37842897cbdfb2f61d4801ca`, tree `eb6ff3fbe4694866f11dae988def4c7b1498524b`. Six directly relevant source files were compared byte-for-byte across the C091 commit, Candidate03 commit, canonical working source and the actual executed verification workspace:

- `ontokin/agent.py`
- `ontokin/agent_store.py`
- `tools/build_surface_agent_demo.py`
- `tools/verify_surface_native.mjs`
- `tools/verify_surface_viewer.mjs`
- `tools/check_local.py`

All six match exactly; native blob IDs and SHA-256 bindings are in the JSON review. This narrows what changed in these files, without excluding effects elsewhere or establishing the failure's cause. The retained state contains no live WAL, filesystem trace or write-order trace sufficient to identify causation. No causal connection to historical C084/C085 occurrences is claimed.

## Scope of one separate recovery

One fresh execution of the unchanged three-role chain is a reasonable bounded diagnostic. It must use the original executables, source workspace, input bytes, environment construction, fixture list, process supervision and **3,600-second per-command limit**. Only output/report-root arguments may be relocated to a fresh absent private directory. The damaged store must not seed that directory. Build, format and browser prerequisites remain sequential, and a failed recovery role must not be retried or followed by its dependent role.

Every command, source binding, original-state comparison, log and generated output must be retained separately. Any recovery captures must be reviewed separately from the **23 captures produced in the original current invocation**. A successful recovery would not repair the failed store, identify its cause, turn the original full invocation into a pass, or clear the independent torque A08 blocker.

This document records the diagnostic scope review. The concrete wrapper's execution decision and its actual results, when available, are separate evidence.

## Evidence entry points

- `INDEPENDENT-REVIEW.json`: exact findings, original role records, source bindings and recovery scope.
- `ORIGINAL-BEFORE.json`, `ORIGINAL-AFTER.json`: complete original artifact inventory.
- `RESULT.json`: first copied-store inspection and preservation receipt.
- `SQLITE-READ-ONLY-DIAGNOSTICS.json`: initial query results and exceptions.
- `SQLITE-PAGE-DIAGNOSTICS.json`: streaming integrity messages, complete page observations and independent final preservation comparisons.
- `retained-store/`: unopened byte-exact retained database copy.
- `inspection-store/`: private copy actually opened read-only; unchanged afterward.
- `inspect_stores.py`, `inspect_pages.py`, `close_review.py`: exact executed review scripts.
