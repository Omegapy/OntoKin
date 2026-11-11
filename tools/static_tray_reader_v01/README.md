# Independent static-tray geometry reader

This tool measures the finite output defined by
[OK-MAP-STATIC-TRAY-001/0.1.0](../../docs/engineering/static-tray-mapping-c198/SPECIFICATION.md)
and [its validation plan](../../docs/engineering/static-tray-mapping-c198/VALIDATION-PLAN.md).
Its five Python files import only one another and the standard library. They
do not import the producer, source compiler, canonical lowerer, Blender worker,
or producer geometry helpers.

`expected.py` transcribes Q01–Q05 from the frozen decimal inputs and derives
independent dimensions with exact rational arithmetic. These dimensional
expectations use the existing 0.000005 m delivery allowance. They do not replace
the separate bit-for-bit source/canonical-record comparison.

## Actual checks

The reader validates the GLB header, JSON and binary chunk boundaries, duplicate
JSON members, internal buffer bounds, offsets and strides, accessor types, finite
values, graph structure and unsupported features. It decodes actual POSITION,
NORMAL and index buffers; accessor min/max values never stand in for geometry.

For every box it measures corner locations, all six surfaces, welded topology,
outward triangle winding, signed rational volume, rigid transforms and fixed
materials. It measures cavity size, four horizontal payload gaps, the zero bottom
gap, headroom and positive material overlap. Missing identities are reported
while other independently readable geometry remains available. Structurally
valid size errors do not suppress the required clearance findings.

The right-sibling closure contains resolved nodes, local and world transforms,
actual vertices and normals, triangle indices, identity/relationship metadata and
material values. It removes GLB container index references by resolving their
objects; it does not round geometry or discard changed metadata. Q04 and Q05
cannot pass without a retained baseline closure. The caller must authenticate
that baseline against its immutable accepted-store evidence.

## Interfaces

The coordinator supplies a completed executable lock before qualification:

```sh
python3 -IB /absolute/checkout/tools/static_tray_reader_v01/audit.py \
  --artifact /absolute/candidate/final.glb --expected Q01 \
  --lock /absolute/input-lock.json --result /absolute/new-audit.json

python3 -IB /absolute/checkout/tools/static_tray_reader_v01/corrupt.py \
  --case D01 --artifact /absolute/accepted/final.glb \
  --output /absolute/new-control/D01.glb --lock /absolute/input-lock.json
```

The input lock's `independent_reader.files` object must contain the SHA-256 of
exactly `audit.py`, `reader.py`, `glb.py`, `expected.py` and `corrupt.py`. The
reader verifies these actual local bytes. Both entry scripts reject a local
`__pycache__` directory or `.pyc`/`.pyo` file before importing reader helpers;
`-B` alone does not prevent reads of existing bytecode. The caller must also
authenticate the source closure before starting either entry script.

The audit CLI requires the complete `independent_reader.delivery_rules`
declaration. The reader rejects unknown, missing or weakened rule values and
checks node/mesh/material order, scene root indices, fourteen nodes, twelve
meshes, one primitive per mesh, the exact POSITION/NORMAL attribute set,
float32 VEC3 geometry, uint16 SCALAR indices, twenty-four position/normal
vertices and twelve triangles per mesh. Fixed material declarations must agree
with the already measured material contract. The native qualification lock must
fix this selected layout before execution.

The `nonsemantic_metadata` declaration closes remaining free-text fields.
Production delivery requires generator `Khronos glTF Blender I/O v4.5.48` and
scene name `StaticTray`. Buffer, buffer-view and accessor name fields are
forbidden, including on unused accessors. No source hash, route or record hash
can be inserted through those fields. These are exact allowed values, not a
blacklist of hash-looking strings. Readable metadata errors produce findings
while geometry measurement continues.

The measurement-only API also recognizes the exact historical marker
`Independent synthetic reader control` and an omitted scene name. It rejects
arbitrary labels. A full delivery audit rejects that historical marker and
requires the production declarations. Current synthetic fixtures imitate the
fixed metadata fields as test data; they remain synthetic CPU evidence.

The `schema`, `buffer_storage` and `raw_to_final` declarations have exact known
values. The reader verifies internal, uncompressed decoded buffer storage and
permits shared buffer data. Exporter determinism and raw-to-final byte identity
remain transaction checks requiring two retained artifacts; a single-artifact
reader cannot establish them. Those description fields cannot add an ignored
constraint under an arbitrary key. The lock's
remaining source, host, worker, receiver and command bindings belong to the
coordinator's complete preflight and independent review.

Both CLIs enforce a 30-second deadline. GLBs are limited to 8 MiB and results to
4 MiB. Auxiliary expected-fixture and baseline JSON files use capped reads of
4 MiB plus one byte from regular nonsymlink files before JSON decoding. Outputs
use exclusive creation. The corruption writer preserves its
input and records before/after hashes and the exact changed byte-offset ranges.
D08 defaults to an exact copy; `--variant reordered` changes JSON key order
only, so measurement equivalence and byte regeneration remain separate.

The Python API is `audit(path, expected="Q01", baseline_right=None,
delivery_rules=None)`. Omitting rules is reserved for synthetic/measurement API
use; any supplied rule dictionary must be complete. A complete earlier result or its `right_closure` can
supply the baseline. Results include stable findings, every measurement and
threshold, per-node decoded data, and the complete right closure.
`expected_case(case)` and `expected_bounds(case)` are independent receiving
references. The constructor must not import them.

## Verification boundary

The separate `tests/test_static_tray_reader_v01.py` creates hand-derived
synthetic GLBs with explicit surfaces and native-independent binary encoding.
It exercises Q01–Q05, valid interleaved buffers, D01–D08 classifications, source
preservation, invalid topology, structural failures, materials, sibling equality
and the isolated lock-verified entry point.

```sh
python3 -IB -m unittest discover -s tests -p test_static_tray_reader_v01.py -v
```

These are synthetic CPU checks. They do not establish real Blender output,
real receiving/import results, visual review, bounded native cancellation,
profile qualification, tray admission, or any broader release gate. D01–D08 must
still be applied to actual retained output under the frozen qualification plan.
