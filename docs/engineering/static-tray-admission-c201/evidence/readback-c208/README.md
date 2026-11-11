# C208 readback binding evidence

C208 adds a CPU-only boundary between an accepted C201 transaction and future
Khronos/Three.js readback. It checks real retained files and supplied observations;
it does not run a probe or authenticate a child process. Read the
[component contract](../../READBACK-BINDING-C208.md).

## Reviewed source and results

The independently reviewed component is local commit
`a645731147e4ce95ddaab8132c5a261cc3a9f44a`, tree
`77679024f09a647905c2d97331fc751c5d0ce73b`.
[Independent review](independent-review/REVIEW.md) approves this component only.
Its [machine record](independent-review/REVIEW.json) binds 66 exact component,
dependency, test and contract files separately from three context documents.

[Candidate validation](validation/CANDIDATE-RESULTS.json) records 223 current
C201 methods, including 52 new readback methods; 78 source/compiler methods;
and 43 core cases with 694 assertions. All passed. The independent reviewer
passed 63 additional controls. All 301 locked inputs, four frozen protocol
documents and 1,033 historical files remain exact; these preservation sets overlap.

All agents used the available Linux x86-64 CPython 3.12.14 environment.
Process creation was blocked during component controls. There were zero native,
receiving, Node, lifecycle or timed-author starts. Production-shaped fixtures
remain synthetic. The inherited full regression stays FAILED: 4,239 distinct
passing methods and thirteen torque-read methods not run after the unchanged
30,000 ms setup timeout. That full suite was not rerun.

## Original failures and fixes

[Draft findings](implementation/DRAFT-FINDINGS.md), original draft source and
complete logs preserve the two public-error normalization failures. The original
draft ran 51 methods with two errors. The corrected 52-method run passed. An
independent draft inspection also exposed the 28–30 second timing gap; a focused
regression control now rejects it. No historical evidence was rewritten.

## Remaining gate

The C208 job/0.1 is a binding-preparation contract. It does not yet name the
validator, Three.js and GLTFLoader entry points within the sealed dependency
closure. An independently reviewed versioned contract must supply those exact
paths and hashes, reject ambient imports, and include this helper in the future
wrapper dependency closure. Actual C201 wrapper/probe, authenticated supervision,
complete coordinator, real host sealing, readiness and admission remain pending.

Publication and resulting-main evidence are recorded separately when observed.
