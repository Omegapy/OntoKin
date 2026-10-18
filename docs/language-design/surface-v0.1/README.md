# surface-0.1 acceptance corpus

These are **prospective inputs**, not evidence that the surface profile executes. The normative contract is [OK-LANG-003](../OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md). The original proposal is archived separately.

* `01-surface-parts.ok` is the exact pinned reusable source dependency for `02-studio.ok`. Its SHA-256 is recorded in the main source and acceptance manifest. Do not edit it without deliberately revising the pin.
* `02-studio.ok` is authored version `0.3` source. Older compilers are expected to reject it.
* `acceptance.json` fixes M01-M12 case identities, independent analytic oracles, resource boundaries, negative diagnostics, held-out variants and required source/destination outcomes.

This directory alone does not mark any acceptance case passed. Actual source compilation, independent GLB inspection, agent repair and browser evidence remain required. A host-language generator or metadata-only material region cannot satisfy the native language gate.

## Numeric and immutable-input clarification

[OK-LANG-003-C1](clarification-c1.md) adopts an explicit coordinate-representation rule at the one-millimeter station boundary and requires isolated validated input snapshots. Its regression cases were specified before the corresponding kernel correction. It does not change the frozen acceptance manifest or register surface source support.

The existing corpus audit checks pin and formula consistency. The additional `tests/test_surface_manifest.py` sends the actual frozen geometric inputs into the kernel and compares the resulting positions, topology, material groups and counts with those expectations. It explicitly identifies the native-placement rejection that remains outside the kernel. These are partial kernel checks, not completed source/agent/destination M01-M12 gates.
