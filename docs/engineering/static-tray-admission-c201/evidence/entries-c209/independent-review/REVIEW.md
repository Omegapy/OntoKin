# Independent C209 component review

**Decision: APPROVE_EXACT_ENTRY_BINDING_COMPONENT_ONLY**

Reviewed exact candidate `d5d02cfadfcd549d527e7699224ff07aa389d4be` against baseline `160d8ebfe8acf47c0f487340baacd10f20364b2a`. The cumulative diff adds only `readback_entries.py`, its focused test module and `READBACK-ENTRIES-C209.md`. It changes no prior product, runtime, test, workflow, frozen protocol or historical evidence file. No product repair was required.

## Evidence and controls

All **42 independent controls passed**, with zero failures, errors, skips or attempted child starts, in **6.947 seconds**. This was one complete clean independent batch. Full results are `initial-controls/RESULT.json` and `initial-controls/controls.log`. The fixture package inventory and adversarial assertions were prepared independently from the baseline transaction fixture and announced API, then reconciled with the frozen contract before their first execution. No failed independent run is omitted.

The controls cover metadata identity/version/selectors and duplicate keys; package-root ambiguity and cross-root metadata substitution; required direct graph edges and wrapper reachability; actual file mutation, symlinks and hardlinks; explicit bare/relative import mapping; absent edges and ambient/URL/encoded/extension inference rejection; new job authority flags, exact written bytes and copy isolation; unchanged legacy `/0.1` job schema and field set; and rejection of a new handle by the old result verifier. Every rejection checks all four actual accepted-pointer files before and after the operation.

`REVIEWED-INPUTS-initial.json` binds **605 files**, including the affected prototype sources, prior tray helpers, all tracked runtime and test files, relevant contracts, and both independent control scripts. `CURRENT-INPUT-EQUALITY.json` confirms those exact bytes remained unchanged after the controls. Candidate Git tree and actual Linux/Python identity are in the manifest. Other agents use this same runtime; no separate host or platform is claimed.

## Findings and practical limits

The implementation checks exact package membership and metadata, fixed named entry paths, independently sealed closure identities, required direct graph relationships, and the actual helper bytes. It reuses accepted-source validation without modifying the existing C208 implementation. Reinspection reconstructs the expected job and checks both retained and on-disk job bytes. Entry preparation preserves the existing output directory and accepted-pointer boundaries; its failure/unknown handling stops that in-memory session.

The three entry paths match the retained historical mapping, including the deliberate `build/three.webgpu.js` target. Metadata selector requirements are explicitly new compatibility constraints. This review used synthetic metadata and JavaScript fixtures, so real package compatibility and runtime APIs remain unverified. A future host seal must inspect actual dependencies; a mismatch is a named blocker, not permission to change historical evidence.

The declared Node subgraph and CPU resolver are not an actual Node import interceptor. They neither discover all JavaScript dependencies nor stop a different program from importing other files. The contract states this distinction accurately. Explicit bare `three` is a fixed graph-bound alias; there is no ambient search. All start/readiness/admission/authenticated-execution authority remains false. No `/0.2` result verifier, wrapper/probe execution or coordinator is supplied by this increment.

## Applicable integration checks

For this exact isolated diff, the proposed inventory is sufficient: all 223 existing C201 methods plus all 61 new methods; 78 source/compiler methods; 43 core conformance cases / 694 assertions; documentation preservation/link checks; and preservation of the 301 historical locked inputs and four frozen protocol documents. These integrator checks were pending when this component review was issued. Full default unit discovery is not required merely to repeat the inherited full-suite failure for an unchanged runtime. Reassess the inventory if shared code changes, a previously passing obligation fails, or an unexplained effect reaches released behavior.

The inherited full regression stays **FAILED**: 4,239 distinct passing methods and 13 torque-read methods not run. C208's actual-main promotion timeout and separate successful rerun remain separate records, with cause unproven. This review neither repairs nor relabels those results. Integration must still use fresh observed ownership/refs, the expected-head lease procedure, and applicable resulting-main checks.

## Exact next bounded action

Implement and independently review a **CPU-only `/0.2` result-compatibility component**. It must bind the exact extended job and entry evidence while retaining C208's accepted-source, process/probe, complete numerical, failure and uncertainty requirements. Continue to hold actual wrapper/probe execution, host sealing, native readiness and admission behind their separate gates.

To rerun these independent controls against a restored exact source checkout, place `fixture_support.py` beside `independent_controls.py`, set `PYTHONPATH` to that checkout and this review directory, then run Python3.12.14 with `-B independent_controls.py --source <checkout> --output <new-results-directory> --candidate d5d02cfadfcd549d527e7699224ff07aa389d4be`. Do not reuse the historical result directory for a new observation.
