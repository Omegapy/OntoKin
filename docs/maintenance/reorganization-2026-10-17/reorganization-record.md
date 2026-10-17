# OntoKin documentation reorganization

| Record | Value |
| --- | --- |
| Identifier | OK-DOC-ORG-001 |
| Date | October 17, 2026 |
| Scope | Repository documentation organization and preservation |
| Status | Implementation complete; source preservation and local navigation verified |
| Repository | [Omegapy/OntoKin](https://github.com/Omegapy/OntoKin) |
| Starting `main` commit | [`2a2b394119229031db78162ab7b82897f4a0064e`](https://github.com/Omegapy/OntoKin/commit/2a2b394119229031db78162ab7b82897f4a0064e) |
| Starting tree | `72aa56f6b74ff9e637fc0def3ba25acb7bd2bb43` |
| Related draft branch inspected | `docs/ok-sem-001-core-semantics` at `c1fbd96721a205e4de3e0118a9d756a02513bcbc` |
| Decision boundary | Organize the existing design record; preserve its meanings, versions, and review states. |

## 1. Intent and examination findings

The project owner requested a complete review and reorganization of the repository's documents. The aim is to make the project and language definition easier to navigate, combining documents where that helps, while retaining every detail. The requested sequence is requirements, an implementation plan, implementation, and a final preservation check. This record follows that sequence. Its requirements concern this documentation change; they do not add OntoKin language requirements.

The starting tree contains 27 files: 26 documentation artifacts and the existing `.gitignore`. The documentation comprises six substantive Markdown documents, four READMEs, one HTML edition, six PNG diagrams, six SVG diagrams, and three Graphviz DOT sources. Each file was fetched at the recorded commit, decoded, and verified against its Git blob identifier before editing. Full-document reviews covered the PRD, capability definition, semantic model, three founding records, alternate formats, and all package navigation. All six PNG figures were visually inspected; SVG and DOT content was also inspected.

The related draft pull request [#1](https://github.com/Omegapy/OntoKin/pull/1) was checked for additional documentation. Its semantics document has exactly the same Git blob as the copy already on `main`: `380850a1940005e29d4bcdd0ac3a9e2a43babda8`. The branch adds two distinct navigation texts: a revised root README and a semantics package README. Both are included in the navigation history and preservation inventory. Their branch and pull request state are outside this reorganization.

### 1.1 What causes the confusion

| Observation | Consequence | Treatment |
| --- | --- | --- |
| The root README lists only OK-001, OK-002, and OK-003. | Readers start with early exploration and miss the current capability, requirements, and semantics drafts. | Rewrite the entry point and supply one guide to all six documents. |
| The README links to `Defining_OntoKin_Docs/`, while the actual path is `Defining_Ontokin_Docs/`. | The directory link fails on GitHub's case-sensitive paths. | Replace it with verified relative navigation. |
| The semantics draft is filed inside `Product_Requirements_Docs`. | Product outcomes and proposed language meanings appear to have the same role. | Place product documents and language design in separate folders. |
| Package directories mix short IDs, long release-style names, and different diagram layouts. | Readers must infer the purpose of each package from its filename. | Use stable document IDs in filenames and one location for founding diagrams. |
| The PRD filename says `v0`, while the document identifies itself as v0.2. | Filename and metadata suggest different versions. | Use a filename based on its stable identifier; retain version 0.2 inside the document and record the old name. |
| The same subjects recur across vision, requirements, capability, and semantics documents. | Readers can mistake elaboration or a different decision level for redundant content. | Explain each document's role and the recorded scope progression. Keep substantive texts separate. |
| OK-003 has Markdown and HTML editions, and figures have several formats. | File count overstates the number of independent specifications. | Present these as alternate editions and source/rendered assets of the same documents. |

### 1.2 Consolidation decision

Consolidate package navigation into the new documentation guide. Preserve each replaced README in full in [navigation history](navigation-history.md), with its original path and commit.

Keep the six substantive documents separate. OK-001 records the founding vision and roadmap; OK-002 explores language concepts; OK-003 explores execution architecture. The PRD defines broad required outcomes, CAP records the later modeling emphasis, and SEM proposes precise relationship meanings. Combining these bodies would create a larger document while mixing different purposes and review states. The existing PRD already connects its requirement catalog, acceptance scenarios, sources, and revision record. Splitting that catalog would add maintenance work without improving the requested reading path.

This decision retains meaningful repetition where it carries context, rationale, or a distinct requirement. The new guide links to the source responsible for each topic instead of creating another product summary that competes with those sources.

### 1.3 Guidance used

The organization is tailored to the content examined. Diataxis supports organizing around reader needs and cautions against creating empty categories merely to fill a template. Its workflow is used as guidance; the owner's explicit requirement for a written plan governs this task. [D1]

arc42 recommends retaining the context, rationale, status, and consequences of important decisions while avoiding redundant text. Its distinction between proposed and accepted decisions supports keeping OntoKin's review states explicit. [D2]

NASA's requirements and configuration management guidance supports traceability, an identifiable starting baseline, change records, and verification against that baseline. These practices are applied to this small repository without adding a formal approval process. [D3] [D4]

GitHub recommends relative links for repository documents and images. Moving files also requires checking heading anchors and references. [D5]

## 2. Reorganization requirements

All requirements below are required for this documentation task. U means the owner's current request; I means the repository inventory and content review. D1-D5 refer to the guidance in section 6. These IDs are independent of OntoKin's existing product requirement IDs.

| ID | Requirement | Basis | Acceptance evidence |
| --- | --- | --- | --- |
| ORG-01 | Identify and examine every file at the starting `main` commit, including alternate formats and diagrams. Inspect related open documentation work for unique material. | U, I, D4 | Complete source inventory with source commits, original paths, byte counts, SHA-256 hashes, and Git blob IDs; document and figure review evidence in section 4. |
| ORG-02 | Preserve every source document's substantive content: metadata, definitions, requirement wording, priorities, evidence columns, examples, equations, pseudocode, diagrams, captions, rationale, caveats, open questions, and references. | U | Complete-file recovery and hash comparison, plus active-document and section checks. |
| ORG-03 | Preserve original document IDs, versions, dates, requirement IDs, and review states. Do not approve proposals, select dependencies, change scope, or claim implementation through editorial reorganization. | U, I, D2 | Original metadata and protected registries remain unchanged; guide accurately identifies each role and status. |
| ORG-04 | Provide one root entry point and one documentation guide with a short reading order and a direct link to every substantive document and alternate format. | U, I, D1 | Navigation review and local link checks; current CAP, PRD, and SEM drafts are easy to find. |
| ORG-05 | Organize the main reading material into two clear subject areas: product definition and language design. Keep maintenance evidence outside the main reading path. | U, I | Implemented folder structure matches section 3.1. |
| ORG-06 | Consolidate navigation where purposes overlap. Retain substantive documents separately when fusion would mix decision levels or obscure unique context. Document the choice. | U, I, D1, D2 | Section 1.2 records the decision; the guide replaces scattered package navigation. |
| ORG-07 | Keep all six substantive documents available as active readable files. A preserved historical copy or summary alone cannot substitute for their full current text. | U | Each source body maps to its active destination; complete text and section comparisons pass. |
| ORG-08 | Preserve all binary figures, vector diagrams, Graphviz sources, and the HTML edition. Keep their relationships to the relevant document visible. | U, I | All 15 diagram files and the HTML edition match their original bytes; image links resolve. |
| ORG-09 | Repair local document links, image references, and heading anchors after moves. Retain historical URLs pinned to earlier commits. Record old paths and all intentional text transformations. | U, I, D5 | Link/anchor report has no unresolved active local references; source map records exact replacements. |
| ORG-10 | Retain the contents of replaced navigation documents in a clearly labeled history, including the two unique navigation texts on the related draft branch. | U, I, D4 | Exact marked source blocks reconstruct all six original READMEs and match their hashes. |
| ORG-11 | Record the complete source-to-destination mapping at both file and Markdown section level. Account for every source once; identify alternate branch versions explicitly. | U, D3, D4 | Source map covers 27 main files and two unique branch files; no unaccounted sources or missing section ranges. |
| ORG-12 | Record these requirements and the implementation plan before restructuring the source documents. Track implementation results against them. | U | This record is created first; section 3 contains tasks, dependencies, and completion evidence. |
| ORG-13 | Verify preservation through content comparison, not word counts or ID counts alone. Retain a reusable offline verification command. | U, D3, D4 | Recovered complete files match original SHA-256 and Git hashes; full requirement and scenario rows, sections, and source references remain intact. |
| ORG-14 | Limit mutations to documentation and its preservation tooling. Keep `.gitignore` unchanged and leave unrelated branches and pull-request states unchanged. | U, I | Final source-tree comparison shows only the planned reorganization and its evidence. |
| ORG-15 | Apply the completed changes to the repository as one coherent, reversible documentation commit. Check the current branch head before updating it and do not overwrite concurrent changes. | U, D4 | Validated Git tree and commit; expected-head update; remote tree/read-back comparison. |
| ORG-16 | Explain how to maintain this structure: where each kind of content belongs, how to identify its status, and how to keep alternate editions and references consistent. | U, I, D1, D2 | Maintenance guidance in the documentation guide; no empty future-specification folders or new language commitments. |

## 3. Implementation plan

### 3.1 Target organization

| Location | Contents and purpose |
| --- | --- |
| `README.md` | Short project introduction, current design status, and entry to the documentation guide. |
| `docs/README.md` | Reading order, document roles and status, current versus founding context, alternate editions, diagram index, and upkeep guidance. |
| `docs/product/` | OK-CAP-001 and OK-PRD-001. |
| `docs/language-design/` | OK-SEM-001. |
| `docs/language-design/foundations/` | OK-001, OK-002, and OK-003, including the HTML edition of OK-003. |
| `docs/language-design/foundations/diagrams/` | All six figures in their original formats, including the three DOT sources. |
| `docs/maintenance/reorganization-2026-10-17/` | This requirements/plan/result record, navigation history, source map, and preservation checker. |

Document filenames use stable IDs and descriptive names. Versions remain inside the documents. The source map provides the exact mapping from every former filename to its new location. The maintenance directory is supporting evidence, not another product or language specification.

### 3.2 Ordered tasks

| Task | Work | Depends on | Requirements | Status and completion evidence |
| --- | --- | --- | --- | --- |
| P1 | Pin the source snapshot, download every file, verify source hashes, and review all documents and figure formats. | None | ORG-01, ORG-02 | Complete. 27 main files and two unique branch navigation files identified and verified. |
| P2 | Research suitable organization guidance; classify each document; write the requirements, consolidation decision, and this plan. | P1 | ORG-03, ORG-05, ORG-06, ORG-12 | Complete. Sections 1-3 recorded before restructuring. |
| P3 | Move the six substantive documents, HTML edition, and diagrams into the two subject areas. Apply only the enumerated navigation changes. | P2 | ORG-02, ORG-03, ORG-05, ORG-07, ORG-08, ORG-09, ORG-14 | Complete. Six source documents remain active; all 15 diagram files and the HTML edition retain their original bytes. |
| P4 | Replace the root and package navigation with a root overview and one guide. Preserve the complete replaced navigation as identified source blocks. | P3 | ORG-04, ORG-06, ORG-10, ORG-16 | Complete. Root overview and documentation guide created; six original navigation texts preserved verbatim. |
| P5 | Generate the file and section source map. Implement the offline preservation and local-link checker. | P3, P4 | ORG-02, ORG-08, ORG-09, ORG-11, ORG-13 | Complete. Source map covers 29 sources and 233 Markdown sections including preambles; checker is included. |
| P6 | Run complete-file, section, registry, reference, and link checks. Independently review content placement, scope/status explanations, and the implemented plan. Repair any observed errors. | P5 | ORG-02 through ORG-14, ORG-16 | Complete. Preservation and navigation checks passed; independent review confirmed content coverage and accurate status/scope explanations. See section 4. |
| P7 | Record verification results, recheck the remote head, construct and validate the final Git tree, publish one documentation commit, and verify the remote result. | P6 | ORG-15 | Publication evidence is recorded by Git: the commit containing this record supplies the final tree and source parent. The delivery message records the actual commit ID and remote verification result. |

### 3.3 Permitted editorial changes

The substantive documents are moved without prose consolidation. Local navigation paths may change. OK-SEM-001's note that the PRD filename retains a `v0` label will be clarified to refer to the original filename, because the active file will use its document ID. The exact old wording will remain in the reversible transformation record.

Historical document inventories, repository-snapshot fields, proposed roadmaps, source URLs, and the older naming note in OK-003 remain historical records. They are explained in the guide rather than rewritten as current facts.

### 3.4 Verification method

The source map stores each original file's byte length, SHA-256, Git blob ID, destination, and intentional transformations. For a moved file, the checker reads the complete destination and reverses only the recorded transformations. The recovered bytes must match both original hashes. For consolidated navigation, the checker extracts the exact identified source block before comparing it. This also accounts for every original byte in the replaced READMEs.

Markdown section records cover the complete source, including any metadata before the first heading. Their ranges must be contiguous and exhaustive, and every section hash must match. Product requirement rows, acceptance rows, owner-intent rows, capability rows, semantic rules, and behavior-check rows receive additional checks. This is content-preservation evidence; it does not validate the proposed OntoKin language or execute its conceptual behavior checks.

Local Markdown links, reference definitions, images, and HTML links are checked against the final file tree and target anchors. Historical source text inside explicitly fenced navigation-history blocks is literal evidence, not active navigation. External research pages are preserved as source URLs; this change does not revalidate every external source cited by the original design documents.

## 4. Implementation and verification results

### 4.1 Content examination and editorial review

The full PRD review covered its 1,131 lines, 74 headings, all requirement/evidence rows, acceptance scenarios, owner traceability, research, and appendices A-D. The capability and semantics reviews covered their complete texts, example sequences, scope relationships, reference catalogs, and proposed rule/check sets. The founding-document review covered the full OK-001/002/003 texts, decision registers, historical roadmaps, glossary, examples, and package READMEs.

The format review inspected all six PNG figures visually and all six SVG and three DOT files structurally. It compared OK-003's HTML and Markdown visible content, image descriptions, and link targets. They are alternate editions of the same record; the Markdown retains additional front matter and the HTML retains screen/print styling. Both editions are preserved without regeneration.

Independent reviews checked the implemented guide against the source documents and examined the preservation mapping. They confirmed that the later modeling emphasis is supported by CAP sections 1 and 9 and SEM section 1.1; the broader PRD requirements remain available; no proposal was promoted to an adopted specification. A separate direct comparison of every destination against the downloaded source files confirmed the checker results without relying on the checker's implementation.

### 4.2 Preservation results

| Check | Result |
| --- | --- |
| Starting main-tree inventory | All 27 files accounted for: 26 documentation artifacts and unchanged repository configuration. |
| Related draft-branch material | Both unique README versions preserved; identical SEM body counted once in the substantive source set. |
| Complete original recovery | All 29 source files recovered exactly from their destinations or identified navigation-history blocks. |
| Source bytes | 1,009,136 bytes from main; 8,601 additional bytes from the two branch READMEs; 1,017,737 bytes recovered in total. |
| Complete baseline-tree identity | Reconstructed Git tree is `72aa56f6b74ff9e637fc0def3ba25acb7bd2bb43`, exactly matching the recorded starting tree. |
| Unchanged main-file bytes | 21 files retain their original bytes at their destinations. |
| Source documents with editorial changes | Two: OK-001 has one image-path change; SEM has five document-link changes and one original-filename clarification. All seven transformations are explicitly reversible. |
| Replaced navigation | Six original READMEs retained verbatim, including four from main and two branch variants. |
| Active substantive documents | All six full documents remain active and are directly linked from the guide. |
| Markdown section coverage | All 233 contiguous sections verified, comprising 228 headings and five preamble blocks. No source lines are omitted. |
| PRD requirement rows | All 226 complete rows unchanged: 213 MUST and 13 SHOULD; exact identifier sets and priorities retained. |
| PRD acceptance and owner-intent rows | All 22 acceptance rows and all 16 owner-intent rows unchanged. |
| Capability rows | All 18 CAP rows unchanged. |
| Semantic rules and checks | All 28 rule headings and all 24 complete check rows unchanged; complete semantic prose also passes source recovery. |
| References, examples, equations, and metadata | Retained through complete-file and section comparisons; only the enumerated navigation/filename edits differ. |
| Figure and alternate-format files | All 15 diagram files and the HTML edition retain their original bytes. |
| Active local links and anchors | Verified without unresolved targets. The checker reports the current number inspected. |
| Independent content and structure review | Passed; no unaccounted source material or newly imposed design decisions found. |

The original main README's broken directory link is replaced by current relative navigation. All historical repository URLs remain as evidence for the commits they cite. The old unpinned file paths are recorded in the source map; the current guide uses the new paths.

### 4.3 Verification boundary and publication evidence

These results establish preservation of the recorded documentation and local navigation. They do not establish that OntoKin's proposed physics, animation, language rules, or numerical targets are implemented or correct. The original documents retain their own evidence boundaries and review status. External reference URLs are preserved; this task did not revalidate every external research claim.

This record captures the completed local checks. Publication is identified by the Git commit containing this file, whose parent is the starting commit shown above. The final remote branch/tree check occurs after publication and is reported with that commit in the delivery message. The remote update must use the expected original head and must not overwrite intervening changes.

## 5. Source inventory and recovery

The machine-readable [source map](source-map.json) identifies every original path, destination, transformation, and section. The [navigation history](navigation-history.md) contains each replaced README in full. These records preserve the complete inventory while keeping the main reading path short.

| Original substantive filename | Active document |
| --- | --- |
| `OntoKin_Modeling_Motion_and_Object_Structure.md` | [OK-CAP-001](../../product/OK-CAP-001-modeling-motion-and-object-structure.md) |
| `OntoKin_PRD_v0.md` | [OK-PRD-001](../../product/OK-PRD-001-product-requirements.md) |
| `OntoKin_Core_Object_Motion_and_Physics_Semantics.md` | [OK-SEM-001](../../language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md) |
| `OntoKin_001_Project_Vision_and_Architecture.md` | [OK-001](../../language-design/foundations/OK-001-project-vision-and-architecture.md) |
| `OntoKin_002_Language_Foundations_and_Minimal_Specification.md` | [OK-002](../../language-design/foundations/OK-002-language-foundations-and-minimal-specification.md) |
| `OntoKin_003_Compilation_and_Runtime_Architecture.md` | [OK-003](../../language-design/foundations/OK-003-compilation-and-runtime-architecture.md) |

Run the following command from the repository root using Python 3:

```bash
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

The command compares preserved content with the recorded source hashes and checks local navigation. It requires no network access or third-party packages. This checker audits the reorganization snapshot. After later intentional content edits, run it at the reorganization commit when checking this migration; record later changes separately instead of silently changing this baseline.

## 6. References

The owner request and the repository content determine this task's requirements. The following primary sources inform the organization and verification method; they do not define new OntoKin behavior. Consulted October 17, 2026.

- **[D1] Diataxis.** [Diataxis as a guide to work](https://diataxis.fr/how-to-use-diataxis/). Reader needs, content-led organization, and avoiding empty template categories.
- **[D2] arc42.** [Architecture decisions](https://docs.arc42.org/section-9/). Decision context, rationale, status, consequences, and avoiding redundant text.
- **[D3] NASA Systems Engineering Handbook.** [Requirements management](https://www.nasa.gov/reference/6-2-requirements-management/). Requirements traceability and consistency.
- **[D4] NASA Systems Engineering Handbook.** [Configuration management](https://www.nasa.gov/reference/6-5-configuration-management/). Identifiable baselines, historical records, change tracking, and verification.
- **[D5] GitHub Docs.** [Basic writing and formatting syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax). Relative links, images, headings, and anchors.
