---
project: OntoKin
document_id: OK-ENG-005
title: Source Impulse Release Conformance
version: 0.1
date: 2026-10-18
status: implementation-in-progress
---

# Source impulse execution and release evidence

This procedure implements the finite release gate of [OK-LANG-004](../language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md). The [adopted corpus](../language-design/impulse-v0.1/acceptance.json) has 16 positive/boundary programs and 24 negative programs whose source bytes and independent expectations were fixed before implementation. Its status records that historical fact; it is not a result file. The [mapping](../language-design/impulse-v0.1/conformance.json) binds I01–I12 to those exact cases, concrete additional test methods and external evidence.

The runner compiles and evaluates each selected source fixture once, compares the prescribed states and diagnostic failures, and retains actual execution records. It independently checks sphere inertia, momentum updates, rotated lever arms, source spans, exact boundary sides, ordered accumulation, zero-impulse identity and complete failed-boundary rollback. It does not derive the expected velocity or source identity from an implementation report. Extreme cancellation checks retain exact canonical results rather than using a large relative tolerance that could hide failure to cancel to zero.

## Execute the source gate

```bash
python3 tools/run_impulse_conformance.py --output build/impulse-release/impulse-pending.json
python3 tools/run_impulse_conformance.py --case I03 --output build/impulse-release/rotation.json
python3 tools/run_impulse_conformance.py --full-suite-only --output build/impulse-release/full-suite.json
```

Exit 0 means the selected gate passed. Exit 1 records actual failure or unstable verification inputs. Exit 2 means required evidence is pending. `--allow-pending` changes only the exit status for a pending preparation run; it never changes JSON gate outcomes or permits a failed execution. Selecting a subset cannot set `full_gate_complete` true.

All full-suite reports must name every actually discovered and executed unittest method, including the fixed inherited floor recorded in the mapping. Missing, skipped, duplicate, failed or undiscovered required methods cannot satisfy a gate. The runner records both the current runtime identity and a stable inventory of runtime, tests, tools, workflows, specifications and source fixtures. Generated reports and archival evidence are excluded so writing a result does not invalidate itself.

## Connect actual external executions

The external evidence manifest uses `ontokin.impulse-release-evidence/0.1`. Each file reference is `{path, sha256}` with an exact `sha256:` hash and a relative POSIX path beneath `--evidence-root`. Retained nested files are similarly identified beneath their report directory. The top-level fields are:

- `implementation`: the actual current reference implementation identity.
- `workflow`: the actual Agent/0.4 exchanges, immutable source snapshots and retrieved artifact records.
- `native`: `build`, `destination`, `browser` and `visual_reviews`, identifying the same delivered source/artifacts.
- `legacy`: current `core`, `agent`, `full_suite`, `construction`, `construction_external`, `surface` and `surface_external` reports.
- `ci`: actual successful GitHub run and required job records for the exact current Git tree and verification inventory.

The workflow must contain real source operations for the frozen positive programs, including the evaluation-only extreme case, actual generated-occurrence patches from P08 to P09 and P10, rejected candidates, retries and frame-relative inspection. Compiling separate repaired source files cannot satisfy I07's Agent repair requirement. Accepted snapshots, each source unit, source edits, complete retrieved bytes, report samples and visual captures must agree on the same program/artifact identities.

I11 requires all nine `delivery_required` fixtures and front, side and animated browser captures for P02, P04, P08 and P11. The high-spin source requests low regular FPS and must receive sufficient actual quaternion samples. Independent decode checks geometry, winding, normals, PBR, local placement, fixed analytic world poses and `impulse_states_after` source-influence metadata; a reported pass flag alone is insufficient. Each capture requires an actual human or agent visual observation tied to its exact valid PNG bytes.

I12 requires the complete current inherited core/Agent, C01–C20 and M01–M12 gates, with freshly generated independent destination evidence. Historical release files cannot certify modified runtime bytes. CI must include the current Python 3.11, 3.12, 3.13 and 3D validation jobs, and the locally available named commit's complete eligible file set and blob contents must match the observed inventory.

```bash
python3 tools/run_impulse_conformance.py \
  --external-evidence build/impulse-release/release-evidence.json \
  --evidence-root . --output build/impulse-release/impulse-conformance.json
```

This final audit reads retained evidence; it does not launch Khronos, Three.js, a browser or GitHub. It explicitly records `executed_external_tools: false`. Missing, stale, contradictory or unsupported evidence remains pending. During the initial reader implementation checkpoint, external gates are intentionally pending even if a file reports success; later reader commits must establish every listed relationship before those gates may pass.

Follow [AGENTS](../../AGENTS.md) for branch ownership, test evidence, integration and recovery. All I01–I12 gates must pass together for this finite milestone. Every report retains `full_product_conformance_certified: false`; finite forces, contact, continuous torque, general dynamics and the remaining [GOAL](../../GOAL.md) requirements stay open.
