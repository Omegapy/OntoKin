# C212 evidence and limits

**Selected outcome:** completed investigation and explicit rejection of an unsupported tolerance increase. The original strict normal promise and held receiver remain unchanged. [Versioned decision](DECISION.md)

## Independent retained-data measurement

A new Python standard-library GLB decoder reads the retained input without importing OntoKin or the receiver. It pairs complete oriented position triples, permits only cyclic rotations, consumes every observed triangle once, and refuses ambiguous geometry. It checks complete object/corner inventories and finite vectors. [Script](evidence/analysis/recompute_c211_normals.py), [result](evidence/analysis/normal-remeasurement.json)

| Observation | Result |
| --- | --- |
| Objects | 18 |
| Exact triangle positions and winding | 7,800 / 7,800 |
| Normal failures at unchanged `2e-6` | 7,088 triangle instances / 14,880 corner occurrences |
| Maximum raw component error | `0.0001531541347503662` |
| Maximum normalized component error | `0.0001531602804677734` |
| Maximum direction error | `0.00015615850038545062` radians |
| Independent failing source meshes | One sphere mesh, repeated eight times |
| New Blender/native processes | Zero |

Thirteen synthetic CPU controls validate correspondence, relocation, winding/inventory refusal, finite vectors and exact/adjacent-float threshold behavior. They pass without altering retained inputs. They validate this measurement method, not native receiving compatibility. [Control harness](evidence/analysis/check_normal_remeasurement.py), [control results](evidence/analysis/normal-self-check.json)

## Native source investigation

All 118 installed executable/importer file bindings match the retained C211 manifest. The actual importer supplies custom normals with vertex merging disabled. Official pinned upstream source uses signed-short angular encoding, approximate inverse cosine and deliberate shortcuts. This supports a lossy native representation explanation. Exact binary-to-source provenance and causal replay remain unproved; there are no internal native fan/short-pair observations. [Binding results](evidence/installed-binding-check.json), [source hashes](evidence/upstream-sources.json), [scale calculations and exclusions](evidence/codec-scale-calculation.json)

Complete source snapshots, original worker reports and their file inventories are retained in the C212 handoff. The source URLs and hashes here permit independent retrieval. Upstream source headers remain in those snapshots; none of that source is incorporated into OntoKin's runtime.

## Reproduce the retained-data checks

From the repository root, create an output directory outside the checkout, decompress `docs/engineering/semantic-receiving-c211/evidence/native/import-observations.json.gz` there with Python's `gzip` module, then invoke the analysis and control scripts with explicit paths:

```bash
python3 docs/engineering/normal-fidelity-c212/evidence/analysis/recompute_c211_normals.py --glb docs/engineering/semantic-export-c210/evidence/proof/after.glb --observations /absolute/output/import-observations.json --output /absolute/output/normal-remeasurement.json
python3 docs/engineering/normal-fidelity-c212/evidence/analysis/check_normal_remeasurement.py --glb docs/engineering/semantic-export-c210/evidence/proof/after.glb --observations /absolute/output/import-observations.json --output /absolute/output/normal-self-check.json
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

The expected measurement is the historical failure, so successful analysis execution does not mean a receiving pass. The scripts and inputs carry SHA-256 bindings. Source revision, environment, commands, logs, candidate/main documentation results and independent review are recorded in the publication evidence and final handoff.

## Scope of verification

C212 changes current documentation, a decision and offline evidence only. Compiler, runtime, Agent, GLB writer, receiver, fixtures, tests, workflows, dependency inputs and historical evidence are unchanged. Therefore the required repository check is the documentation preservation/link checker, plus executed analysis-method controls. A new full product regression or native/visual run would not validate this decision-only change and was not selected.

Historical C211 affected checks passed, but its broader run remains interrupted: 1,476 observed passes and 3,205 methods without outcomes. C210's failed broad result and earlier failures remain failed. C211 rendering failed; native save/reopen/visual gates were not reached. The held rendering correction remains unexecuted. [Original receiving results](../semantic-receiving-c211/RESULTS.md)
