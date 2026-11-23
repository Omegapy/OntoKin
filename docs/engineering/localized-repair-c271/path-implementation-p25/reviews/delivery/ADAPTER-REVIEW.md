# Independent P25 adapter acceptance

Reviewer: `/root/reconcile`, who authored neither the adapter nor production
implementation. **Accepted for the bounded P25 synthetic/mocked controls.**

The accepted adapter is `ADAPTER-005.py.source`, **71,062 bytes**, SHA-256
`363bfb5c3b7dbb40410412cafb1aa453e966aebdd79b55efabcda1a2572ca0da`.
The retained `attempt005` binds production candidate001, SHA-256
`eea3e6343ae34d9c930a810ca4f363cbcd4264a8d943731f927e41b213755d7a`.
The final live adapter, frozen adapter and attempt copy are equal. The runner
source is also bound and preserved in that attempt.

## Findings and resolution

Three mandatory findings from `ADAPTER-REVIEW-001.json` are resolved:

| Finding | Final assertion |
| --- | --- |
| A01: new path diagnostics could omit their required stage or use an unrelated rule | Required `rtld_paths` stage, closed details, mapped rule and category are checked. Legacy diagnostics and outer drift wrappers remain distinct. |
| A02: positive proof assertions did not establish the physical parent step and i386 link order | Traces retain the input basename and held physical parent. P01/P04 require the admitted `..` step from `/usr/lib64` to `/usr`; P03 checks `/lib -> usr/lib` in both root passes. P02/P03 check the exact repeated missing-basename lookups. |
| A03: race evidence could satisfy a generic distinct-identity count | F05–F07 require the exact original and changed tuples for the declared same path. F12 requires all four labelled canonical-file identities and its completed binding. |

The corrections strengthen the predeclared obligations. They do not alter the
P24 matrix, crosswalk, schema, accepted design, mutation inputs or expected
categories. Earlier adapter freezes and observed runs remain preserved.

Two additional evidence corrections preserve the initial proof and initial case
input by copying them before later faults can change their data. This matters
for F08's later creation of `/libx32`: the retained initial fixture still records
that entry as absent. These changes do not modify production behavior.

## Case coverage and observed evidence

All **52 frozen obligations** were reviewed against the accepted P24 design,
schema, matrix and crosswalk. The adapter contains **51 generated named methods**:
five positives, 33 runtime refusals and 13 injected faults. N34 remains the
separate external source-completeness obligation, with operational adoption
withheld; it has no runtime method or skip. Historical N57 is unchanged.

Ten separately declared supplemental methods address concrete contract risks:
close failures, combined callback/cleanup evidence, partial reads, exact snapshot
and guard exclusions, preserved libc dispatch, proof-before-alias ordering,
launch-clock handling, and closed shape/physical-guard relations. They were read
in full and do not replace any frozen control.

The final retained run reports **61 passed, zero failures, errors or skips**.
The independent `ADAPTER-EVIDENCE-AUDIT.json` records **37 passed checks** and a
case-by-case assessment of all 51 runtime records. Every record preserves its
exact frozen case/crosswalk, expected initial mutation and fault, category,
process-count distinction, bounded descriptor use and cleanup. New path error
reasons/categories also match the adopted schema. The saved log contains exactly
the 51 named frozen methods and ten supplemental methods, each with an `ok`
outcome. No test was rerun by this reviewer.

The F09 result retains one **mocked** prior Node outcome and start receipt while
rejecting later success. Actual target counts remain zero in every retained
record. The controls supply no operational plan admission, `STATIC_READY`, H0/H1,
host readiness or full-routine claim.

## Read coverage and limits

The full accepted design, schema, adoption and final runner were read. All matrix
and crosswalk content was read using exact common-field reuse; the read packets
reconstruct every original case exactly. The final adapter was read through the
complete version002 text and every subsequent change through version005, with
unchanged bytes reused. All final case records were parsed and checked; relevant
faults and trace semantics were reviewed. Complete arbitrary raw syscall traces
were not all reread. Production bytes were hashed only to bind the observations;
production implementation review belongs to `/root/controls`.

One audit-only parser initially expected unittest's result on the method line;
these named tests put their docstring and result on the next line. The original
audit report and script are preserved. Correct parsing resolves that single
audit failure, with no test or oracle change. An intermediate F06 display
truncation was repaired by reading its complete final diagnostic separately.
There is no remaining required read gap or unresolved mandatory adapter finding.

Machine-readable acceptance: `ADAPTER-REVIEW-002.json`. This review accepts the
bounded adapter and its retained synthetic/mocked evidence only. It does not
accept main integration, parent completion or a future operational H0 plan.
