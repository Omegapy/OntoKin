# C210 independent semantic-export review

**Decision:** Approve the finite component at commit `bb7e831a05513a092ee5845f8bf3fd0124d3e5a4`, tree `752b501fc4ad8ba36a4ecc5c68869267a1e6fd65`, subject to the root integration gates listed below. The reviewed implementation worktree was clean. Exact owned-file hashes and scope are in [REVIEW.json](REVIEW.json).

## What was checked

The reviewer read the current coordination rules, goal/status, adopted construction and Agent contracts, exporter validation contract, normalized records, source bundles, Agent revision handling and the unchanged keyed-rack fixture. This confirmed that the sidecar uses the existing representation rather than introducing another intermediate representation.

The independent source/artifact review passed **47 controls**. A separate audit of the retained actual Agent exchanges passed **21 controls**. These are separate from the implementation worker's 13 unit tests and 54 workflow checks; none of those counts is substituted for another.

- All 18 occurrence identities match the frozen independent oracle and survive the edit.
- Only the selected blade's serialized geometry and animation change. The selected Finger's length parameter and its blade form the two changed semantic object records. All 16 unrelated objects retain their semantic values; all 11 objects in the second rack retain their geometry and recorded motion.
- Exactly one of 34 sites changes its declared local offset. Eight hinge and eight follow declarations retain their values. Ownership remains distinct from GLB transform parenting.
- Direct `struct`/JSON decoding independently checks actual GLB headers, chunks, accessor extents, indices, finite values, geometry dimensions and per-object geometry/motion content. It does not use OntoKin's GLB reader for these observations. The largest full-dimension discrepancy from the frozen source oracle is recorded in [independent-controls.json](independent-controls.json).
- Stale source/artifact pairing, a comment-only source revision change, stale sidecars, wrong mesh/accessor references, invented dimensions, an omitted site, invented physics support and an unsupported external requirement reject.
- A source-declared sphere body explicitly exceeds this finite profile. A real GLB exported over only 0.5 seconds rejects instead of claiming the full two-second source horizon.
- The [transcript audit](transcript-controls.json) checks 24 actual Agent exchanges, all 12 retained artifact chunks against exact assembled GLB bytes, invalid edit/retry preservation, accepted edit/retry identity, rejected changed/stale requests, precise invalid-candidate diagnostic bytes and clean-store regeneration.
- All 192 preexisting `ontokin/*.py` files remain byte-identical to the initial inventory. All four frozen C201 protocol files remain byte-identical to published C209. No old source-language or exporter implementation was edited.

## Findings resolved before the reviewed checkpoint

The initial sidecar design could accept a valid prefix GLB while recording only the complete source duration. The finite profile now rejects partial intervals explicitly and separately identifies delivered interval and source duration. The independent real-prefix control passed.

The contract's unit-test command now uses `unittest discover` with an exact filename pattern. This avoids reliance on importing a `tests` namespace that has no local `__init__.py`.

## Reproduction

Run the implementation's documented workflow first into a fresh directory. Keep these review scripts and `initial-inventory.json` together, then run from any directory:

    python3 independent_review.py --repo /path/to/OntoKin --proof /path/to/proof --output independent-controls.json
    python3 audit_transcript.py --proof /path/to/proof --output transcript-controls.json

The scripts never mutate source, accepted artifacts or Agent state. The controls create only in-memory negative variants and one in-memory prefix export. Detailed bindings retain the original execution locations as provenance; the command arguments allow relocation.

## Limits and remaining root gates

The root still owns applicable local-driver verification, honest accounting for inherited failures, exact-artifact Khronos/Three.js checks, actual visual inspection, scope/navigation/preservation review and conditional serialized integration. Component approval is not a full regression or release pass. It establishes no Unreal/UEFN importer, live destination physics, comparative authoring benefit or complete product scope.

The required accepted-revision argument provides an identity precondition. It does not authenticate acceptance; the actual Agent transcript supplies separate finite evidence. No C201 native admission, C199/C200 schedule, Unreal plugin, second backend or author study was started by this review.

The source and evidence must be included in the verified next handoff before delivery is declared complete.
