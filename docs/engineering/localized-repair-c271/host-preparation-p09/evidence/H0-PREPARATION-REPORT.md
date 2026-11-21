# H0 preparation: selected Python is outside the admitted ELF layout

H0 stopped at a concrete static prerequisite. The existing selected Python image has a dynamic string table that spans two adjacent load segments. The accepted inspection implementation requires the entire table to fit within one load segment. No operational installation plan, installation, executable inspection plan or H1 approval was produced.

## Exact input and source

The selected `python3` was both the existing task-PATH executable and `CODEX_PRIMARY_RUNTIME_PYTHON`. It resolves to `/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12`: 30,894,944 bytes, SHA-256 `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`, mode `0o755`. `selected-python.bin` retains those exact bytes with nonexecutable evidence mode `0o600`. No alternative interpreter was searched or selected.

The Director confirmed detached source `h0_source` at commit `2c6bbfb7aa1d402ce47ffdc24adb4d89b8a81c1e`, tree `03f8751715eb2196f8d56f12868cc572d3392dd8`. Its accepted `current_host_inspection_v01.py` is 147,900 bytes, SHA-256 `b2f4c869fd03919047db797bd3a80616cbe16f6b17689fe61d40754b27f97a39`. This worker read and hashed the source; the Director owns Git identity verification.

## Why the current parser cannot accept it

ELF is the executable-file format. `PT_LOAD` identifies a mapped segment; `DT_STRTAB` and `DT_STRSZ` identify the dynamic string table's address and byte length.

| Raw field | Observed value |
| --- | ---: |
| `DT_STRTAB` | 4,191,704 |
| `DT_STRSZ` | 42,266 |
| String-table end, exclusive | 4,233,970 |
| First load-segment range | [4,190,208, 4,194,304) |
| Second load-segment range | [4,194,304, 4,328,816) |
| Load segments containing the whole table | 0 |

`read_elf_metadata` lines 701–705 selects only segments satisfying `virtual <= straddr` and `straddr + strsize <= virtual + size`, then requires one unique mapping. For these exact bytes the mapping list is empty. Its declared refusal is `CHI-UNSUPPORTED: Ambiguous/unmapped ELF string table`. `_check_author_runtime` calls this parser for the actual selected Python image at lines 1194–1195, before operational inspection can proceed. This is a source-backed static incompatibility, not an observed product exception. It does not establish that the executable is corrupt or that its runtime behavior fails.

## Preserved attempts

Attempt001 was an independent, standard-library-only file reader. It raised `AssertionError` at the full-range mapping calculation and exited 1. Its source, empty stdout and complete stderr remain unchanged. It created no JSON result or image snapshot. The initial interpretation was an inspection-script failure; the next diagnostic established why that predicate was unsatisfied.

Attempt002 independently retained the image's raw program headers and dynamic entries, copied the exact image bytes, and exited 0. It does not relax or execute the accepted parser. `PYTHON-ELF-DIAGNOSTIC-002.json` records the observations. Both helpers were launched once with the existing selected Python and `-I -S -B`; neither imports project code or contains subprocess calls. No runtime/preparer command was attempted or left unresolved.

The shell passed its existing environment to those file-inspection helpers. A complete environment snapshot was not captured before launch, and these evidence-only calls do not claim the five-variable operational launcher contract was satisfied. The absolute interpreter, arguments, cwd and output destinations are preserved in `OPERATIONS.json`. This limit does not alter the raw file/header finding; it does prevent treating these helpers as operational inspection-plan validation.

## Completed and remaining work

The independent reviewer reported complete frozen inventories for the exact P05 Node archive and C195 archive, with no findings: two Node members and 730 C195 members. Only 24 C195 files are the retained dependency targets; every archive member still requires authentication. The inventory files and their hashes are referenced in `H0-STATIC-BLOCKER-001.json`.

After the Director confirmed the early recovery save, this worker created only `h0_work` evidence. The first concrete prerequisite blocker stopped further preparation. There were zero product imports, accepted-parser calls, preparer calls, runtime installations, Node/ldd starts, checker starts, original-method runs or full-routine runs by this worker. Python metadata, transitive closure, ldd/Git/loader bindings, install plans/receipts and an exact executable inspection plan remain unprepared. Existing source, tests, contracts, pins and historical evidence were not changed.

Independent blocker review and the Director's partial delivery are the remaining actions for this phase. A possible fresh phase is a bounded review of finite string-table mapping across adjacent ELF load segments, with strict bounds and refusal behavior retained. This report does not authorize or implement that change.
