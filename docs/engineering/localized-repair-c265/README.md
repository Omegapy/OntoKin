# C265 independent source hinge observer

`observe_source_hinges(source_files)` derives the finite source interface in
[C260 contract 0.1.0](../localized-repair-c260/CONTRACT.md). The isolated
[source module](source_hinges.py) takes exactly a dictionary of supplied
`main.ok` and `hinges.ok` bytes. The entry must pin the actual companion hash.
It uses the exactly bound C257 lexical/module/occurrence utility and independently
reads site and hinge declarations. No product compiler, evaluator, exporter,
GLB field, semantic sidecar or fixed expected-answer table supplies hinge truth.

## Returned facts

The `ontokin.c265.source-hinge-observation/0.1` result contains source hashes,
byte counts, canonical manifest/program revision, complete object and hinge
occurrence identities, separate definition identities, ordered endpoint site
records, signed basis axes, closed angular limits and initial coordinates.
Every hinge/site declaration and field expression has an actual source filename,
SHA-256 and integer UTF-8 byte interval. Keyed generation witnesses remain explicit.
Names define display paths; opaque literal keys define identity.

Endpoint `interface` and canonical `sizeM` equality is checked as a source-only
compatibility fact. Site pose expressions remain byte witnesses with
`poseEvaluated: false`; this component does not evaluate offsets or world alignment.

## Finite numeric and refusal policy

The six signed coordinate basis axes are admitted without normalization or sign
canonicalization. Angle literals support deg/rad; sizes support m/cm/mm. Exact
decimal values and exact unit factors are combined before a single binary64
rounding. Degrees use the contract's exact represented Pi64/180. Limits are
ordered, inclusive and not widened by a tolerance. Supported changed source
values, names, keys, membership and import aliases are derived from their bytes.

Unsupported expressions refuse the whole observation. A bare carriage-return
terminator inside a `//` comment is explicitly unsupported because the pinned
C257 lexer otherwise ends that comment only at LF. Normal LF and CRLF comments
remain supported; quoted text is not treated as a comment. `Fault.code` distinguishes
`MALFORMED`, `UNSUPPORTED_SOURCE_FORM`, `RESOURCE_LIMIT`, `INPUT_BINDING` and
`IO_ERROR`. Bounded supplied source hashes and byte counts are retained on
refusal; oversized input is not hashed merely to report a diagnostic. No partial
qualified set is returned. A valid expression outside this finite profile is
unsupported here, not redefined as invalid OntoKin.

## Verification and use

The [independent controls](test_source_hinges.py) exercise only the public API
and derive expected answers separately from the adopted rules and actual bytes.
Run from the repository root with a new evidence directory:

```sh
python3 -B docs/engineering/localized-repair-c265/test_source_hinges.py --evidence-dir /tmp/c265-new-run
```

Use the [requirements](../../workflow/tasks/C265/REQUIREMENTS.md),
[plan](../../workflow/tasks/C265/PLAN.md) and [input bindings](INPUTS.json) to
review the bounded scope. Results, review and integration are separate receipts.

## Remaining boundaries

This API establishes source-derived declaration facts only. It does not compare
an artifact, admit historical endpoints, prove full source validity, qualify
accepted revisions or atomic edits, evaluate site poses or physics, perform a
rebuild/native/model trial, complete C255 semantics or demonstrate authoring
advantage. The other C260 interfaces and their remaining controls are separate
work. Existing runtime behavior, budgets, fixtures and historical evidence are
unchanged.
