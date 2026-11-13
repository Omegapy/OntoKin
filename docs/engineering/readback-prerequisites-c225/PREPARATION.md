# Reproduce the exact prerequisite preparation

The helper recovers this retained Linux environment's exact CPU-readback inputs. It is intentionally tied to the unchanged historical absolute paths and byte identities. A different host must satisfy the existing checks or receive a separately reviewed portability decision; changing an inventory to describe unverified files is not recovery.

From an identified clean source checkout, first run a dry-run with an external fresh report path:

```bash
python3 -B docs/engineering/readback-prerequisites-c225/restore_readback_prerequisites.py --repo "$PWD" --report /absolute/outside/checkout/readback-preflight.json
```

To install only when both destinations are absent, add `--apply` and use a different external report path. If both locations already contain the complete exact inputs, the helper verifies and reports them without replacing them. Partial, extra, changed or symlinked locations are refused. Reconcile a refusal before retrying; preserve any recorded unknown or failed operation.

```bash
python3 -B docs/engineering/readback-prerequisites-c225/restore_readback_prerequisites.py --repo "$PWD" --apply --report /absolute/outside/checkout/readback-restoration.json
```

The helper starts no Node checker or native application. The focused cohort, when independently selected, is:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_static_tray_readback_v01.ReadbackCPUControls -v
```

C225 ran those same three methods through a reviewed observational runner so the pre-run inventory, process attempts, original test output, source identities and synthetic artifacts were retained externally. That runner does not change the methods, guards or fixtures. Its exact source and commands are in the [saved raw evidence](evidence/RAW-EVIDENCE-LOCATION.json). Do not rerun the focused cohort solely because a handoff is being restored; the next selected task is the aggregate attempt.

The restored prerequisites are runtime dependencies, so their installed directories are not committed or bundled again. Their exact source archive and host record already belong to the preserved source chain. The final source restore and this helper together reproduce the preparation where the recorded host bindings remain valid.
