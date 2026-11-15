# C243 results: mapping investigation completed; native capture blocked

C243 narrows C241's source-derived lifetime risk to the exact selected fixture
and call sequence. The prescribed no-custom-extension loader route has no
established safe ordinary-caller capture window between source-map construction
and mesh replacement/deletion. [Design and evidence chain](DESIGN.md)

The source investigation covers nine exact upstream files. Five newly fetched
supporting files include `Node::replace_by`, the raw-pointer map declaration,
extension callback dispatch and generation API declarations. The original GLB
contains 18 mesh-bearing scene roots, five shared meshes, no skins and no
`GODOT_single_root` extension. The ordinary/default mesh branch selects a
synthetic nonmesh parent and converts the 18 product nodes inside the built-in
post phase. The loader permits selected built-in extension overrides first;
their complete installed selection remains unverified. This finding is
source-derived; Godot was not run.

## Executed checks

The retained [read-only inspector](evidence/inspect_mapping.py) passed all
**18 static verification groups** on Linux x86-64 / CPython 3.12.14. It checked
the nine upstream byte/blob/hash bindings, eight unchanged authority files,
six unchanged prior contracts, exact fixture and source-node/mesh mapping,
ordered generation/conversion/signal facts, and unchanged installed candidate
bytes. [Full receipt](evidence/STATIC-MAPPING-REVIEW.json)

These are source and file checks. They do not invoke a product checker, simulate
Godot, test a native pointer, or demonstrate installed API behavior. The embedded
build identifier remains different from the inspected upstream revision; build
lineage is unresolved.

The focused documentation preservation/link check is recorded in
[DOCUMENTATION-CHECK.json](evidence/DOCUMENTATION-CHECK.json). Independent review,
published commit identities and any actual-main verification are separate
integrator evidence, not inferred from author checks.

To reproduce the static inspection after restoring the C243 package:

```bash
python3 -IB docs/engineering/second-target-c243/evidence/inspect_mapping.py --package /absolute/extracted-c243 --report /absolute/static-mapping-review.json
```

The inspector needs the exact installed candidate for its last two checks. It
does not install dependencies, locate an alternative executable or start it.
If those bytes are absent, that fresh inspection cannot pass; the retained
receipt still describes only the actual environment in which it was produced.

## Completion and preserved limitations

The bounded deliverable is the precise blocker and concrete **unadopted**
callback/signal design. No C220 exception, observer/emitter, engine patch,
metadata injection, source regeneration or new receiving claim is implemented.
Native/version/import/render/save/reopen starts, product runs and aggregate
runs are all **zero**.

R07 remains pending. The original strict Blender normal failure, all historical
evidence and numerical limits retain their meaning. The [next separate
task](NEXT-TASK.md) is a versioned capture-hook decision; it must finish before
observer implementation or any later admission work can claim this mapping
prerequisite resolved.
