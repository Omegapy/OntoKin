# Current-host provider implementation candidate

This is the P06 implementation candidate for the [adopted P05 design](../current-host-p05/ADOPTION.md). It is separate from the historical C199/C225 execution environment. The files below do not establish an eligible host, historical replay, an actual Node result, full routine completion, R03 acceptance or integration.

## Entry points and selection

The new Python provider is `prototypes/static_tray_v01/current_host_readback_v01.py`; the new probe is `prototypes/static_tray_v01/current_host_readback_v01.mjs`. The separate preparer is `tools/prepare_current_host_readback.py`. The driver selects an absolute configuration path and an independently approved expected digest. The original CPU class reads those same two values from `ONTOKIN_CURRENT_HOST_READBACK_CONFIG` and `ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256`.

| Interface | Result and boundary |
| --- | --- |
| `validate_selection(config_path, config_sha256, source_root)` | Returns the decoded configuration only after static identity checks. It starts neither Node nor ldd. |
| `derive_workspace_binding(config_path, config_sha256, source_root, workspace_root, output, source_before, workspace_inventory)` | Requires the driver's complete copy equality and Git identities. Creates a fresh derived configuration and binding; returns their paths/digests and the immutable parent configuration digest. |
| `prepare_case_manifest(output, *, config_path, config_sha256, source_root, schedule_root)` | Exclusively creates the new manifest and returns its value/digest. |
| `verify_case_manifest(path, *, config_path, config_sha256, source_root, schedule_root)` | Rebuilds the expected binding and compares the entire manifest, including the twelve original ordered structural slots. |
| `guarded_run_process(argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None)` | Validates before and after one call to the unchanged supervisor. No retry, clock reset or limit extension. |
| `setup_cpu_cohort(cls)` / `finish_cpu_cohort(cls)` | Preserve setup failures, reconcile three checker attempts and retain evidence before explicit cleanup of an owned temporary cohort. |

The configuration, manifest, host lock, source/dependency inventories, method/discovery locks, workspace binding and install plan have closed structures in [SCHEMA.json](SCHEMA.json). The schema describes required structure. The implementation additionally checks actual bytes, modes, aliases, path relationships, full inventory membership, clocks and source ownership. Canonical provider documents use sorted ASCII JSON with comma/colon separators and reject nonfinite values and duplicate keys.

An expected digest does not come from the configuration being approved. It is a separate input to the driver/provider. The Node application argument carries that same comparator:

`NODE --no-addons --max-old-space-size=256 --experimental-loader LOADER NEW_PROBE --expected-config-sha256 DIGEST --job FILE`

The digest pair appears before the terminal job pair, so the unchanged original helper can continue replacing only the final argument. The guard compares that argument with its externally selected digest. The probe compares actual configuration bytes and the manifest selection against the argument; a rewritten configuration/manifest/job cannot supply its own expected comparator. The five original Node environment variables and original Node flags remain fixed.

The initial P06 concern assumed the argument shape could not carry this comparator. The independent review corrected that premise: the adopted contract forbids **unbound** extra flags, and the original source map explicitly permits the argument-parser/bootstrap adaptation. The initial finding and superseding review are retained in phase evidence. This adaptation does not weaken the CH11-C coherent-unapproved-input refusal.

## Source and workspace ownership

The provider derives its own root from its loaded source file; the probe derives its own root from `import.meta.url`. Executable roles must belong to that root. A copied workspace cannot execute the original checkout's provider or probe.

The CPU source inventory contains every regular file under `ontokin`, `tests`, `prototypes/static_tray_v01` and `tools/static_tray_reader_v01`, plus the explicitly listed driver/preparer/storage helper, package locks, project metadata, C198 controls, original external manifest and adopted P05 contract/adoption/map inputs. Parent initializer files are included when present. It rejects links, special files, bytecode caches, changed/missing/extra entries, dirty tracked source and untracked source. The source commit/tree must be the actual clean selected checkout. Only the existing driver's exact generated-file exclusions can apply to a derived workspace.

This CPU execution inventory does not replace the driver's larger inventory of copied source and preserved evidence. The workspace derivation binds that complete original/copy equality, both roots, the same commit/tree, the immutable parent configuration, a fresh identity and the actual workspace provider/probe paths. It preserves the original configuration. The immutable method lock's original map descriptor remains evidence at the original root; the copied map's bytes must match too. This evidence reference cannot redirect executable source.

The seven original methods, `check_case` and `run_seam` retain their original body AST identities. Only the original module's provider imports, availability decorator and class setup/teardown wiring change. The availability skip is removed. Missing selection is a visible setup error. The original module header and historical path constants remain from its previous provider; current setup consumes already approved host observations and starts no preparation command.

## Host and exact dependency inputs

Only Node `v24.22.1` is accepted. The executable must have the selected P05 digest `acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa`, size 126,951,512 bytes and mode `0o755`. Its source archive must be the separately saved P05 archive: digest `100ae976555b388472c3e875aeda67bd7d8c9229a968a11661fb852624adaeb5`, size 45,186,132 bytes. These bindings identify the selected candidate; they do not assert vendor provenance or historical binary equivalence.

A host lock binds the actual Linux boot/platform/kernel/libc identity; Python executable/version and the seven unchanged verification pins; the selected executable; complete admitted runtime/inspector/interpreter/library/loader roles; actual aliases and file modes; and independently retained bounded inspection receipts. The provider reads ELF interpreter metadata without execution and checks the ldd script's interpreter. Successful version and shared-library receipts must use the fixed clean environment, a five-second allowance, exact commands, actual process/start/exit/cleanup evidence and bounded output. The version must match exactly; unresolved or changed shared-library bindings refuse.

The dependency inventory is restricted to the exact 24 relative files from the unchanged C199 external-input manifest. It retains validator `2.0.0-dev.3.10`, Three.js `0.186.1`, revision `186`, and the original module loader/layout. Every file and necessary directory is checked, including mode, missing/extra entries and link refusal. No general npm lock or newer package substitutes for these inputs.

**Fresh host observation and receipt authoring remain unfinished Gate H prerequisites.** P06 implements their strict consumption and safe static installation; it does not add or run a host-observation command. A later bounded phase must author/independently review the actual observation tooling and freeze real source/input/host identities before using these interfaces. Supplied JSON or a passing mock is not a host qualification.

## Checker lifetime and evidence

The original scientific helpers keep their 30,000-ms clock, child deadline at 28,000 ms and 2,000-ms cleanup reserve. The guard consumes that same clock for binding work. It verifies again after writing preflight evidence and before the single supervisor call. Bounded Git reads use only remaining allowance. It rechecks source, configuration, dependencies, runtime, manifest, job and inputs after every actual supervisor outcome.

The original supervisor receives the same argv, environment, clock, stage deadline and cancellation argument. A start callback wrapper records the start and invokes the original callback once. A provider evidence failure remains a provider failure even if the supervisor converts the callback exception into its own `Stop` during cleanup.

Only a genuine delegated supervisor `Stop` may be re-raised unchanged, and only after successful postflight. `CurrentHostBindingError` is a separate `RuntimeError`, with a `CH-` category and retained cause/process evidence. Adapter clock failures use `CH-CLOCK`. This prevents the original negative-reference helper from treating a binding or evidence failure as its intended scientific rejection.

Each attempt reserves a separate ledger outside the checker stage, saves preflight identity, actual start, the unmodified supervisor receipt, postflight state, output hashes and final failure/success/unknown state. Evidence uncertainty is failure or unknown. Setup uses its own `try/finally` because unittest need not call teardown after a setup error. Teardown checks all three expected case ledgers and preserves temporary evidence before removing only its own temporary directory. Interrupted work has no destructor that can erase its evidence.

An absent or untrusted selection cannot authorize a filesystem destination. That refusal carries a structured `refusal_record`, no-start information and `evidence_finalized: false`; the driver or independently declared direct-invocation harness must capture it. The provider does not invent an ambient output parent. Once the configuration is authenticated, setup failures retain their own durable record under its approved evidence root.

## Safe static preparation

The preparer accepts `--plan ABSOLUTE_FILE --plan-sha256 EXPECTED_DIGEST`; it is a dry-run unless `--apply` is explicit. It never starts recovered code, Node or ldd. Operational plans identify either the exact retained dependencies or the selected Node archive; the CLI refuses the `isolated-control` purpose used by tiny filesystem regression fixtures.

The plan freezes the whole archive member inventory, target file/directory inventory, modes, input descriptor, source binding and fresh report destination. Preparation rejects absolute/traversing/backslash/noncanonical names, duplicates, symlinks, hardlinks, special/sparse files, unexpected modes, excess count/size, missing/extra members and changed bytes. It hashes all admitted archive contents and materializes only declared regular target files.

An existing destination must be complete and exact; it is never repaired in place. An absent destination is staged under the same parent and published with Linux `renameat2(RENAME_NOREPLACE)`. Ancestor identities are checked before/after publication. A race retains the other writer's content and records exact readback without retry. A lost/uncertain publication reply stays unknown. Cleanup checks the owned staging inode and never deletes the published destination. Reports and prepublication intent are separately retained.

## Verification boundary

Static parsing and original-body identity checks can establish source preservation only. Focused Python filesystem tests and explicitly mocked process boundaries establish only their selected controls. Their exact source, fixture identities, mock seams, commands, failures and outcomes belong to independently frozen phase evidence.

No claim of actual Node syntax/runtime execution, direct-probe refusal, original three CPU outcomes, numerical-row recomputation, host qualification, complete runtime discovery, full routine completion, R03 acceptance or integration follows from this candidate. The original four coordinator seams remain mocked controls. Later Gate H must execute the real approved positive/negative routes, independently audit measurements and complete cleanup evidence; Gate R must reconcile and run the whole required default inventory and all driver stages.
