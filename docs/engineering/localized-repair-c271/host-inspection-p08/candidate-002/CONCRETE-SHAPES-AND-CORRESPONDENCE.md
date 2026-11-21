# P08 implementation detail and existing-contract correspondence

This note describes the new authoring module only. It does not authorize an operational plan, observations, preparation, qualification, the original seven methods, or the full routine. C271 and its parent obligations remain open.

## Concrete shapes within the accepted P07 design

The module docstring is the normative concrete nested-shape index for this candidate. All selected JSON plans/documents are bounded and canonical, and their objects have closed keys. The public plan retains the accepted P07 top-level fields. There is no embedded expected digest or approval field.

Each command's `supervisor_outcome` is exactly `{raw, committed}`. `raw` is derived as `cwd/LABEL.process.json` and belongs to the unchanged supervisor. `committed` is a different predeclared atomic wrapper receipt. Both occur in the path inventory. Raw bytes are retained unchanged even when malformed or inconsistent; the wrapper does not repair them.

The installation index is `{schema, plan, report}`, with schema `ontokin.current-host-readback-inspection-installation/0.1.0`. The index binds the existing preparer's selected plan and actual report by descriptor. It adds provenance without modifying the original installation report or executing installation. A plan/report pair must agree on source, purpose, destination, selected archive, member/file/directory inventory and exact final tree.

Author runtime metadata is the accepted `{schema, executable, interpreter, files, aliases, startup_files, extension_files, loader_inputs, environment}` shape. The executable descriptor must equal its actual runtime file binding. Every runtime alias and canonical file binding must also appear in HOST. Startup files, native extensions and the author interpreter use `inspector_runtime`, except an interpreter already represented by the separate common ELF interpreter role. Loader input files use the loader or inspector runtime role as appropriate. This does not audit unrelated installed package bytes.

The caller-owned outer capture is `{authority, log}`. Authority is immutable. The existing log descriptor binds an initial prefix of at most 16 MiB; the same private regular inode may append up to 64 MiB total. Prefix bytes, file mode, link count and guarded inode/ancestors stay fixed. Validation reads only the prefix, checks sizes and the current deadline, and never obtains execution approval from appended content. The module writes neither file.

## Preserving existing installation/dependency predicates with bounded traversal

The protected P06 provider and preparer files remain unchanged. The new module uses checked streamed directory traversal for its own static input checks so it does not inherit an unbounded `os.walk` enumeration.

| Existing predicate | New authoring correspondence |
| --- | --- |
| Preparer `_plan_shape` closed source/purpose/archive/destination/report/file/directory/member schema | `_check_installation` calls the authenticated existing `_plan_shape` before using the bound plan. |
| Actual report state and source/purpose/destination relation | `_check_installation` requires actual successful `INSTALLED_EXACT` or `ALREADY_PRESENT_EXACT`, exact report keys, zero Node/ldd/checker counts, matching source/purpose/report path and exact selected destination. |
| Exact selected Node file, archive and `SOURCE.json` provenance | The same selected version, digest, size, executable mode, archive digest/size and preparer file map are required. |
| Provider `_tree_state` complete file and directory inventories | `_check_installed_tree` compares every traversed relative file/directory with the exact supplied sets; missing or extra files/directories refuse. The traversal has the existing 2,048-entry allowance and checks the deadline per entry. |
| Necessary parent directory set and directory modes | The exact necessary parent set is reconstructed from the selected filenames and every directory mode is checked. |
| File SHA-256, size and mode | Every selected file goes through the same strict bounded descriptor/file check; hardlinks and symlink components remain refused. |
| P06 immutable historical dependency inventory | `_check_runtime_dependencies` obtains the authenticated provider's unchanged `dependency_inventory`; selected paths and digest/size pairs must match all 24 historical files. |
| P06 retained archive pin and actual archive bytes | The authenticated provider's unchanged archive digest is required and the selected archive descriptor is checked against bytes. |
| Exact dependency versions | `validator/package/package.json` must report `2.0.0-dev.3.10`, and `indexer-view/three/package.json` must report `0.186.1`, using the existing bounded provider read. |
| Seven Python package versions | Actual selected metadata files are read without adding site directories or executing startup/package code. All seven names and versions must equal the unchanged lock. |

Focused controls preserve missing/extra/file-mode/directory-mode/tree bounds and the historical 24-file cardinality. Literal assertions separately bind the production source tree/file sets, fixed limits, selected Node/archive identity, environment and seven package versions. None of these controls run Node or ldd.

## Reconciliation and uncertainty

Reconciliation makes no write, fsync, process call, signal, retry, relaunch or approval. It verifies the selected plan relation and complete retained graph: reservation directories; preflight source/boot relation; command intent; actual callback; raw and committed supervisor outcome; inspection; final command sidecar; HOST; result; and exact two-item completion list. Descriptor paths must be the predeclared paths, not alternate content-equivalent files. Both files and directories must match the closed completed package inventory.

An outcome-only PID becomes positive count evidence only when its complete fixed-command receipt and actual raw receipt relationship validate. A PID-shaped object by itself cannot establish a start. Incomplete or inconsistent evidence remains unresolved.

`OBSERVED_UNAPPROVED_AS_RECORDED` describes the retained graph and content only. It does not prove that a previous completion-marker directory fsync succeeded. Every read-only reconciliation reports `durability_state: UNKNOWN` and `evidence_finalized: false`, together with `approved: false` and `relaunch_permitted: false`. A caller-owned appended log cannot upgrade those values.

For a multi-callback contract violation, the separate failure details preserve every ordered callback, an exact observed distinct-start count and lower bound, and the original final process receipt. Ordinary success/count projection is unavailable. Aggregate total completeness can remain unknown while the exact known observed count remains explicit. A later drift or persistence failure retains the anomaly and original supervisor exception/receipt.

## Run preservation and mock boundary

The logical fixture recipes and mutation selectors are frozen by exact source hashes. Actual temporary roots, filesystem inode/time identities, UUID publication names and ordinary UTC samples vary by run. A run uses a new absolute `ONTOKIN_HI_RETAIN_ROOT`; the test harness retains all generated fixture trees and records actual per-file identities and hashes. The source snapshots, command, selected environment, complete stdout/stderr and result JSON are retained before any revision.

`run_focused_guarded.py` installs process guards before importing the candidate or project helpers. It permits only the new focused test module or its exact named tests. Calling the script itself requires the separate candidate/mapping execution gate to be satisfied. It has not been executed while this note is prepared.
