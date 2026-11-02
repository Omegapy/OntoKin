# C088 Agent input amendment

The original [frozen inputs](../freeze/INPUTS-MANIFEST.json) remain immutable. The first candidate Agent run retained 218 exchanges: eight workflows completed and A01, A02 and A03 stopped at the unchanged request schema because their edit patches used an object identifier. The inherited protocol requires an exact source-file identifier.

[Source-file scope amendment 1](agent-file-scope-v01/AMENDMENT.json) changes exactly seven `element_id` leaves in `agent/request-workflows.json` from `["sparse-panels", "demo", "first"]` to `["sources", "entry"]`. The preconditioned patch, original and replacement hashes, unchanged predecessor schema checks, effective full inventory, and original failed-run identities are retained together. All other 903 data files remain byte-identical. Source programs, patch spans and replacement text, semantic answers, resource schedules, geometry, provenance and earlier bindings are unchanged.

The [independent review](../../../engineering/keyed-membership-2026-11-02-c088/AGENT-FILE-SCOPE-AMENDMENT-REVIEW-01.md) accepts this correction for publication and exact readback. The amendment's original pending-status field records its authoring stage and is not rewritten. A separate publication/readback receipt authorizes the successor Agent run. Until that receipt exists, the corrected candidate workflow has not been executed.

Source, native and original-control readers continue to use the original freeze. The successor Agent producer uses the sealed `effective-freeze` directory; the independent Agent reader additionally requires the original freeze and this exact reviewed amendment identity. Historical failures remain failures. This input correction makes no release or full-product acceptance claim.
