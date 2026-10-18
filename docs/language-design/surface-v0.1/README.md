# surface-0.1 acceptance corpus

These are **predetermined acceptance inputs**, not execution results. They were fixed before native surface source support. The normative contract is [OK-LANG-003](../OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md). The original proposal is archived separately. Native parsing, construction, GLB/0.3 export and Agent/0.3 are now implemented; [STATUS](../../../STATUS.md) identifies integrated work and complete release evidence.

* `01-surface-parts.ok` is the exact pinned reusable source dependency for `02-studio.ok`. Its SHA-256 is recorded in the main source and acceptance manifest. Do not edit it without deliberately revising the pin.
* `02-studio.ok` is authored version `0.3` source. Older compilers are expected to reject it.
* `acceptance.json` fixes M01-M12 case identities, independent analytic oracles, resource boundaries, negative diagnostics, held-out variants and required source/destination outcomes.

This directory alone does not mark any acceptance case passed. Actual source compilation, independent GLB inspection, agent repair and browser evidence remain required. A host-language generator or metadata-only material region cannot satisfy the native language gate.

## Numeric and immutable-input clarification

[OK-LANG-003-C1](clarification-c1.md) adopts an explicit coordinate-representation rule at the one-millimeter station boundary and requires isolated validated input snapshots. Its regression cases were specified before the corresponding kernel correction. It does not change the frozen acceptance manifest or register surface source support.

The existing corpus audit checks pin and formula consistency. The additional `tests/test_surface_manifest.py` sends the actual frozen geometric inputs into the kernel and compares the resulting positions, topology, material groups and counts with those expectations. It explicitly identifies the native-placement rejection that remains outside the kernel. These are partial kernel checks, not completed source/agent/destination M01-M12 gates.

## Execute the native release requirements

[conformance.json](conformance.json) maps M01–M12 to concrete source, protocol, geometry, boundary and regression tests. It also fixes the mandatory workflow artifacts, independent destination checks, browser captures and evidence identities. The original `acceptance.json` and pinned library are unchanged. The [composition companions](compositions/README.md) add ordinary/generated source and rotated-release expectations.

Run `python3 tools/run_surface_conformance.py --output /tmp/ontokin-surface-conformance.json` from the repository root. This actually executes the mapped tests. Selected requirements needing absent or stale external evidence remain pending and produce exit status 2. `--allow-pending` supports CI before external attestation without changing the recorded pending status. `--full-suite-only` produces identified execution evidence for every discovered test and enforces the inherited test floor.

The [release procedure](../../engineering/OK-ENG-004-native-surface-release-conformance.md) explains the complete source-to-export, current legacy C20, browser review and CI workflow. Supplying its identified evidence with `--external-evidence` enables the full audit. No file in this input directory independently declares a release passed.
