# P23 documentary hydration map

**Hydrate the exact missing tracked paths in `DOCUMENTARY-MISSING-TRACKED-PATHS.txt`; the complete required set is `DOCUMENTARY-TRACKED-PATHS.txt`.** The corresponding `*-SPARSE-PATTERNS.txt` files contain anchored, escaped patterns for a non-cone sparse checkout. Preserve existing sparse entries; the Director owns all Git operations.

The map is bound to branch HEAD `51a00f21013386df6ee4ce3c3560c902b32c6af5`. Both unchanged checkers were read fully. This review derived file dependencies only; neither checker was imported or executed, and no repository, index, ref or source file was changed.

## Coverage

| Input class | Concrete source | Why required |
| --- | --- | --- |
| Workflow entry files | `tools/chat_workflow.py`, registry, CURRENT, memory, knowledge, required reads, three skill files | The workflow validator opens these records and checks required paths/frontmatter. |
| All task records | Every tracked `docs/workflow/tasks/*/task.json` (12) | The validator enumerates present task directories. Omitting a directory would silently reduce coverage. |
| Workflow evidence | Requirement/check/completion evidence; completed-step artifacts; CURRENT, memory and knowledge source fields | Each referenced local path must be a real file. Incomplete plan artifact paths are only syntax-checked and add no requirement to create nonexistent files. |
| Preservation baseline | `source-map.json` and its 29 records / 24 unique destinations | The documentation checker reads the complete destinations and reconstructs original sections and registries. |
| Full tracked navigation | All 1,585 visible tracked `.md`, `.markdown`, `.html` and `.htm` files | The checker traverses every present visible document, beyond the 29 preserved sources. All tracked documents are selected to avoid narrower sparse coverage. |
| Document targets | Every required local link target; recognized README/index files for directory anchors | File links need real target bytes. Directory links need an actual tracked child. Only linked example/product artifacts are included. |

The final set contains **4,222 tracked files**, compared with 21,019 in the repository. Stage 1 supplied 1,938 paths. Parsing the hydrated documents added 2,284 target paths; 2,099 final-set paths were still missing when measured. The scan read 1,586 documents (1,585 tracked plus the new P23 declaration) and found 6,233 local link edges with no unresolved target path. This is a coverage finding, not an anchor-validity or checker pass.

`HYDRATION-STAGE2-TARGET-PATHS.txt` contains the additions only. `DOCUMENTARY-HYDRATION.json` records checker hashes, per-target reasons, all list identities and the current untracked candidate targets. No placeholders are proposed. Newly authored P23 documents and references must remain present when the real checkers run; later changes can add dependencies.

## Retained read incident

The first read-only Git object batch used `GIT_NO_LAZY_FETCH=1`; unhydrated promisor blobs were unavailable. The analysis stopped before producing a closure rather than fetching or modifying Git. The Director then hydrated Stage 1 successfully. `HYDRATION-READ-INCIDENT.json` preserves that boundary.

## Next action

The Director hydrates the missing real tracked files, verifies the candidate payload, and runs the unchanged workflow and documentation commands. These gates validate documentary structure, preservation and navigation. They establish no H0/H1, original-seven, full-routine or product acceptance.
