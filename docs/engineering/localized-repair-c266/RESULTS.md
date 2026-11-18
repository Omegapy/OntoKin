# C266 results: input association prerequisite

## Implemented boundary

The isolated `bind_hinge_inputs` function validates complete retained source/program/object provenance against independently derived source facts. Both repeated artifact maps must agree with source, including source byte spans, class/declaration identities, typed path steps and generated input-entry witnesses. It returns bound objects only; hinge value/set/endpoint agreement remains false. [Requirements](../../workflow/tasks/C266/REQUIREMENTS.md) and [README](README.md) define exact coverage and exclusions.

Implementation checkpoint: `5454bfeb2c27aed0af23fb4dd363638ffbb10b07`. Implementation SHA-256: `68849dbe3339c158eac7ec43fb1defcbd2993c37c6a0a5ee813d2da71fb03dda`. Original source/GLB pairs both bind eighteen objects. Changed membership also binds without a fixed count. No product compiler/evaluator/exporter or native application ran.

## Independent control outcomes

The final authored suite passes 34 methods with zero failures, errors or skips. All 748 public API calls match expectation: 28 bindings and 720 typed refusals. Tests derive expected mappings independently from source bytes and declared construction rules, not from implementation helpers. The exact test/helper/source snapshots, per-call input identities and deduplicated actual input bytes are retained in `evidence/independent-controls/run-02/`.

The earlier run-01 retained two test-fixture construction errors: its positive final-override fixture attempted duplicate same-scope assignments. The pinned source utility correctly refused them. The corrected fixture supplies a single direct owner override of a distinct class default; an explicit duplicate-override refusal test was added. Implementation bytes did not change. Original test/helper snapshots, logs/results and input ZIP remain in run-01.

[Independent review](REVIEW.md) approves the exact published implementation, with 87 distinct passing controls. Its one earlier inserted-key fixture error and corrected outcome remain preserved. The public-API checks include matching-but-wrong repeated provenance, UTF-8 offsets, complete object sets, opaque keys, full keyed-entry spans and intentionally unqualified changed/omitted hinge fields. No complete C260 H group is claimed.

## Candidate and resulting-main gates

The complete declared affected cohort includes C253 corpus binding, C255/C256/C257/C258/C261/C265/C266 methods, workflow structure and documentation preservation. Candidate and actual-main execution receipts will identify their exact revisions and outcomes separately. A component test pass alone does not establish those later gates.

This engineering-only standard-library component is not imported by the product. Runtime, exporter, fixtures, profiles, source budgets, hosted workflows and predecessor component bytes remain unchanged. Full product aggregate, conformance/export/native/visual/model trials and other Python compatibility roles are not run for this isolated increment. Historical failures retain their exact states, including the earlier failed aggregate and thirteen torque-read methods not run. C174 full historical graph retention remains unestablished; no full offline archive is claimed.

## Next boundary

After verified integration and saved delivery, a new continuation may select complete hinge-field/set/ordered-endpoint comparison under unchanged C260. C266 deliberately leaves omitted top-level module/scene and program collections unobserved; a future full comparator must reconcile any additional required association rather than assume this prerequisite proves it. Historical byte admission remains a separate fourth interface.
