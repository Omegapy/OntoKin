# C085 comparison amendment 001: original primary key source

**State:** Proposed for independent review and publication before complete delivery comparison.  
**Original input commit:** `92b1ee60a2b9439878b7124981d2896be858937f`.  
**Original input manifest SHA-256:** `4914fd1696bc0c441736684289a4c4422c9db30ba99091dfbbbf8d1eb1c8a2a9`.

## Source-only finding

The adopted zip rule preserves the left input's original primary key declaration. The paired panel's left input is the dimensions collection returned by the unchanged `.17` dimensions library. Its `left` and `right` entries originate in `package:fixture.pair-dimensions@1.0.0`.

The separately authored explicit `.17` control creates its paired material collection with a fresh keyed literal in `package:fixture.pair-panels@1.0.0`. Its primary key entries therefore correctly originate in that panels unit. The actual and control input-entry locations have different `source_id` values even though their stable keys, generated occurrence identities and complete geometry agree.

The frozen delivery-comparison requirement enumerated `generated.input_entry` locations but permitted differences only in their filename, revision and byte offsets. Correctly retained primary origins cannot satisfy that restriction. This defect follows directly from the frozen source text and original key-origin rule. No candidate GLB or runtime outcome supplied the diagnosis or proposed correction.

## Narrow correction

The accompanying machine-readable map binds each side's original **source ID, revision, filename, start byte and end byte**. Independently validate all five fields before normalization. At only those enumerated primary generated input-entry locations, permit the `source_id` difference and replace it with the same role-bound comparison marker on each side.

The existing permitted filename/revision/offset replacement must also use role-bound markers at these locations, because a marker containing the original source ID would preserve the already validated difference. Retain every field and its raw JSON position; retain each original value and enumerate every changed path in the comparison report.

The two authorized projection locations per generated occurrence are:

- `nodes[i].extras.ontokin.source_mapping.generated.input_entry`, where the node's exact source occurrence path and element ID select `i`.
- `extras.ontokin.program.occurrences[path].generated.input_entry`, where the exact source occurrence path selects `path`.

The four paths are `first.panels["left"]`, `first.panels["right"]`, `sibling.panels["left"]` and `sibling.panels["right"]`. The exact node and program mappings must agree before comparison. This is **eight location paths per unique bundle**. The five named delivered cases represent three unique actual/control bundle pairs: **40 named-role locations and 24 unique-bundle locations**. Repeated source aliases and Agent retrieval labels are disclosed aliases; they do not create additional unique bundles or new allowances.

## Preserved requirements

No other `source_id` may change under this amendment. The exact ten-field zip records, both contributor entry locations, operand/body locations, inherited derivation records, stable keys and occurrence IDs remain independently checked. The amendment grants no writable identity.

All source cases, explicit controls, independently authored values, original adoption and original input manifest remain unchanged. Complete BIN equality, geometry, materials, UVs, exact PNGs, samplers, motion, unknown JSON, member order, raw encoding, framing and padding retain their original comparisons. No broad metadata or extras removal is authorized.

Preserve the first frozen comparison rule and this separately reviewed amendment as distinct evidence. Publish the reviewed amendment and bind its exact bytes in the independent reader before performing the complete delivery comparison. Implementation, execution, integration and full release acceptance remain separate; this document makes no execution or release claim.
