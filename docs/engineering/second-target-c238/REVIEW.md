# C238 independent review

**Accepted for the finite CPU admission scope.** Independent execution used `cb662d9d2603085eea9c1f05513baeb7312a48b2`, tree `0ab3d6915221897ee6da4c09f553443c6ef6dfe4`. The checker SHA-256 is `76c87096d810236b58ac47a13ad58ab9eec558500104c6c96acf89f462deea83`; the [contract](CONTRACT.md) retained its preimplementation SHA-256 `7620410c8306ddf3b8b9ec73b0a3f3eef4013d25464317dbe7451af35b58b388`.

The final cohort passed **161 scenarios**, with **495,103 report assertions**. It fully audited all **21 admitted reports**, including **491,400 corner-map rows**; **140 cases refused** as expected. Of those scenarios, 157 used the public API and four used the CLI. Source and all eight original input hashes/modes stayed unchanged. [Consolidated receipt](evidence/INDEPENDENT-REVIEW.json).

## Independence and coverage

The reviewer independently decoded the locked GLB and read original reference, semantic and source-payload bytes. The fixture builder imported no author/product builder, evaluated no authoritative source, and invoked no target. The reviewer checked every admitted report field, source/derived identity projection, raw byte binding, dependency, corner row, material association, pose slot, semantic provenance and limitation flag.

Controls covered stale, corrupt, missing, duplicate and swapped members; incorrect schemas, source identities and origins; all corner/source inventory joins and winding; contradictory normal copies and material resources; unsupported capability claims; parser limits; unsafe paths/files/aliases; actual file mutation/replacement during the final descriptor check; fresh authority after real input corruption; CLI exits and lack of file-writing side effects. The suite also admitted deliberately inaccurate but structurally consistent observations to confirm that component fidelity remains pending.

## Resolved findings

Already inspected member bindings now survive a later refusal. Identity-stage wording now distinguishes envelope identity checks from later member projection checks. Three cosmetic field restrictions now match their original component domains; Unicode, NUL and boundary cases pass. No unresolved code finding remains.

The review records its own initial numeric-time fixture error and standard-library import metadata assertion error. Both were corrected in the independent harness; no product code changed for those errors. Earlier author/independent source and results remain separately identified in the handoff.

## Evidence and limits

The handoff contains the independent constructor, runner, complete original and corrected attempts, one full positive report, partial-refusal evidence, exact source/input hashes and the frozen 42-file evidence manifest. The evidence manifest SHA-256 is `bb7798ca6a9aec00821efe380b64dca3342df6e4f604831f61eb3f1e46b674ee`. The reviewer and author worked as separate roles in the same actual Linux x86-64 / CPython 3.12.14 environment.

This review establishes the declared CPU admission behavior. It does not establish native capture, numerical accuracy, positional correspondence, original-source equality, full R07, another operating system or a broader release. Separate publication review passed 35 checks on the exact tree integrated by PR #210. All 58 affected methods and the documentation checks passed on actual main `cbed653208d4d9a4f1a669e94dc05fca4571d005`. [Publication review](evidence/PUBLICATION-REVIEW.json). [Integration evidence](evidence/INTEGRATION.json). Final archive restoration and saved delivery remain separate closure evidence.
