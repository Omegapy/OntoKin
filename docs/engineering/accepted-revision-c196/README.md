# C196: promote and reuse the accepted repair

This bounded continuation checks whether OntoKin can replace its accepted
375 mm design with the already qualified 365 mm repair, reject an edit based
on the former revision, and regenerate from the saved accepted source.

Preparation and execution are separate. No result is implied by a frozen
protocol or a runnable script. The predecessor's full requirements are in
[C195 NEXT-TASK](../ownership-recovery-c195/NEXT-TASK.md), and the exact C196
sequence is in [PROTOCOL.md](PROTOCOL.md).

`run_transition.py prepare` verifies a completed C195 recorded-only replay,
copies the accepted store with original file modes and freezes its inputs.
`run_transition.py execute` requires an independent hash-bound review and a
C195 merge receipt, then reserves its one permitted execution exclusively.
`run_transition.py audit` only reads retained results; it never invokes Blender.

The experiment preserves the original 0.2 mm mapping limit and all numerical
and provenance checks. Identical GLBs reuse their exact prior receiving and
visual receipts. Each newly produced native scene requires its own independent
replay. General physics and the inherited failed regression remain separate.
