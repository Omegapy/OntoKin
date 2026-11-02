# Independent static review of the C088 binding integration

**Decision: no static integration blocker found. Dynamic verification remains pending.**

Reviewer: `membership_review`, separate from the author of the Agent, runtime,
catalog, export and schema wiring. The exact reviewed bytes, file modes and all
schema differences are bound by `ROOT-INTEGRATION-STATIC-REVIEW-01.json`, SHA256
`46f8d42d3aa0659450d359cc7ac81258c80000f54aedefcd57f4d66857d49bdc`.
The worktree basis is adoption commit
`a4d16331f720671548d125f2fcf3e1745277f631`; the contract remains specification
SHA256 `e9a55ae015b1892453217deea38ea85e269e2551608ab5ed7aa7d21bea337d0b`.

## Scope and findings

The review read the eight changed shared production files (`agent_cli.py`,
`budget_runtime.py`, `cli.py`, `evaluator.py`, `execution_budget.py`,
`program_runtime.py`, `scene.py`, `texture_gltf.py`), all five new
`keyed_membership_*` binding modules, and the three Agent/0.21 schemas. It also
traced their inherited Texture and Budget service, runtime and protocol entry
points. The review did not import or execute product modules.

- The explicit Agent/0.21 service, protocol, runtime and independent store select
  the new profile without registering it as an old default. Existing bundle/0.2
  and files/0.2 transport, operation shapes, immutable source/asset handling,
  admitted request context and durable lifecycle remain inherited.
- The added entry-budget version map, direct export wrapper, CLI dispatch,
  program support record, scene contract map and native texture reader target
  selection consistently name source/Agent/GLB .21. A repository text audit
  found no remaining shared `.20` dispatch branch outside these reviewed paths
  that required extension for this bounded successor profile.
- The direct export wrapper fixes the profile and rejects a caller-supplied
  replacement. Scene validation continues requiring an exact authored
  profile/delivery-target match. The `.21` texture reader enters the inherited
  strict shape branch; no new metadata-authority field or membership-lineage
  family is admitted.
- Discovery derives detached JSON from predecessor templates and constructs
  current host-policy information for each request. It describes all five
  membership stages, the full admission cost, eager/static behavior, declaring
  boundaries, retained generated restrictions and inherited provenance. Its
  String entry explicitly lists .20 and .21 declaring semantics while retaining
  the original String diagnostic profile and byte quotas. The original .20
  catalog source is unchanged.
- An independent structural comparison found exactly 26 scalar schema changes:
  binding/profile identifiers, titles and the response contract description.
  Every inherited request field, operation shape, diagnostic reference and
  provenance record structure is preserved. The three predecessor schema files
  remain byte-identical to adoption HEAD. This review checked actual objects;
  it did not rely on the root-authored derivation receipt as its oracle.

## Focused integration tests authored before execution

`tests/test_keyed_membership_interfaces.py` contains nine focused tests. Source
bytes, revision identities and Boolean answers come from the frozen input
packet. The tests cover current and detached discovery; predecessor isolation;
independent store reopen and unchanged defaults; cross-contract and extra-field
request refusals; exact inherited schema shapes; true and false membership
inspection retaining the original closed filter records through repeat and
reopen; inherited rekey constraints; explicit parser and CLI selection; and a
small real CLI GLB/0.21 export whose strict reader rejects invented metadata.

The new test file has SHA256
`5a9fa592710e5f7784bf7df1648391300b3828f295b8a187d72ed768115f4485`.
Its syntax compiled under Python 3.12.14 without imports or test execution.
`tests/test_string_concat_interfaces.py` was independently compared with HEAD
and remains byte-identical. The receipt is
`../implementation-notes/INTERFACE-STATIC-COMPILATION-01.json`.

These tests supplement the independently authored source, native, resource,
Agent, delivery, hostile-reader and inherited acceptance cohorts. They do not
replace those gates, and this review makes no passing runtime claim.
