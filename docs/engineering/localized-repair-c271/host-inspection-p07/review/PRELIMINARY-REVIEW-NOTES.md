# Preliminary P07 review notes

These are source-derived review criteria before the author candidate exists. They are not a candidate verdict or new acceptance.

- Keep independently selected approval separate from observed host data. P06 validation already consumes HOST; avoid a circular bootstrap in the new authoring entry point.
- Emit exactly the closed P06 host and successful inspection schemas. Failure, refusal, no-start and unknown receipts require a separate durable ledger. Never convert one into a successful inspection.
- Retain exact inspection argv, fixed five-variable environment, 5,000-ms total process lifetime, actual PID/process group, bounded logs and cleanup proof. The original supervisor reserves 2,000 ms within the five-second inspection allowance.
- Source/recovery/runtime/dependency provenance must precede execution. A version response cannot approve an executable. The source archive and candidate Node pins remain fixed.
- Host roles, named aliases and resolved file inventories must be exact sets. Bind ldd, its literal shebang interpreter, inspector inputs, dynamic-loader files and all seven required Python package pins.
- Explain how loader resolution is observed before execution and independently selected afterward without pretending that hashing a current machine authenticates an entire operating system. Refuse unexplained or unresolved loader behavior.
- Preserve expected/attempted/actual-start/terminal/unknown denominators separately for inspection, direct-probe controls, original CPU methods, mocked coordinator seams and later full routine.
- Retain P06-H01/H02/H03 and all seven original method outcomes, and keep Gate R, R03/R04/R05 open.

Primary inspected anchors: provider `_verify_inspection`, `_verify_host`, `_verify_source`, `_alias`, `_elf_interpreter`; probe `verifyInspection`/`verifyHost`; supervisor `Clock`/`run_process`; P05 adopted contract; full P06 schema. See READ-SET.json for exact identities.

No source/project execution occurred. One combined read output exceeded the display budget; the omitted contract tail and machine contract were subsequently read separately, and the full P06 schema was read in compact canonical form.
