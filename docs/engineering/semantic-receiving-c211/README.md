# C211 Blender receiving proof: failed/partial

C211 attempted the next C210 gate: receive the exact accepted semantic export in one pinned Blender build. The actual import produced useful measurements, but the finite receiving proof **failed**. Main retains this result and its evidence; the prototype remains held in [draft PR #155](https://github.com/Omegapy/OntoKin/pull/155).

All delivered triangle positions/winding, sampled world poses, materials and native object metadata passed their independent comparisons. Imported sphere split normals exceeded the predeclared precision limit. Rendering separately failed because this installed build lacks OpenImageDenoise. No native scene save, reopen or visual review was reached.

Read [RESULTS.md](RESULTS.md), the [independent review](evidence/review/FINAL-REVIEW.md.txt), the [verbatim attempted contract](evidence/CONTRACT-ATTEMPT-1.md.txt) and [current status](../../../STATUS.md). The [held source](https://github.com/Omegapy/OntoKin/tree/cdae8b582a37e37f76f142f07039ba74cedc08ad/prototypes/semantic_receiving_c211) includes an unexecuted denoising correction; that correction does not resolve normal fidelity. The [current held contract](https://github.com/Omegapy/OntoKin/blob/cdae8b582a37e37f76f142f07039ba74cedc08ad/docs/engineering/semantic-receiving-c211/CONTRACT.md) is distinct from the original attempted bytes.

The next bounded action is an explicit normal-fidelity and loss decision, grounded in these measurements, before any further receiving attempt. Preserve the original failure and tolerance; do not retroactively relabel it passed. A second destination and direct-authoring comparison remain later stages. C199/C200 stay closed; C201 admission remains deferred.

[Publication and actual-main verification](evidence/publication/INTEGRATION.json) record the documentation-only integration and lease release. The held prototype remains unmerged.
