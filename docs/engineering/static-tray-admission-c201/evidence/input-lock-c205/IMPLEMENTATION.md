# C205 input-lock implementation worker

The bounded component is committed at `28bf6d74f651b22acc0ee5a4154dcd21b861c81b`,
tree `7acaeb92a51d88fd3c10f3edaed72e651eb42cb2`, on
`work/c205-input-lock-4ba2fd`, based on published main
`5183504302ad0c21f1e9e91c6ad146eee64a22c8`. Only three additions changed:
`prototypes/static_tray_admission_c201/input_lock.py`,
`tests/test_static_tray_admission_c201_input_lock.py`, and
`docs/engineering/static-tray-admission-c201/INPUT-LOCK-C205.md`.
No shared STATUS, existing implementation, historical evidence, protocol or
workflow file was changed. This worker neither pushed nor merged anything.

## Implemented behavior

The separate strict JSON validator binds exact protocol/schedule/limits,
independently observed Git identities and actual source/dependency bytes,
required qualified/C201/host roles, dependency graph, expanded commands and
clean environments, distinct initial stores/outputs/environment roots, and one
fixed persistent authority. It rejects old twelve-slot schema, missing/extra
fields, wrong types, changed actual bytes, unsafe paths, replay evidence,
incomplete gate receipts and nonindependent approval identities.

An externally retained frozen TrustedContext pins lock/approval, source,
closure, launch plan and authority identities. Documentation explicitly states
that this component cannot authenticate that context, independently discover
all imports or host aliases, observe Git/current interpreter identity, persist
context across restarts or authorize native work. Fixtures are classified as
fixtures. Every returned native/readiness/admission flag is false.

## Draft findings and corrections

1. Root identified that pre-seeding the graph traversal's visited set with frozen
   inputs skips dependencies reachable only from a frozen role. The corrected
   traversal seeds its frontier with those inputs and starts visited empty. A
   positive control verifies a helper reachable only through the constructor.
2. Root/reviewer independently reproduced POSIX double-leading-slash path
   acceptance. It could disguise an output nested within the repository during
   lexical ancestry checks. Absolute paths now require exactly one leading
   slash; public-validator and context controls reject that spelling. Original
   independent failing controls remain in the review worker's evidence.
3. Reviewer found that the first generic environment shape could not express
   the qualified Blender/Node clean launches. The final schema fixes inherited
   safe native/Node flags, full clean environments, exact stage jobs, distinct
   per-slot environment roots and a singleton bound Node loader. Controls use
   deliberately resealed plans to reject removed safe flags or altered jobs.
4. Reviewer found that forbidding a broad host root made actual /usr, /lib and
   /opt inputs structurally unrepresentable. The final schema treats host_root
   as a namespace and checks actual host/gate input files against writable
   roots. A '/' namespace fixture passes; an input inside the repository fails.
   Alias paths remain conservatively rejected and real alias/bootstrap evidence
   is explicitly a later integration requirement.
5. Additional schema controls reject wrong-type gate maps and multiple Node
   loader inputs before those values can be used.

## Checks and exact boundaries

The final focused run passed 72 methods with no errors, failures or skips on
Linux x86-64 CPython 3.12.14. `git diff --check` passed. The commit changes only
the tested files; final file hashes and command/runtime details are recorded in
`IMPLEMENTATION.json`. The final log is `final-tests.log`; original draft and
intermediate passing logs remain separate.

No Blender, receiver, Node, lifecycle or timed-author process started. Test
launch seams reject attempts to spawn children. No production lock, real host
receipt, independent readiness approval or admission result was fabricated.
Independent exact-revision review, root-run applicable regression/documentation
checks and any publication remain the main integrator's responsibility.

The next coherent implementation increment is C201 transaction/readback
compatibility. Full coordination, actual source/equality/cleanup/promotion
verification, complete current-host sealing, trusted bootstrap and native
readiness remain pending. Historical C199/C200 schedules stay closed and the
inherited full regression remains failed at its original timeout boundary.
