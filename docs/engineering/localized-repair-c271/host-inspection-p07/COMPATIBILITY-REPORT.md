# C271 P07 — gaps and compatibility

**Verdict proposed for independent review:** the missing prerequisite can be implemented as one bounded host-inspection authoring module, without editing the adopted P05/P06 contracts or current provider/probe. This is a design verdict. No host has been selected or qualified, and no operational configuration is supplied.

The source baseline is the retained implementation at `3d9d5eacaff25244916f99912ef92947e1582592`. The Director's later `f980ad31eb2af9d7e8b1b233b84e21ee662730fd` checkpoint adds P07 workflow documentation without changing that implementation. `SOURCE-BINDINGS.json` records actual local hashes and source anchors; the Director owns remote-state validation.

## Current gaps and the selected resolution

| Observed gap | Bounded design resolution | Remaining evidence |
| --- | --- | --- |
| P06 consumes HOST/inspection documents but has no authoring entry point. | New `prototypes/static_tray_v01/current_host_inspection_v01.py`, inside both existing source inventories. | Future implemented bytes, focused controls and independent source review. [S05; S07–S09] |
| `validate_selection` already requires successful HOST receipts. | Use a new closed pre-HOST inspection plan and externally supplied approved digest. Observe only after independent static review. | Actual interpreter/inspector/loader/source/path fields and reviewed plan; unavailable in P07. [S08] |
| P06 host/inspection objects reject extra fields; process/cleanup schemas describe success only. | Preserve their exact schema. Keep plan provenance, counts, refusals, failures and unknown outcomes in new immutable sidecars. | Real successful process receipts; failure-sidecar tests. A mock cannot fill an operational success receipt. [S06; S08; S09] |
| Original supervisor preserves process handling but its raw final file is not an atomic durable publication interface. | Retain its raw receipt; wrapper atomically commits independent evidence. If a final write loses the receipt, keep actual start/logs and mark UNKNOWN. | Fault controls for write/fsync/rename/callback/interruption; no invented success. [S11] |
| Runtime closure must be authorized before `ldd`, which can itself invoke loaders/commands. | Independently review one finite static resolution map and exact script/interpreter/runtime inputs. Freeze required presence/absence and all admitted branches before launch. | Actual host static closure and unsupported-case decision; no general loader emulator. [S01; S08; S09] |
| Current consumers use a permissive regex/set extraction of ldd paths. | Authoring accepts a stricter complete-line grammar and exact predeclared mapping; reject every unexplained line/path. Its successful output still satisfies both consumers. | Real compatible stdout; parser controls cover malformed/unresolved/extra cases. [S08; S09] |
| Python and JavaScript have some nonidentical checks. | Author only the stricter intersection: actual Linux/glibc; exact seven pins; regular nonlinked `/usr/bin/ldd`; direct shebang; no `not found` in either stream; exact role/alias/file sets. | Static schema/consumer review and later actual JavaScript execution. [S06; S08; S09] |
| P06 source acceptance contains only selected static/mock controls. | Preserve evidence/reuse decisions by exact input identity; run actual H1/H3 separately. | P06-H01/H02/H03 remain `NOT_RUN_GATE_H`; three CPU starts remain their own denominator. [S23] |
| Driver summary uses aggregate unittest footer counts. | Require a separately source-bound observational collector and per-method independent reconciliation before Gate R. | Exact collector/hook and actual full outcomes; no replacement test runner or method changes. [S01; S12] |

## Exact compatibility choices

The inspection CLI defaults to a static check captured by the outer harness; it does not consume the fresh observation paths. `--observe` starts only the two approved preparation commands. Source validation may reuse the five bounded existing Git identity reads, separately bound and accounted. The current source guard is not represented as a zero-subprocess operation. The `rename_without_replacement` import is explicit, rooted at the authenticated checkout; its source is already listed by both P06 consumers. [S08; S10; S12]

The successful command shape remains `[NODE, "--version"]` or `["/usr/bin/ldd", NODE]`, with the exact five-variable Node environment. Each uses a total 5,000-ms clock, a maximum 3,000-ms active interval and the existing 2,000-ms cleanup reserve. This is stricter than treating five seconds as active work followed by extra cleanup, and it satisfies both current receipt validators. Unexpectedly slow observations fail visibly; the design does not extend the deadline. [S06; S08; S09; S11]

The P06 `process` record has fourteen required keys; its `cleanup` record has four. Host has ten top-level keys and exactly two inspection descriptors. No approval flag, plan digest, start counter, failure field, null-success value or extra host role is added to those objects. New sidecars carry the extra evidence. They represent an interrupted launch window with a null exact start count and an observed lower bound; missing durable callback evidence cannot be counted as zero. Descriptor path/mode/size/digest checks use the current schema. [S06]

The current host roles require nonempty `loader_configuration`, `shared_libraries` and `inspector_runtime` lists. Named aliases must equal the union of roles, and files equal their resolved targets. The design refuses hosts that cannot truthfully supply these sets; it does not fill them with unrelated placeholders. Intermediate alias/ancestor and absence guards are recorded separately because P06's alias schema cannot represent them. [S06; S08; S09]

The selected Node build, source archive, exact 24 dependencies, all seven original method IDs and nine method/helper AST bodies remain fixed. A static comparison confirmed all nine original body hashes match provider constants. The current probe's scientific suffix from the no-external-fetch statement through exit handling is byte-identical to the original probe. This is source-preservation evidence only; JavaScript syntax/runtime behavior is untested. Exact hashes and 24 dependency identities are recorded in `SOURCE-BINDINGS.json`. [S08; S09; S13; S19; S21]

The original module header still describes historical setup inspections; P06 current setup consumes approved observations and runs no preparation command. The design preserves that existing source byte and reports the actual current boundary separately. Preparation, syntax, direct negatives, original CPU checkers and mocked coordinator seams therefore have distinct counts. No historical header or old successful run is reinterpreted as current execution. [S07; S08; S13; S17]

## Unresolved items, deliberately not invented

The future implementation and its exact hashes do not exist. Real executable/destination paths, Python/ldd/loader closure, install receipts, host timestamps/boot ID, successful inspection receipts, actual discovery inventory, configuration digest, negative fixture hashes and the later observational/audit tool bindings remain unavailable. These are the inputs of later declared stages, not reasons to label this design an executable plan.

No mandatory incompatibility has been identified that requires a consumer edit. Actual static inspection may still find a host the strict P06 schema cannot represent, a loader resolution the finite map cannot justify, or a command that cannot finish inside five seconds. In that case stop with a concrete refusal and retain evidence. Any need to widen schemas, execution surface or time limits is a separately reviewed scope decision, not an implementation convenience.

The no-reader-import conclusion for H01/H02 relies on the actual early refusal plus bound probe/module-loader control flow. It is explicitly an execution-path inference, not operating-system-wide import telemetry. The later independent reviewer must decide whether the frozen evidence supports that exact claim. If not, the direct-host gate stays unmet pending a bounded separately reviewed observation method.

P07's current acceptance question is whether this design is concrete and compatible enough for the next bounded HI implementation. Host eligibility, original seven outcomes, complete Gate R/R03, R04 integration and R05 closure remain open. No existing failure is relabelled and no execution gate is waived.

## Authoring checks and retained errors

`AUTHORING-ERRORS.json` preserves one failed metadata collection: the initial path list assumed C225's separately archived `audit_outcome.py` was a current repository file. The collector stopped with `FileNotFoundError` before producing its source inventory. The corrected inventory binds the current `evidence/OUTCOME-REVIEW.json`; the historical review and raw-evidence boundary remain explicit. No project code ran and no repository file changed.

`drafts/author-001/` retains the first human drafts before correcting an internal process-field count and clarifying dry-run path reuse. The final static artifact report records exact schema-key agreement, control coverage, source/body hashes and zero execution claims. Independent review remains separate from these author checks.

### Independent count-contract correction

Candidate-001 remains immutable. The reviewer identified that interruption between child launch and durable callback leaves actual starts unknown. Candidate-002 explicitly separates exact actual count (0/1/null), observed lower bound and count status; requires positive evidence for zero or one; and prevents unknown aggregates becoming zero. This changes only the new sidecar design and associated plan/control descriptions. Existing P06 success schemas and source remain unchanged.
