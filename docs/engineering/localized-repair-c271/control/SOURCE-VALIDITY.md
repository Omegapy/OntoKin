# C271 independent missing-import-digest control

**Oracle status: predeclared; no observer invoked by the author.** This control
addresses only the missing actual source import digest in C269 H22.02. It has
two positive baselines and four negative cases. Each negative deletes one
contiguous byte range from an original entry source. The companion source and
GLB remain the exact historical bytes.

## Authority and classification

[OK-LANG-002 section 3.1](../../../language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md#31-entry-program-and-definition-modules)
requires the adopted import syntax. Its
[construction grammar, `import_decl`](../../../language-design/construction-v0.1/ontokin-construction.ebnf)
requires the sequence `"version", STRING, "digest", STRING, ";"`.
Neither `digest` nor its following string is optional.
[Section 3.2](../../../language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md#32-exact-closure-and-content-identity)
requires an exact source digest and resolves it against the supplied dependency
bytes. It prohibits an ambient, cached or fetched replacement.

The unchanged [C260 contract](../../localized-repair-c260/CONTRACT.md),
sections 2, 3.1, 5 and 6, requires the pinned source closure before association
or comparison. It requires typed refusals and distinguishes malformed input
from a valid source form outside the observer's supported subset. The
[control plan H22](../../localized-repair-c260/CONTROL-PLAN.md) requires source
and program binding refusal when a source import digest is missing. The
[C269 H22.02 coverage record](../../localized-repair-c269/COVERAGE.json)
identifies the absent isolated deletion case; it supplies no expected output
for these new inputs.

Both deletions are **malformed source syntax**, not valid unsupported
expressions. They are also distinct from a missing import statement, a missing
dependency file, a stale but present digest, and an empty quoted digest string.
The import alias, declaration key, package, version and terminating semicolon
remain present. The frozen exact refusal code is **`MALFORMED`** at source
observation, source/program binding and hinge comparison. The Director
confirmed only this public code spelling from the C265 and C266 README API
descriptions; that confirmation supplied no implementation behavior or
observed outcome. The normative category was selected first from the grammar
and C260 refusal requirements.

A different code, an untyped host exception, a successful return, or a
qualified partial hinge result contradicts this oracle. Exact diagnostic
wording is not prescribed. A contradiction must be retained without changing
the oracle or repairing the implementation in this phase.

## Exact inputs and isolated changes

[EXPECTED.json](EXPECTED.json) records every actual source/artifact path,
byte length, SHA-256, candidate program manifest and revision. The five
historical inputs match [C260 INPUTS.json](../../localized-repair-c260/INPUTS.json).
The published scope supplied to the worker is
`c27609ebab7c86ff20d7bd288994b49e3dd3c7e1`, based on main
`e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`; these are assignment provenance,
not a claim that the worker read a live remote head.

| Variant, applied independently to `before` and `after` | Exact deletion | Resulting entry bytes | Expected result at each of the three source-consuming interfaces |
| --- | --- | --- | --- |
| `baseline` | None | 1,708 | Success with the independently declared baseline hinge set |
| `missing_digest_clause` | Bytes `[217, 297)`: `digest` plus one space plus the complete quoted digest string | 1,628 | Typed `MALFORMED` refusal; no successful/qualified partial result |
| `missing_digest_value` | Bytes `[224, 297)`: only the complete quoted digest string | 1,635 | Typed `MALFORMED` refusal; no successful/qualified partial result |

Offsets are zero-based half-open UTF-8 byte offsets in the unchanged original
entry. The complete removed text and its hash are recorded for each case.
The first variant leaves the original indentation followed by `;`. The second
leaves `digest ;`. Original newlines, indentation, semicolon and every other
entry byte remain exact. The entry's comment describing a pin is deliberately
left unchanged because it is outside the targeted deletion; a comment supplies
no import pin.

The two variants exercise distinct mandatory grammar terminals. Repeating
them for both original endpoints keeps each refusal adjacent to its own
unchanged positive baseline. The endpoints differ only in the historical
length override; no additional hinge, provenance or resource case is added.

The GLB is intentionally not rebound after the source deletion: the task
requires the historical artifact to remain unchanged. Its old entry-source
claims would also become stale if source parsing could proceed. That does not
weaken the primary check: the source-only call must first demonstrate the
missing-digest refusal, and binding/comparison must propagate that same exact
typed refusal. An unchanged artifact cannot repair malformed source syntax.

## Independent baseline derivation

The entry's `first` rack takes the helper's literal keys `lower`, `middle`,
`upper`. The final direct `second.mounts` override supplies `bottom`, `lower`,
`middle`, `upper`, `top`. Thus there are eight Finger occurrences. The supplied
`hinges.ok` declares one `flex` hinge on Finger, using `self.pivot` followed by
`self.blade.base`. Each Finger owns one distinct Blade, so the source contains
eight hinges, sixteen associated endpoint sites and eighteen objects including
the two racks. The joint and site occurrence IDs follow C260 section 3 and
OK-LANG-002 section 3.3; the oracle lists them explicitly without relying on
row order or rendered display paths.

The shared literal axis is `(0, 0, 1)`, already a unit basis axis. C260 section
4.2 specifies one-round conversion with the exact binary64 Pi64. Consequently
the signed limits are `-0x1.921fb54442d18p-1` and
`0x1.921fb54442d18p-1` radians, and initial is exact zero. Both endpoint sites
declare interface `hinged.part` and size `0[m]`. The before/after length
override does not enter any of these hinge values. Site poses are recorded
source expressions but are not evaluated or qualified here.

## Construction, verification and independence

[construct.py](construct.py) uses only the Python standard library. It reads
the five pinned historical inputs and the listed specification/audit files;
it does not read, import or execute the C265–C268 observers/tests, product
parser/evaluator/exporter, or their outcome logs. The author inspected only
the C269 gap and audit context, not observer execution logs. No producer
sidecar or expected-record corpus supplies a hinge answer.

The script checks the five original identities against the unchanged C260
manifest, finds each exact unique deletion target, preserves the prefix and
suffix, and reconstructs the original by reinserting the removed bytes. It
independently computes candidate program identity using the canonical
manifest algorithm in OK-LANG-002 section 3.2. That identity names malformed
candidates before parsing; it is not an assertion that the candidate resolves.

Run the static verification from the repository root:

```sh
python3 docs/engineering/localized-repair-c271/control/construct.py --check
```

The initial `--write` creates missing fixture/oracle files only and refuses to
overwrite different existing bytes. The [static report](STATIC-CHECKS.json)
records reconstruction checks and environment details. These checks establish
input isolation and reproducibility, not an observed refusal. The Director
must freeze/publish the oracle before running the unchanged observers.

This author owns only `control/**`. No Git/index, task-state, CURRENT, STATUS,
observer, dependency or historical file was changed. No integration, complete
H22/C260 qualification, accepted revision, source execution, export, native
trial or comparative result is claimed.
