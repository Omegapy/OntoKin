# C063 independent diagnostic-stack integration review

Date: October 28, 2026, America/Denver. Reviewer: `/root/integration_review`.

## Review method and boundary

This review used read-only authenticated GitHub file, tree, ref, and pull-request reads. I read AGENTS, GOAL, STATUS, OK-ENG-009, the C060/C061/C062 handoffs, C062's proposed C063 task, the three live PR descriptions and changed-file inventories, diagnostic entry points, and retained tooling/integrity reviews. I independently compared both complete, nontruncated remote tree listings and read both workflow definitions.

I ran no product request, unit suite, auditor, calculator, archive construction, repository mutation, or lease action. This document is the only local file I authored. Earlier execution outcomes discussed below are retained evidence that I read, not executions performed by this reviewer. The source inspection covered integration scope and tool entry boundaries; it is not a claim to have independently rederived every condition in the full diagnostic implementations.

## Disposition

The C060 -> C061 -> C062 stack is suitable for a bounded diagnostic/evidence integration review. No product runtime change, altered workflow trigger, deleted historical source, or activated held optimization was found in the cumulative remote-tree comparison. The failed documentation gate remains a prerequisite until a fresh unchanged checker actually passes in the identified complete checkout.

The coordinator subsequently reported recovery of all twelve historical archives through authenticated raw URLs returned in Contents-directory metadata, with exact Git-blob and size verification totaling 74,915,834 bytes, and reported that complete-checkout materialization is in progress. I have not independently inspected those downloaded bytes. The coordinator's recovery inventory and actual checker receipts must establish those results separately.

## Independently observed source scope

| Pull request | Checkpoint | Observed head | Dependency |
| --- | --- | --- | --- |
| #58 | C060 | `00533b953ed345cbf5fa13eaa56aafa3a2f052a8` | Main `b37b39102aea67eb81bd9e38518352403a844e99` |
| #59 | C061 | `e5e99b92e4efa541b434abcdda5c2ec31dda6a39` | C060 |
| #60 | C062 | `995ab0a46131a99b12e939b43bfb25e44287f442` | C061 |

All three were open drafts when inspected. Main remained at the commit above. These are time-bounded observations, not permanent assertions about refs.

The independent cumulative tree comparison established:

- Main contains 3,327 tracked blobs; C062 contains 3,458.
- The stack adds 131 paths, modifies only the preexisting `docs/README.md`, and deletes no paths.
- All 65 `ontokin/` files retain their main Git blob identity and mode.
- Both workflow files retain their main Git blob identity and mode.
- Actual workflow definitions use only `workflow_dispatch`, set `enable_hosted_ci` to false by default, and gate hosted jobs on that value being true.

C060 adds the original-request probe, collector, and independent auditor. C061 adds a separate setup collector and auditor. C062 adds its offline calculator and historical receipt runner. These tools are not connected to existing product routes. All existing tests, fixtures, runtime files, limits, and workflow files are unchanged by this cumulative stack.

## Applicable development gates

Under OK-ENG-009, the relevant scope is standalone diagnostic tooling plus preserved evidence and navigation. The executable tools mean the entire stack should not be described as prose-only. The applicable changed-behavior evidence consists of the original executed diagnostics, independent audits, intended corruption rejections, calculation, and their exact source and archive identities.

A complete legacy product-suite rerun is not automatically required for this cumulative change: it changes no released runtime machinery, existing invocation routes, fixtures, or tests. The previously agreed scope conclusion remains unchanged. A fresh alteration to those inputs would require a separate scope assessment.

Before integration, the coordinator must establish exact archive recovery and complete checkout identity, an actual pass of the unchanged preservation/navigation checker, the diagnostic evidence and final tool identities, and the cumulative equality of unaffected inputs. The exact earlier successful audits and negative controls remain attributed to their recorded source revisions; a publication or merge must not relabel their executed revision.

Integration requires a fresh bounded main lease, dependency reconciliation, protected or expected-head operations, actual resulting commit/tree verification, and the applicable resulting-main documentation check. Eligible input equality must be established wherever candidate evidence is reused. This review adds no new testing requirement beyond the agreed diagnostic/evidence scope and repository integration procedure.

## Execution and portability cautions

C062's `run_checks.py` is a historical executor-specific receipt runner. It computes paths for `c062-documentation-base` and `c062-work/final-checks` from its former layout and executes at module top level. Preserve its bytes as the source of the retained receipts. Invoke the calculator and unchanged documentation checker directly with current explicit paths for fresh C063 checks.

C060 and C061's auditors bind original absolute source/evidence locations and Git objects. Their retained successful audit receipts remain meaningful. Copying evidence to a new directory does not make an unmodified audit invocation portable. Preserve historical receipts unchanged; do not claim a relocated replay unless its original identity conditions or a separately reviewed relocation procedure are satisfied.

C061's auditor loads its unchanged C060 dependency only after checking SHA-256 `5a1ece268ba6f8bf71f2f62fbe2963da34175280797ec66be668261b2886b0cf`. Keep that dependency unchanged. The auditors check offline evidence; their success does not accept retained GLBs, complete a failed request, or certify a product release.

## Dependency order and retained obligations

Resolve C060 first, then C061, then C062. After base integration, reconcile successor dependencies against actual main before retargeting or merging. Keep the index-only `archive/pre-consolidation-20261028` branch outside all development and merge paths.

The diagnostic integration does not change historical original28's 24/28 failed result, unresolved P11/P16/P23/L03, rejected M1, held C035, incomplete LFS payload migration, or the remaining reach release and destination obligations. It introduces no runtime optimization or newly successful recording. Retained reader-input GLBs remain unvalidated.

If archive recovery or another applicable gate remains blocked, C063's finite scope requires publishing the exact prerequisite and stopping that scope. It does not permit weakening the checker, substituting fabricated archive bytes, or beginning another performance loop.

## Primary reviewed references

- [C063 proposed scope](https://github.com/Omegapy/OntoKin/blob/995ab0a46131a99b12e939b43bfb25e44287f442/docs/engineering/reach-recording-validation-2026-10-28-c062/NEXT-TASK.md)
- [Development integration policy](https://github.com/Omegapy/OntoKin/blob/995ab0a46131a99b12e939b43bfb25e44287f442/docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md)
- [C060 PR #58](https://github.com/Omegapy/OntoKin/pull/58)
- [C061 PR #59](https://github.com/Omegapy/OntoKin/pull/59)
- [C062 PR #60](https://github.com/Omegapy/OntoKin/pull/60)

After writing this review, I pause all operations. No reviewer process or transfer is running. The coordinator owns the subsequent exclusive offline checks and publication decisions.
