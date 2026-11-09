# C184 hosted participant isolation

**Blind admission is blocked on the hosted launcher tested November 9, 2026.** Both fresh participants used a host shell to read a marker from the other route, a coordinator marker and an evaluator marker. An unseen repair on this host could therefore expose the other participant’s work and the scoring materials.

The coordinator generated four independent 32-byte random markers and recorded their digests before dispatch. One child was assigned the Blender label and one the OntoKin label. Each got an empty history with the same requested settings. Each copied its own marker to an echo file and returned all four digests. An independent worker checked the original files and both echoes. Across the two children, all six protected reads succeeded. [Registration](evidence/registration.json) · [Blender request](evidence/blender/request.json) · [Blender reply](evidence/blender/reply.txt) · [OntoKin request](evidence/ontokin/request.json) · [OntoKin reply](evidence/ontokin/reply.txt) · [Independent inspection](evidence/independent-inspection.json)

The inspected launcher exposed no per-child setting to restrict tools or files. Both children also reported seeing delegation and GitHub tools. The probe exercised the shell only. The stop rule deferred outbound access, nested delegation, attempt caps, active deadlines, and post-submission custody. No unseen case was created, timed or scored. [Launcher inventory](evidence/host-interface.json) · [Decision and control outcomes](evidence/result.json)

To verify the archived result, run this command from the root of the restored or cloned repository with Python 3.12:

```bash
python3.12 -IB docs/engineering/hosted-boundary-c184/operator/verify_boundary.py docs/engineering/hosted-boundary-c184/evidence
```

The command checks the public receipts against the registered hashes and the independent inspection. The two public [C183 spacer repairs](../hosted-spacer-c183/README.md) remain available for native export checks. C185 starts with evidence of a changed launcher or enforcement policy. [Admission procedure](ADMISSION.md)
