# Proposed C258 follow-field origins

| Field | Independent source origin | Actual artifact origin |
| --- | --- | --- |
| Relation occurrence ID and path | Child occurrence key/name context plus the follow declaration's literal key/name tokens | Follow row `element_id` and `path` |
| Relation definition identity | Defining package/module/class key and follow member key | No direct field; only association through actual child class/full source mapping and relation key |
| Follow declaration span | Exact UTF-8 start/end byte span in the defining `.ok` file | Absent; do not manufacture an artifact span |
| Parent frame | `parent` expression, FrameRef declaration/default, selected initializer and lexical `self` context | Follow row `parent_frame`, joined to the actual full object mapping or explicit `world` |
| Child occurrence | Actual `child = self` expression and current occurrence context | `child_object`, joined through node path/full ID/class mapping |
| Offset reference frame | `pose` first argument and the same resolved frame dependencies | Implicitly the row's parent-frame convention; no separate encoded field |
| Offset translation | Pose argument, Vec3 parameter default/initializer, generator binder, selected keyed literal/helper argument, signed numeric tokens and unit tokens | `offset_position_m`; relevant typed node Vec3 property copy |
| Offset rotation | Four literal `quat` arguments, admitted norm, normalization and sign rule | Unmodified `offset_rotation_wxyz`; no sampled-track fallback |
| Program/source association | Actual file hashes, import pin, canonical manifest and parsed module/definition identities | Program/source authority fields and node/source mappings validated by the pinned C257 dependency |

Every source origin records a named original file and UTF-8 byte bounds.
Every artifact origin records the artifact SHA-256 and its actual JSON pointer.
An associated value is labeled as derived; a missing direct artifact authority
stays absent. Ownership edges and scene-graph parent indices are never follow
field origins.
