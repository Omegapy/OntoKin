# C272 reconciliation of the C269 audit with C270 and C271

This record serves TASK-009 and REQ-009. It reconciles the four groups that the
[C269 audit](../localized-repair-c269/AUDIT.md) left partial with the evidence recorded after it.
For each group it states whether a check of this workflow depends on the property concerned.

C269's counts were 24 complete and four partial groups, and 94 complete and five partial
subcases. They are **the audit's result at its baseline**
`23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb`, an evidence-only audit with no new run. They are
not a fresh audit, and this record does not recount them. No group becomes complete here by
inference from one new control.

## Inherited and new results

**Inherited** results are those of C269, C270 and C271, cited at their own revisions. The only
**new** result so far is the observer baseline on this host:
[RESULTS.json](evidence/observer-baseline/RESULTS.json). It ran at `539cbfe1`, whose observer
files equal main `38ee8d18`'s, with CPython 3.12.13 on macOS 26.6.2 arm64. All 12 groups
passed with 282 methods, and a repeat run gave the same outcomes and counts. Earlier records
of these groups were on Linux only.

## The four groups

| Group | C269 finding | Later evidence | Present state | Does this workflow depend on it? |
| --- | --- | --- | --- | --- |
| H16, unsupported endpoint and joint forms | A source-valid declared or computed `SiteRef` was not exercised with an exact unsupported-form assertion. | C270 ([PR272](https://github.com/Omegapy/OntoKin/pull/272), merge `4d27756f`): the observer refuses an accessible, explicitly declared `SiteRef` parameter as `UNSUPPORTED_SOURCE_FORM`. C270 records that no broader H16 qualification follows. | Partial for C260. The declared form is covered; computed forms are not. | **No.** The three cases' sources are the frozen closures, and they contain no `SiteRef` parameter; C255's source-byte check refuses any other source. No check of this workflow depends on how the hinge observer treats a `SiteRef`. The gap stays open for C260. |
| H20, unrelated-field independence | Some source-invariance expectations came from the observer itself; comparison mutations bundled unrelated fields and did not exercise each ownership, follow and motion field separately. | None recorded. | Partial. | **Yes.** V1 and V2 change exactly the original length parameter that H20 names, and this workflow uses the C267 hinge comparison on the edited outputs. The workflow's expected fields come from C255's independent formulas, not from an observer. The missing part for this workflow is the isolated changes: one ownership field, one follow field and one motion field of a delivered artifact, each changed alone. It is added as a control of this workflow in TASK-020. |
| H22, source and program provenance | An isolated removal of the actual source import digest, with its retained outcome, was not found. | C271 ([PR279](https://github.com/Omegapy/OntoKin/pull/279), merge `417b89b8`): the H22.02 isolated missing-digest control, documentation only; 6 inputs, 18 interface calls, 12 exact `MALFORMED` refusals. Its phases P02 to P38 did not merge. | H22.02 covered at C271's revision; group H22 is not reported complete by inference. | **Yes, through the workflow's own provenance checks.** Every case binds the exact source closure, and the service resolves the import against its pinned digest. TASK-021 presents a missing or changed dependency pin to the workflow and expects a rejection, beside the stale-provenance faults. C271's control is cited and not rerun. |
| H24, structural and resource bounds | No supplied excessive-site input with its actual typed outcome. C269: "The remaining obligation needs an explicit decision or a bounded additional control." | None recorded. | Partial. This record takes no H24 decision for C260. | **Yes, for this workflow's own new metadata reader** (GAPS.md, G3). That reader parses delivered site, action and event tables. It gets bounds and typed refusals, with a bounded control: an excessive-site table, a duplicate JSON key and a truncated GLB, each refused with a typed fault and no host exception (TASK-020). The existing hinge observers' excessive-site case stays open for C260, because no check of this workflow sends them more sites than the frozen family has. |

## What this does not establish

The residual controls of this workflow (TASK-020) qualify its own checks on the three frozen
cases. They complete no C260 group and do not qualify C260. H16 and the hinge observers' part
of H24 stay open with the reasons above. Nothing here becomes a separate documentation-only
milestone.
