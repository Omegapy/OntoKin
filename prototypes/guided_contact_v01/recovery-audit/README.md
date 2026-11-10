# C191-R2 author recovery audit

The recovered candidate `dc782500d74a8b269c3471121345d6c8566508eb` admitted
contradictory native object types and could publish an artifact directory with
no usable saved native scene. This audit reproduced those failures before
repairing validation. The adopted contract, original expectations and historical
files remain unchanged.

## Observed failures and repair

The native-result schema allows `MESH` and `EMPTY` objects. The role-specific
validator must also require a mesh for each visible/helper solid and an empty
object for each constraint. Previously a carriage reported as `EMPTY`, or a
constraint reported as `MESH`, passed validation. Both now reject with the
existing `C191_E_NATIVE_RESULT` diagnostic.

The transaction previously required only the native JSON trace. Deleting
`scene.blend`, replacing it with an empty file, or replacing it with text still
produced `successful=true` and committed a new accepted pointer. The transaction
now requires the scene before recording/export. A missing scene rejects with
the existing `C191_E_NATIVE_FAILURE` diagnostic. An empty or incompatible header
rejects with `C191_E_NATIVE_RESULT`.

The first repair checked the twelve header bytes and the presence of payload.
Its exact code and successful six-case result are preserved at
`0afeb31ba87195cd133734f1a0ec09ad950be255`. Coordinator review correctly identified
that this still admitted obviously truncated files. The additional failures and
the subsequent complete envelope check are recorded below.

The initial repair changed `native_validation.py` and its call site in
`transaction.py`.
The source parser, native construction, solver configuration, canonical input,
captured motion and GLB encoding/projection did not change.

## Evidence

One audit-only A run supplied an actual native seed before the mutations. It is
separate from the independent formal native batch. Its
[returned receipt](evidence/baseline-A-result.json) identifies every artifact and
the exact executed implementation. The native-result SHA-256 is
`a11d6e719fb71d3cebd6953dc4fa06fedd6f7ffd91ac3b656a0419f269979a02`;
the final GLB SHA-256 is
`1ccfdd4691edb924747a5b7b48bfdf01b2647e3393979cf088b9de231f00f38d`.

[Before repair](evidence/before-fix/summary.json), the valid-copy control passed
and all five bad candidates incorrectly committed. These failed acceptance
results remain preserved. [After repair](evidence/after-fix/summary.json), all
six controls passed: the valid copy committed, each bad candidate rejected with
its specified diagnostic, the previous accepted pointer stayed unchanged on
rejection, and every previous artifact byte remained unchanged in every case.
Both reports bind actual Python file hashes; the post-fix report records the
pre-commit Git HEAD separately from its changed worktree bytes.

## Complete saved-scene envelope

The current validator reads the complete uncompressed `.blend` file, in bounded
chunks. It checks the pinned 64-bit, little-endian file version, every 24-byte
block header and payload length, nonnegative length/count/type-index fields, the
DNA block marker, required scene/object/mesh blocks, and the terminal `ENDB`
block with no trailing data. It requires one global block and one DNA block.
Every block charges five field operations and checks cancellation/deadline;
each payload chunk has a further budget checkpoint. The admitted file remains
subject to the existing 64 MiB staged-output ceiling. A validation receipt binds
the complete scene hash and observed block/byte counts.

The pinned Blender installation's own `scripts/modules/blend_render_info.py`
documents the block layout and uses 24-byte headers on its 64-bit path. Its
exact installed bytes and archive identity are identified by
[format provenance](evidence/format-provenance.json). The new code is an
independent bounded envelope validator; it does not import Blender's parser.

[Before the envelope repair](evidence/structure-before-fix.json), only 2 of the
13 direct-validator expectations passed. The header-only case rejected, but
eleven malformed payload/block cases were accepted. The inputs cover a header
plus one byte, partial block headers and payloads, missing/truncated end blocks,
trailing bytes, negative/overrunning block lengths, a nonempty end block, a
missing DNA block, and an otherwise empty header/end pair. Those failures are
retained separately from the original five transaction defects.

[After the envelope repair](evidence/structure-after-fix.json), all 13 direct
checks passed. The valid 613,968-byte seed was checked through all 1,882 blocks;
the twelve malformed variants rejected with `C191_E_NATIVE_RESULT`. These direct
checks make no transaction or re-simulation claim. The independent reviewer
separately exercises atomic rejection through the supervised transaction.

This validator checks the file envelope, not the meaning of DNA or scene data.
Independent fresh-process opening, persisted configuration inspection, cache
clearing and re-simulation remain required qualification gates. Neither the
initial header check nor the complete envelope check replaces them.

## Optional output paths preserve accepted bytes

An additional transaction audit found that caller-selected receipt paths could
overwrite `state.json`, an old artifact, or the input `.ok` file, including after
the source had already rejected. Symlink aliases had the same effect. Direct
writes to an external hard link also modified the old artifact inode. Separately,
`validate` could overwrite its own source with canonical JSON, or overwrite its
claimed canonical output with a receipt when both requested paths were equal.

The existing diagnostics and state meanings now apply to these paths:

- A valid `run` source with a known protected receipt path rejects before a
  native worker starts, with `C191_E_PUBLICATION` at the output binding.
- An invalid source retains its original diagnostic. The unsafe optional receipt
  is suppressed and reported on stderr; accepted state and artifacts stay exact.
- Receipt delivery rechecks its path. An alias introduced after initial checking
  cannot overwrite state after a successful commit. Only that optional receipt
  is suppressed; the actual successful commit remains successful.
- `validate` rejects source/output aliases with `C191_E_IO` at its source header
  before either requested output is written. Canonical and result outputs must
  be separate from each other and the source.

Path checks compare absolute and resolved paths and use `samefile` for known
input aliases. Every descendant of the current store is protected. A reopened
scene is also a protected input. External receipts and canonical files use a
temporary sibling plus atomic replacement; replacing a separate hard-link name
therefore leaves the original store/source inode unchanged. Ordinary receipt IO
failures after a commit retain the earlier warning-only policy.

This guard handles trusted caller mistakes and the measured late-alias test. It
does not claim adversarial cross-process filesystem isolation or discover
arbitrary unrelated stores. The existing README and frozen harness destinations
remain outside their stores and distinct from source inputs.

The [pre-fix alias audit](evidence/aliases-before-fix/summary.json) passed only
the valid external-path control; eleven other expectations failed.
The [post-fix audit](evidence/aliases-after-fix/summary.json) passed all twelve
cases, including invalid-source preservation, direct/symlink store aliases,
external artifact hard links, valid-source preflight refusal, a late state
symlink and validator output collisions. Exact returned receipts are retained
beside both reports. Valid transactions use the identified copying worker;
these tests make no additional native-solver claim.

This repair changes only auxiliary output handling in `common.py`, `api.py` and
`transaction.py`. It leaves the frozen source language, canonical bytes, solver
settings, native worker and raw/final GLB mapping unchanged.

These supplemental expectations were recorded before running the controlled
mutations, after reviewing the recovered implementation. They do not replace or
retroactively enlarge the original frozen checker. The independent reviewer
owns separate confirmation and the final native qualification.

## Reproduce the focused audit

`check_native_boundary.py` exercises the actual API, process supervisor and
atomic publication path with a trusted copying worker. It copies only the
identified native trace and scene from an already successful A seed, applies one
fault, and checks the returned state. It makes no fresh native-solver claim.

From the repository root, with an identified A artifact directory and the
pinned Blender executable:

```sh
python -B prototypes/guided_contact_v01/recovery-audit/check_native_boundary.py \
  --repo "$PWD" --seed /absolute/path/to/A/artifacts/attempt-id \
  --output /absolute/path/to/fresh-audit-output --blender /absolute/path/to/blender
```

The output directory must not exist. To reproduce the original failure, run the
same supplemental script with `--repo` pointing at the recorded pre-fix
candidate. Each audit result records implementation file hashes, the native
seed hashes, the script hash, returned receipt hashes and state preservation.

To run the direct complete-file checks, use `check_scene_structure.py` with
`--repo`, `--seed` pointing to the identified `scene.blend`, and `--output`
pointing to a fresh directory. Its report records exact validator/script/seed
hashes. The pre-fix output used the first-repair commit identified above.

`check_output_aliases.py` uses the same `--repo`, `--seed`, `--output` and
`--blender` arguments as the native boundary audit. It copies the identified
seed store before each case, so its deliberate pre-fix corruptions never alter
the seed or the repository source fixtures.
