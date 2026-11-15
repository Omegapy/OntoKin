# C249 review: held animation selection and track inventory

## Decision and exact source

Independent review approves this component for held-source publication only.
It owns one fresh C248 capture and preserves the consumed C246/C247 boundary,
then records the sole native animation and all 36 position/rotation track roles
for the original 18-part fixture. It does not assign playback, seek, evaluate
poses or authorize a native start.

Approved author: `feb5efe78c8c748fc51f455a59619a82ec5652d0`.
Approved author tree: `79b6988d2695a59b9fe7856b3e4fb476758d44f4`.
Base held C248: `bc235deca57c032fdd9a3b310274f1c130631e0e`.
All eight author files retain their [independently checked hashes](evidence/EXACT-REVIEW-SOURCE.json).
This publication adds this review and nine exact evidence copies; it changes no
inherited file, fixture, contract or tolerance. A local author commit and the
later GitHub publication commit are separate identities even when their source
bytes agree. The handoff and PR record the observed publication identity.

The [independent approval](evidence/APPROVAL.json), [full review](evidence/INDEPENDENT-REVIEW.md)
and [author result](evidence/AUTHOR-RESULT.json) bind the roles and source. Earlier
pending fields describe their own checkpoint times; this review records the
subsequent held-source decision. All reviewers used the same Linux x86-64 /
CPython 3.12.14 environment. Separate roles do not establish another platform.

## Checks and findings

| Check | Observed result |
| --- | --- |
| Author synthetic model | 41 methods passed |
| Portable source/API binding checker | 371 checks; 23 primary-source files and 13 authority/dependency files |
| Independent adversarial model | [197 cases / 3,133 assertions passed](evidence/ADVERSARIAL-FINAL.json) |
| Independent source/API/fixture inspection | [210 checks passed](evidence/SOURCE-BOUNDARY-RESULT.json) |
| Final source consistency | [40 checks passed](evidence/FINAL-SOURCE-CONSISTENCY.json) |
| Author documentation preservation | 29 preserved sources / 5,244 local links; scoped whitespace passed |
| Godot/parser/native/product/aggregate starts | Zero |

The native source, model and author test bytes equal the independently tested
`6d1b2cc8f9aef745ee29a60d183f38de3e294c40` checkpoint. Root checks this publication
assembly separately before publishing and records its documentation/equality
results in the handoff.

[C249-F01](evidence/INITIAL-FINDINGS.json) is corrected: unsupported root paths
are rejected before native lookup. [C249-F02](evidence/MODEL-INITIAL-EXCEPTIONS.json)
was a synthetic-model error; malformed settings now return partial refusal
receipts. Original source, initial failed controls, corrected results and the
author's lexical-check correction remain preserved. No failed native run is
claimed, and no earlier failure is rewritten as a pass.

## Limits and following boundary

The single-animation association is supported by the pinned importer route and
source fixture. It is not a direct public source-animation/native-resource
pointer attestation. Actual native identities and NodePaths are observed by the
held source; names and track order do not replace the identity association.
The Python controls use fabricated objects and a resolver map and do not parse
GDScript, execute C246 events or prove installed behavior. Typed API inspection
and synthetic results have separate evidential roles.

Native parsing/getters/lifetimes, installed lineage, atomicity, key payloads,
pose fidelity, diagnostic coverage, hard limits, raw sealing, serialization,
rendering and persistence remain unproved or deferred. R07 and execution
admission remain pending. The original strict Blender-normal failure is
unchanged. [The next separate scope](NEXT-TASK.md) is held pose-observation
source or its precise API blocker, only after verified saved C249 delivery.
No next component is implemented here.

[Recovery and delivery checkpoint](https://chatgpt.com/library?file_id=libfile_fde3_f-13e3ca7283788191aa1c30570fbe2266_2ab2a24d43748191957f9bcc356b59de&account_id=personal)
records actual saves and exact source/evidence references. [Scope #227](https://github.com/Omegapy/OntoKin/issues/227)
closes only after the standalone handoff is verified, restored and confirmed saved.
