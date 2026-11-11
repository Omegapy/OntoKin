# C198 resulting-main verification

**Result: PASS.** This separate check verifies the fetched merged commit `7e0e7da3dd97779c2c96d4d8a22a72b1282607e2` and tree `9415598f7a136df2fdb2fe4d6c9c11f17bb38bff`. PR #133's merged status was supplied by the parent after its GitHub readback; no new remote status query was performed here.

The detached worktree at `/workspace/scratch/816fbabc1c3c/c198_main_review` remained clean at the exact merge throughout verification. Its complete 13,915-file mode/blob/path inventory equals published candidate `7e22ea8fd18793f5fbb295d713e2b8668ff0c056` and tested local publication `77f50e134bc3533adf782a7e26bf1aa271fd61e4` exactly.

All nine frozen contract inputs match their byte counts and SHA-256 hashes, and the canonical freeze-file-list digest matches. The retained independent review's input-freeze, script, receipt, candidate and 256 passing-check bindings match the merged bytes. These are checks of the prior review binding; the 256 review probes were not rerun or relabeled as fresh results. All 54 inherited refs retain their exact expected targets.

Fresh execution of `python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py` passed: 29 preserved sources and 0 failures; exit code 0. The full stdout/stderr logs are retained beside the machine-readable receipt. The exact Python executable, version, platform, duration and log hashes are recorded there.

This verifier authored part of the semantic contract. This is therefore **not an independent semantic review**; the separate `live_repo_audit` review retains that role. The present task checks resulting-main identity, retained approval bindings and documentation preservation independently of the integrator's execution.

There were zero source fixture executions, native exports, simulations, receiving jobs, timed authors, full regression runs or GitHub mutations. The inherited driver/tail remain FAILED, with 4,239 distinct passing methods and thirteen torque-read methods NOT RUN. Adapter implementation, qualification, tray admission and broader release gates remain open.

Fresh verification assertions: 42. Failed assertions: [].
