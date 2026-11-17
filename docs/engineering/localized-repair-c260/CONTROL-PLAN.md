# C260 independent implementation control plan

**Status: planned, unrun.** C260 delivers this plan and a fixed-input design
inspection. There is no hinge observer to execute these cases against yet.
These controls become required for the later implementation; no case below
is a current passing result.

## Independence and input construction

The reviewer must author expected field values and source associations from
the adopted rules and actual source bytes, without importing the new observer,
product compiler/evaluator/exporter, C255 oracle, producer semantic sidecar or
motion output. A small independent JSON/GLB fixture editor may change copied
metadata, preserving chunk alignment and size. It must not obtain its expected
hinge answers from the implementation being reviewed.

When source bytes change, update their exact import pin and canonical
program/source provenance in any deliberately paired artifact. Distinguish a
binding refusal from a field mismatch: for a source-only numerical control,
update necessary provenance claims while deliberately retaining the old hinge
field. That isolates the field comparison. Also keep a stale-provenance case
to verify binding refusal itself. A claimed successful paired change must
change actual source and actual metadata, not only an expected-answer table.

Use separate outputs for raw source observation, raw artifact observation,
comparison and historical byte admission. Record every input hash, exact
checked implementation revision, commands, outcomes and original failures.
Run no source evaluator, export, native application or model trial.

## Required controls

| ID | Independently constructed case | Required future outcome |
| --- | --- | --- |
| H01 | Both original frozen endpoint bundles and GLBs | Eight complete hinge rows each; one shared joint definition; sixteen source-associated endpoint sites; exact hashes admitted only by historical API |
| H02 | Change source `initial` to a supported in-range literal while retaining artifact initial after provenance rebinding | Source observer returns changed value; artifact observer retains original claim; comparison refuses disagreement |
| H03 | Change only artifact initial to an in-range different number | Raw claim visible; comparison refuses; historical admission fails bytes |
| H04 | Paired supported initial change with updated import/program/source bindings | Comparison passes changed value; historical admission refuses; no accepted-revision claim |
| H05 | Independent source-only, artifact-only and paired changes to each ordered limit | Actual changed fields drive outcomes; no baseline-value substitution |
| H06 | Boundary equality and zero-width limits, including initial at either endpoint | Inclusive canonical comparisons pass; out-of-range initial and reversed limits refuse |
| H07 | Equivalent signed deg/rad literals and canonical negative zero | Exact one-round Pi64 conversion; mathematically unequal or adjacent binary64 values refuse when mismatched |
| H08 | Six signed basis axes; paired axis reversal | Exact sign preserved, normalization identity; no axis-sign canonicalization or motion fitting |
| H09 | Source zero/nonunit/nonbasis axis, including a valid language nonbasis unit vector | Refusal; unsupported valid expression distinguished from malformed/invalid basis input |
| H10 | Artifact wrong axis length/type, boolean, NaN/Infinity, tiny nonzero replacement of source zero, or opposite sign | Refusal without normalization, tolerance or repair |
| H11 | Source parameterized/computed axis, limits or initial; typed Angle parameter with baseline-equivalent default | Unsupported-form refusal; original values never substituted |
| H12 | Paired joint lexical-name rename retaining key, then key change retaining name | Paths and definition/occurrence IDs follow their separate actual tokens |
| H13 | Source-only and paired endpoint-site name/key changes | Correct endpoint/site-definition association; no suffix or terminal-name guessing |
| H14 | Swap ordered endpoints, supply same-object endpoints, or bind one path to another object's site | No sorting; distinct-object requirement; mismatches refuse |
| H15 | Valid `self.SITE` and direct-part-site paths; private own part with public child site; inaccessible private external site | Supported lexical access passes; invalid/private access refuses |
| H16 | Unsupported origin endpoint, keyed endpoint traversal, deeper chain, computed SiteRef, scene joint or non-hinge joint | Typed unsupported-form refusal without dropped declarations |
| H17 | Duplicate/missing/extra joint fields or declarations; member/key collisions with sites/parts/implicit `origin`/`frame`; constructor shadowing | Ambiguity or unsupported binding refuses before expected values are produced |
| H18 | Site missing required field, nonliteral/empty interface, negative/computed size, unequal interface or canonical size | Explicit source compatibility refusal; pose expressions remain unobserved rather than evaluated |
| H19 | Reorder nonempty keyed input, insert/delete supported keys, direct final-membership override and legal keys containing dots/underscores/hyphens; then empty input and invalid Unicode/quote/overlength keys | Complete set derived from valid actual keys; no fixed count, order-based identity or naïve dotted-path splitting; empty input is unsupported and invalid keys refuse |
| H20 | Change unrelated source geometry or the original length parameter; independently change ownership/follow/motion metadata | No hinge values inferred from these fields; only explicit structural/source-binding obligations may refuse; no full-source or other-component pass is claimed |
| H21 | Missing/extra/duplicate joint rows, duplicate object identity, incorrect owning class or source span | Complete set/association refuses; node and joint-row reordering alone passes |
| H22 | Stale/missing/contradictory source hash, import digest, program manifest/revision, repeated node/source mapping or definition claim | Source/program binding refusal; display path alone cannot authorize comparison |
| H23 | Observe artifacts with no direct site/definition/span table | Missing direct authority remains explicit; derived site associations are never relabeled artifact fields |
| H24 | Truncated/misaligned GLB, duplicate JSON key, wrong JSON shape, excessive bytes/tokens/objects/hinges/sites/depth | Typed structural/resource refusal; no leaked host exception or partial qualified result |
| H25 | Long numeric lexeme/exponent, adjusted-exponent limits, overflow and underflow boundary | Bound work before numeric allocation; implement exact declared canonical policy or refuse explicitly |
| H26 | Historical file missing, wrong size/hash, symbolic link, symlink loop, path escape or permission error | Bounded typed I/O/admission refusal; no ambient/network fallback |
| H27 | Changed supported raw source/artifact supplied to first three interfaces | Inspectable as changed inputs; historical flag remains false and unrelated qualification flags absent/false |
| H28 | Nontrivial site pose/geometry or motion change that leaves observed hinge fields equal | Explicitly remains outside this declaration comparison; successful field agreement cannot claim endpoint world alignment or physical validity |

## Review acceptance

Review the code's actual field paths, lexical/name/key handling, numeric
conversion, error boundaries and dependency admission in addition to executing
the cases. Cases may require multiple independent assertions; reporting a
single high count cannot replace their coverage or recorded failures. A future
implementation may use extra tests to resolve a concrete finding, but may not
weaken the frozen comparison policy or expand its advertised support without
a reviewed version change.

Keep schema/contract validation, fixed-input inspection, implementation tests
and real product/trial qualification separate in all reported results.
