# C059 final evidence reuse and resulting-main verification

**State:** Source-reviewed method, not an execution result. No runtime/test command or remote mutation was performed to prepare this method.

## Decision boundary

The 34-step suite belongs to the exact candidate on which it actually ran. After final evidence publication and merge, reuse its applicable runtime results only after establishing complete eligible-input equality. Run the unchanged documentation checker on actual resulting main, and independently audit new or changed evidence records. Do not describe the full suite as freshly executed on main or claim its complete original source inventory is unchanged.

This follows OK-ENG-006 sections 2 and 4 and OK-ENG-009 section 3.6. It preserves every failed or pending release role and every environment limitation. If an applicable computational or verification input changes, rerun the affected checks; the exception process cannot make that change evidence-only by declaration.

## Why both a tree comparison and an inventory comparison are needed

`tools/check_local.py` inventories `ontokin`, `tests`, `tools`, `docs`, `examples`, `schemas`, `prototypes`, `.github`, and seven named root files, including STATUS. It includes untracked source files. Therefore final documentation/evidence publication normally changes its aggregate inventory digest.

Retain the actual `summary.json`, `source-before.json`, `source-after.json`, logs and reports without rewriting their candidate identities or source hashes. The driver's generated-example exclusions apply only to its isolated workspace comparison. They do not permit changes to original checkout examples or omission of those files from final equality.

Compare all tracked paths, modes and Git blobs, including paths outside the driver's inventory. Also compare the full actual inventory against the tested inventory; this catches untracked source inputs that a Git-tree comparison alone would miss. Both comparisons use the same closed exception list.

## 1. Bind the actual candidate evidence

Before reuse, establish all of the following from immutable records and the exact local Git objects:

- The suite summary identifies the actual tested commit/tree and interpreter/platform. Verify its source-inventory member hash and canonical inventory digest, member count and unique normalized paths.
- Original source-before and source-after inventories match exactly; the summary records source unchanged and Git revision unchanged. Keep each actual planned step, actual executed step, command, exit status and log/report identity. Verify the exact planned/executed identity set rather than counting 34 rows alone.
- The result claimed for each reused role matches its actual report. Preserve pending external cases and compatibility/visual limitations even when the driver process passed.
- The tested working tree is clean and has no omitted untracked source inputs. If it was dirty or included untracked inputs, explicitly bind those exact bytes to the actual tested manifest before using a commit as their identity. Do not equate a base HEAD with uncommitted tested bytes.
- Bind supplemental native/browser checks to their own commands, input artifacts, source identities and environments. Their artifact hashes must match the artifacts actually produced by the suite. They are not established merely by the suite summary.

## 2. Freeze an exact exception list

Prepare a list of exact repository-relative file paths, not a directory glob. For each changed or added path record its disposition, old/new Git blob and mode where present, byte length and SHA-256, reason, affected verification roles and the review that establishes it is an output or governance update.

The default permitted modifications are:

| Exact path | Permitted scope | New verification |
| --- | --- | --- |
| `STATUS.md` | Actual current outcome, remaining gates, exact integration/ownership identities and links. No changed product promises or numerical authority. | Final claim review and documentation/link check. |
| `docs/engineering/repository-reconciliation-2026-10-28/README.md` | Actual reconciliation, validation/publication narrative and links. | Final claim review and documentation/link check. |

New evidence members may be added under `docs/engineering/repository-reconciliation-2026-10-28/` only when each exact path is listed. A path under that directory is not automatically exempt. Record new JSON, logs, archives, images and other artifacts individually. Identify executable reproduction material separately and review it; its presence is not evidence that it ran.

Prefer keeping every existing JSON/input/review/receipt/log immutable and adding separately named final summaries. If an existing JSON summary must change, add an explicit reviewed exception naming its permitted changed fields and preserve its previous bytes. Never replace earlier input hashes, command outcomes, review inputs or failures to imply that an earlier run covered later bytes. Existing logs and evidence members must not be overwritten by a later attempt.

No exception is permitted for the preserved held-source subtree, AGENTS, GOAL, the root README, either adopted C059 decision, runtime, tests, tools, schemas, workflows, examples, source libraries, frozen corpora, adopted language/release documents, independent oracles, verification pins or test mappings. More generally, **every path not individually excepted remains an equality requirement**. No original path may be deleted or renamed by this publication-only phase. No new symlink, submodule or executable activation is evidence-only.

## 3. Establish equality on the actual merge result

Use the observed resulting-main commit, not a planned merge SHA or a moving branch name without readback. Record its actual tree and merge parent identities. The archive retention commit must not appear as the product merge source or product base.

1. Read the complete untruncated Git trees for the tested candidate and resulting main. Compare their union by exact normalized path, object type, file mode, blob and byte size. Include newly added, removed and mode-changed paths. Reject unsupported special entries.
2. The resulting tree difference must equal the reviewed exact exception set: no extra path, missing expected change, rename, deletion or mode-only surprise. Outside that set, the complete tracked mapping must be identical.
3. Hash the actual resulting-main checkout or immutable downloaded blobs and verify its binding to the observed tree. Require a clean worktree and no unaccounted untracked source inputs. A local checkout at the right HEAD with changed files is insufficient.
4. Reconstruct the driver's source inventory without importing or running product code. Match its original source-directory/root-file and ignore rules. Reject duplicate, absolute, traversal or escaping paths and symlinks. Compare the union of tested and final inventory members after removing only the exact reviewed exceptions. Require identical paths, byte lengths and SHA-256 values.
5. Confirm every added inventory member appears in the exception list. Preserve all original example identities; do not apply the driver's isolated-workspace generated-product exemptions here.
6. Record counts and hashes for the equal subset, the complete old/new inventories, all differences and every approved exception. Preserve the old aggregate inventory digest unchanged; the new aggregate digest is expected to differ.

This establishes candidate-to-main identity for unchanged eligible inputs. It does not rerun a role, establish a new interpreter/platform, prove timing stability on another machine or validate a destination that was never exercised. A narrow runtime-file digest alone is insufficient.

## 4. Fresh checks for the changed evidence and documentation

Run the unchanged preservation/link checker on actual resulting main. Keep its actual command, source identity, inputs, environment, exit status and output. This covers the changed navigation and preserved original documents; it does not validate the new evidence JSON.

Independently audit each new or changed record:

- Parse JSON strictly; reject duplicate object keys and non-finite numbers. Apply the identified schema or explicit field contract, unique IDs, normalized paths and exact type rules. Do not silently normalize malformed records.
- Resolve referenced members within their declared evidence root. Require containment, unique paths, actual existence and exact byte length/SHA-256; compare Git blobs/modes when claimed. Validate archive transport bytes separately from extracted member closure, and do not claim internal inspection without doing it.
- Bind command receipts to actual source commit/tree, input manifest, executable/tool identity, settings, command, start/end, exit status and raw logs. A generated summary is not a new execution. Verify planned/executed role sets, actual test counts, exclusions, failures and pending roles against their underlying reports.
- Verify supplemental readers used the exact produced/retrieved artifacts. Keep original failed attempts separate. Preserve the actual C035 exclusion, known reach failures, absent compatibility roles and all uncompleted release gates.
- Reconcile final STATUS and README claims against the receipts. A historical preparation record that says pending may remain as such when clearly labeled; final result claims need a separate actual receipt. No pass is inferred from an earlier proposal/review or a commit's existence.
- Keep the initial policy review bound to its original exact files. For changed STATUS, reconciliation narrative or summaries, add a final review/reconciliation. Do not change that review's historical input hashes.
- Verify actual cleanup/ref/PR outcomes against their recorded readbacks. The documentation checker skips remote URLs and does not establish live GitHub state.

The unchanged checker verifies 29 historical source-map records, reconstructs the original baseline tree, and scans Markdown/HTML local links. It does not parse arbitrary evidence JSON, check recorded hashes/commit IDs in code spans, validate remote URLs, certify current runtime inputs or check the truth of result claims.

## 5. Output records and finite publication closure

Keep validation output outside the checked source tree while commands run. Outputs and postprocessed summaries are not their own inputs. Explicitly identify any records generated after a check. Bind their exact bytes through the later immutable publication/readback rather than claiming that the earlier command validated them.

If publication of receipts creates a later main commit, compare that transition separately: only the exact named output records may change. Reuse computational evidence only while the original eligible-input equality remains true. Rerun documentation checking when new or changed Markdown/HTML/link targets affect its inputs; JSON-only output additions need their own member/claim audit and exact publication readback, not another unchanged runtime suite.

A suitable final claim is: the identified candidate completed its recorded checks; the actual resulting main preserves every unchanged eligible computational/verification input; its changed documentation and evidence received the separately identified checks; the named incomplete reach and release gates remain open. Report actual stage outcomes and source revisions, not a synthetic single all-purpose green result.
