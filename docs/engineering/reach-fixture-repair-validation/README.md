# Reach fixture repair: focused verification

This checkpoint repairs the two test defects retained in
[attempt 005](../reach-runtime-validation/README.md#attempt-005--independent-reference-and-reader).
It is not a source/Agent rerun or a reach release result. The full OntoKin goal
remains open.

## Scope and identities

The isolated branch `work/reach06-test-repair-20261020-2008-7of9` starts from
combined implementation `1ed885c930da4adcb590d35f400b72dac57f9f74`, tree
`1f83adddf323131b9d2e3e6f85ca6a1600af218a`. Its owner is
`interactive-reach06-test-repair-20261020-2008-7of9`.
Only two existing test methods change. New fixture checks, a test helper and
this separately identified evidence are added. Runtime files, frozen source
fixtures and expectations, budgets, historical evidence, workflows, main and
STATUS are unchanged. The original worker branches and PRs remain intact.

## Corrected defects

**LP02 source evidence.** `ProgramBundle.sources` supplies diagnostic `Source`
objects, not package-bearing `SourceUnit` records. The test used the former's
nonexistent `package_id` and `version` attributes. The new
[source identity helper](../../../tests/reach_fixture_support.py) reads
`ProgramBundle.units` and verifies returned UTF-8 bytes, revision and filename
before reporting the unit's package identity. It does not add fabricated
attributes to diagnostic objects or weaken the expected source identities.
All nine principal LP02 requests, its ten prescribed additional evidence reads,
four untouched sibling comparisons and the overall 42-step inventory remain.

**Stop/replacement rounding witness.** The additional, non-frozen L02 variant
used duration 3 and stopped at 0.5 seconds. Both correctly rounded target
coordinates have a numerator divisible by 3, so dividing them by 6 is exactly
representable in binary64. There was no rounding discrepancy for that test to
observe. Duration 5 gives target/10 instead. The exact discrepancies are
`-1/360287970189639680` and `-1/90071992547409920` radians. The existing reference
test now checks that its actual admitted targets produce a nonzero discrepancy
before checking continuous ideal state and replacement slopes. The frozen L02
source, canonical targets, expected limits and numerical tolerances do not
change.

## What actually ran

The [report](report.json) and [raw log](tests.log) record **11 passing methods**,
zero failures/errors/skips/expected failures, eight parsed Python files and
unchanged before/after input hashes. The interpreter is CPython 3.13.5 on Linux;
the exact command, working directory and platform are in the report. The three
production modules used by these checks were recovered through the connected
GitHub API and verified against their actual upstream Git blob hashes.
No compiler, evaluator, Agent service, SQLite workflow or delivery adapter was
substituted with a stub and called a passing runtime test.

These checks exercise real source-bundle identity objects, exact arithmetic
preconditions, mismatched revisions/names/bytes, UTF-8 and line-ending
preservation, and nonmutation of evidence inputs. The transport-only unit
inputs deliberately do not claim to be executable `.ok` scenes. They validate
the new helper and rounding witness, not the full source/action implementation.

Reproduce this focused check from a complete checkout with an unused output
path:

```bash
python3 docs/engineering/reach-fixture-repair-validation/run_focused.py --output /tmp/ontokin-reach-fixture-check
```

The runner checks the declared production blob identities, records actual
arguments and rejects an existing output directory to preserve earlier runs.
A later production change requires a separately identified verification run,
not silent reuse of this evidence.

## Required next execution

The execution container had no previous checkout and could not resolve
`github.com`; authenticated connector reads/writes remained available. This
allowed verified recovery of the small input subset, not a complete compiler
and service environment. The two corrected integration methods have therefore
**not been rerun** here. Do not turn attempt 005 into a passing result or merge
the complete reach release on this evidence.

In the complete combined checkout, apply the child patch and run:

```bash
PYTHONPATH=tests python3 -m unittest -v test_reach_reference test_reach_agent_protocol_cases
python3 -m unittest discover -s tests -v
```

Then continue the writer arithmetic and independent impulse-history work,
actual source/Agent GLB delivery, hostile-byte probes, Khronos/Three/browser
checks, visual review, compatibility, inherited roles and all R01-R12/Q01-Q22
release obligations. Agent/0.6 delivery remains unavailable. Main integration
still requires a current-head review, a verified lease and resulting-main
checks. No hosted workflow was dispatched or retried by this continuation.
