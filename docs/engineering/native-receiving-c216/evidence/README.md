# C216 observed failed-start evidence

These records describe one known failed native process, not an accepted receiving result. [Results](../RESULTS.md) distinguish passed prelaunch controls from failed and unrun native gates. Exact executed source is `2cb197ffe6047b13c9099f2987049ab0d1a29b2d`; the same tree is held under published identity `53a6e3169edf944180120a14b10ae09fc471cfc8` in [draft PR #165](https://github.com/Omegapy/OntoKin/pull/165).

- [Pre-execution review](PRE-EXECUTION-REVIEW.json) binds the exact source/plan and approves import only.
- [Prepared plan](plan.json) retains exact commands, limits and staged scene-binding rules; its one attempted schedule is closed.
- [Process receipt](import-process.json), [failure traceback](import-native-failure.json), [stdout](import-stdout.log) and [stderr](import-stderr.log) preserve the actual first native outcome.
- [Root stopping record](NATIVE-STOP.json) binds the absent outputs and process-group recheck.
- [Independent failure audit](FAILURE-AUDIT.json) confirms the known failure and distinguishes its static namespace inference from unrecorded runtime attributes.
- [Independent final failure review](FAILURE-REVIEW.json) and [all 26 requirement dispositions](REQUIREMENT-DISPOSITION.json) close this failed scope. The 47 passing audit checks verify failure accounting, not native acceptance.
- [Implementation static review](FAILURE-STATIC-REVIEW.json) records installed package layout without another native process.

The complete source bundle, both prepared runs, exact accepted inputs, importer source archive, independent reference code/controls and original harness failure are retained in the [C216 recovery checkpoint](https://chatgpt.com/library?file_id=libfile_fde3_f-c2d4d4a41da48191aa40ec3a9ef904a9_2ab2a24d43748191957f9bcc356b59de&account_id=personal) and the final handoff identified there after confirmed delivery. Package paths are `workers/native-preflight/`, `workers/native-review/` and `evidence/c216/`. Original absolute paths identify actual execution locations; the handoff retains corresponding package-relative bytes. A prepared plan is never automatic permission to replay an earlier native attempt.

No `received.blend`, native observations, normal-loss result or planned image was produced. No source program or exporter ran. Full product regressions were not rerun for this isolated experiment; historical failures remain unchanged.
