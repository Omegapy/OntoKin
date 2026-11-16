# C253 executed results

## Reviewed source and actual checks

The initial author was `b8d13dfff041c355fbef2b0359a9c886bee7d843`.
Independent review held it for four focused corrections, including eight false
acceptances among 20 static-validator fault controls. Those original failed
observations remain in the handoff; they are not overwritten by the correction.

Corrected local source `8c15fce161f7081fb9d73d07f86698dc74bad27a`, tree
`42cdde35736fd6f4ab5071b774df8cd861ba6720`, is independently approved.
It was published for PR review as the distinct equal-tree commit
`c46a1a21924dba2ef6b41864168d675f94cf48cf`.
[PR #236](https://github.com/Omegapy/OntoKin/pull/236) and
[scope #235](https://github.com/Omegapy/OntoKin/issues/235) record integration
and handoff closure separately. Equal trees do not make local commits remote
ancestors.

| Executed check | Observed result and scope |
| --- | --- |
| Static corpus verifier | 14 exact committed files; two-source dependency closure; three literal-edit cases; 18 identities and 16 unrelated objects; original times/tolerances bound. |
| Independent adversarial verifier controls | 20/20 named faults rejected after correction; ordinary valid manifest still passes. |
| Independent formula consistency | 252 pose rows across both length states and 18 original geometry records agree; maximum observed pose-component difference 1.11e-16. No product/runtime calculation supplied these expectations. |
| Exact corrected-source documentation | 29 preserved sources / 5,267 local links, zero failures; clean unchanged checkout. |
| Published initial candidate security check | GitGuardian success on c46a1a21924dba2ef6b41864168d675f94cf48cf; no workflow run observed for that head. This is not a product/compatibility check. |

The interpreter is CPython 3.12.14 on Linux x86-64. Checks ran as static source,
JSON, mathematical and documentation work. No product, parser, native,
aggregate or model-trial workload ran. No existing runtime module, historical
fixture, expected value, tolerance or workflow was edited.

## Decision and preserved limits

The [review](REVIEW.md) approves only this protocol and its static bindings.
One public family supports qualification of a future evaluator. Model snapshot,
full baseline dependencies, equivalent route seeds, native readers and runner
remain unqualified. Unseen evaluation families and a prospective sample-size
justification are required before a general comparative claim.

The next scope is the [offline oracle component](NEXT-TASK.md). Godot R07,
comparative R08, strict Blender-normal failure, all nine C221 records / 41
criteria and held C251 drafts retain their states. The root integrator must
verify actual resulting main, release its lease and confirm the standalone
handoff save. Final publication/closure receipts are retained in that handoff's
`evidence/publication/` directory and durable recovery checkpoint.
