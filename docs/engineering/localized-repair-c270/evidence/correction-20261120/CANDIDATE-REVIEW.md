# C270 exact-candidate review

Reviewer: `/root/github_reconcile`.
Candidate: `a6099546e2ae66e78621008338ecd3b2d352d9b8`.
Tree: `6e05696718723fe77f6973d1aa2319638723d127`.
Starting main: `55c585acdaa750961ac37a5c46c9160bed149f97`.

## Verdict

The classification correction, current dependency-pin changes, preservation boundary and completed affected-check evidence are acceptable. No mandatory finding remains in those reviewed areas. This is a bounded correction of the C270 R02 refusal category, with no added successful endpoint support.

Final integration eligibility is **pending** the separately running routine local driver's outcome and review of any later documentation/evidence-only checkpoint. This report does not approve an unknown future candidate. Actual-main verification and saved delivery remain Director-owned later gates.

## Reviewed behavior and rationale

The frozen control declares a private parameter of exact type `SiteRef` in the same class as the joint that reads it. Its initializer aliases an existing site. Adopted core type/member/access rules independently establish the validity argument preserved in C270; C260 explicitly excludes parameter-based endpoint observation and requires unsupported-form refusal.

The new branch in `Source.site()` uses the actual resolved member kind, exact complete type token and authored visibility. It returns `UNSUPPORTED_SOURCE_FORM` for accessible declared `SiteRef` parameters. It never reads the initializer's value, follows an alias, derives a site identity from that value, or returns a qualified record. This is sufficient to identify an unsupported form; it is not a source-validity validator.

The access check occurs before the new unsupported classification. External private parameters remain `MALFORMED`. Missing terminals, other member kinds, non-`SiteRef` parameters, invalid nominal-type forms and omitted parameter visibility remain `MALFORMED`. Existing declared-site observation, private-own-part traversal, intermediate-path refusals, numerical behavior, bounds and successful result structure are unchanged.

The additional `explicitVisibility` fact is confined to this decision. The parser's historical default remains untouched. This avoids classifying a visibility-omitted property as an admitted declaration when the adopted property grammar requires explicit visibility.

No unresolved ambiguity justified additional behavioral probes. The reviewer inspected the exact code and the complete supplementary test logic, independently checked retained results and identities, and did not duplicate broad suite execution.

## Change and dependency audit

The only behavioral source changes are `Source.scan_class()` and `Source.site()` in C265. In C266, C267, C268 and C268's current fixture helper, removing the `DEPENDENCIES` assignment makes each before/after abstract syntax tree identical. Those four files contain no other behavioral change.

All 17 current downstream dependency entries match actual candidate sizes and SHA-256 values. The unchanged C265→C257 dependency also matches. All nine changed dependency entries agree with the recorded before/after identities. C268's historical input pins, C257, C261 and the independent C266 fixture recipe remain unchanged.

| Implementation file | Bytes | Candidate SHA-256 |
| --- | ---: | --- |
| C265 `source_hinges.py` | 38229 | `70d5e5b6247347bf44eaa3be0bc9c91b13f10d4717b4b32261eaebad75987132` |
| C266 `hinge_binding.py` | 17639 | `8f6b26f0bedad335b069975d0491e5565a25f0793b3bc48802e90d3993aa0d0a` |
| C267 `hinge_compare.py` | 12382 | `9b2899d95471546a25a8a7e5ed9d9ac2a1e42854c31808d4e68aff2582686b58` |
| C268 `endpoint_reader.py` | 14914 | `97cdff3449d84c4d6cbc249b17578e45a90066e824424b6dd2c334156f91094a` |
| C268 `endpoint_control_fixtures.py` | 9181 | `4c9cd728aed99fca2bd190deba432f1c1d97abdb55b1f8de0d8ae56386633d48` |

Git tree comparison preserves 18,460 existing entries with unchanged object identities and modes. Exactly the five authorized implementation/pin files and five declared workflow/status files change; there are no deleted existing paths. Additions are confined to this correction's documents/tests and evidence. All 204 original C260/C270 engineering files, including the frozen source/oracle/runner and original failure evidence, are unchanged. The oracle remains `aa73df1e9ffb4d76bc589a7239f454be28e4cd6ae4ee523b208dbf66860ef4a7`.

The six retained implementer-preflight code snapshots match the candidate bytes. A preflight result remains attributed to its recorded uncommitted input snapshot; the fresh candidate executions below supply the committed-source evidence.

## Inspected fresh execution evidence

All completed reports identify candidate `a6099546e2ae66e78621008338ecd3b2d352d9b8`, its exact tree, CPython 3.12.14 and Linux. Before/after source and input identities are stable, and the tracked checkout remains clean. The reviewer reopened the listed input/output files and verified their sizes and hashes, checked retained cause-chain fields and log method totals, and compared the results with the unchanged oracle and inspected test code.

| Evidence | Inspected outcome |
| --- | --- |
| Frozen C270 H16 runner | 5 cases, 45 assertions pass; no failed assertion |
| Three changed-input interfaces | Source, binding and comparison all return exact `UNSUPPORTED_SOURCE_FORM` |
| Refusal propagation | Matching reason and complete source-origin cause chains; exact source hashes/sizes and artifact identity retained; no qualified partial fields |
| Original positive inputs | Source has 8 hinges/16 sites; original comparison retains full declared-field agreement |
| Complete affected cohort | 12 groups, including 282 methods and 14 original corpus bindings; zero failures, errors or skips |
| Supplementary distinctions | 8 methods covering 16 variants and 48 public-interface calls; all pass |
| Documentation/workflow checks | Both pass on the exact candidate |
| Frozen control reconstruction | `build_control.py --check` recorded as passed; preserved inputs independently matched to oracle identities |

The affected method inventory is C255 31, C256 29, C257 23, C258 28, C261 28, C265 49, C266 34, C267 25 and C268 35. The three additional groups are the C253 corpus binding check, documentation preservation/navigation, and workflow structure. The C266/C267/C268 retained call records and corresponding output hashes were inspected; none contains a reported failure, error or skip.

The unchanged historical runner still carries its original text saying “No implementation repair.” That is a limit of that retained runner invocation, which does not edit code, not a claim that this correction phase made no repair. The present phase and exact implementation identity make the distinction explicit.

## Review artifacts and remaining gates

- `DESIGN-REVIEW.md` records the independently derived boundary before implementation inspection.
- `CANDIDATE-STATIC-AUDIT.json` records 74 successful source/pin/preservation checks; `audit_candidate.py` reproduces them.
- `CANDIDATE-EVIDENCE-AUDIT.json` records 282 successful evidence-identity/assertion/log checks; `audit_evidence.py` reproduces them. These are audit checks, distinct from the 282 executed regression methods.
- The routine local driver is still pending at this report's checkpoint. Its result must be retained and any new or worsened failure assessed before integration.
- Later evidence/state-only publication requires exact-delta review, then conditional integration, fresh actual-main checks and the separately verified saved handoff.

No complete H16, H20, H22, H24, C260, source validity, site/world behavior, native/model trial, product qualification or comparative advantage follows from this correction.
