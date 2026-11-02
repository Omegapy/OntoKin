# Independent resulting-main review 01

**Verdict: passed.** The actual resulting main `b193828ba7e08439f04344405e732c57b3ff75a4`, tree `72116c83bc5ac3b2c17886384030ab3e52a10978`, passed 222,486 checks with zero failures. This review was performed by the independent corpus author, who did not perform root's integration.

## Exact checks

The read-only audit verified all 12,244 tracked source files / 706,217,349 bytes, actual filesystem modes, full source-to-native byte equality, and 10,028 native objects by recomputed Git SHA-1 and SHA-256. The native scope comprises 9,358 unique current source blobs, 667 current tree objects and three identified commit objects. It does not claim an audit of every historical Git object.

HEAD, the complete index and the clean worktree matched the exact resulting commit at the beginning and end. Both C089 `655097f016af17434b9b26fae22491f5f302aa18` and reviewed candidate A `754f72106279abc6c867ab180300f2ba382a3f2d` are ancestors. The native merge has exactly two ordered parents:

1. `5f707369de6cbf67fce2df4dc72ac8ecee3f61a3`
2. `133cff003287ccda44760b95871ed76a5b39b646`

All 10,847 baseline paths remain present. The only changed pre-existing paths are `STATUS.md` and `docs/README.md`. All 1,397 added paths fall within the three declared torque contract, Agent/0.22 schema and C090 engineering prefixes. Every other baseline source byte and native mode is unchanged.

All 399 frozen input files, their global manifest and ADOPTION.md match candidate A exactly by native blob and mode. The full file sizes and SHA-256 identities also match the manifest. The global manifest remains `98df30158c0cd77c542d89652f5dec6b585d03451a06bf7b1baffee0fc2f02eb`; ADOPTION.md remains `488464be47a28d2091a871c987ec83946c046a16738fb6f7c4ec1e6f18d1e93a`.

## Scope and evidence

No production code was imported or executed. No network request, Git mutation, source edit or index update was performed. This check does not establish a later lease release, sealed-package recovery, torque runtime result or product release. Those remain separate observations.

The complete per-file inventory and check outcome are in `resulting-main-review01.json`, SHA-256 `f2e8eae4ec28e23501573c29aafbcee7bfa698862fbc79bcec7fcf20319fd928`. The executed read-only script is `audit_resulting_main.py`, SHA-256 `2fd137cccc0e209f6f1a9cd9edcce37772fe343565824782a683d0193d42e30b`. The audit ran from 2026-11-02T21:46:13.580579+00:00 to 2026-11-02T21:46:18.077390+00:00 in 4.49684 seconds. Root held the worktree/index fixed for this audit window.
