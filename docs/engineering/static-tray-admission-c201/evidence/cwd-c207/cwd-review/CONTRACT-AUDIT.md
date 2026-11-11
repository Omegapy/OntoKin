# C207 independent working-directory contract audit

## Decision

Use each slot's bound stage-output directory as its planned child working directory. Require exact equality among `commands[slot][stage].cwd`, the command's `output`, and `outputs[slot][stage]`. Each expanded job argument remains the absolute `<output>/job.json` path. Construction and receiving jobs must bind `output_directory` to that same path. No qualified worker, receiver or supervisor edit is needed.

This is a compatibility correction within the four approved C201 protocol documents. ADMISSION section 6 already requires exact expanded commands, environments and distinct output paths while retaining the qualified constructor, receiver and supervisor by identity. It does not require repository cwd. The incorrect repository-cwd requirement originated in the C205 input validator, and C206 deliberately exposed it rather than rewriting the binding.

## Per-stage evidence

| Stage | Observed qualified behavior | What C207 can establish |
| --- | --- | --- |
| Construction | `supervisor.run_process` resolves its stage, passes it as `subprocess.Popen(cwd=stage)`, and records it. `worker.main` rejects when `job.output_directory` resolves differently from `Path.cwd()`. | Planned cwd, job output and supervisor observation can bind the same stage. |
| Receiving | The same supervisor applies. `receiver.main` rejects when `job.output_directory` differs from its current directory. | Receiving plan, receiver job and process evidence can bind its distinct receiving stage. |
| Node | The current C205 plan binds a separate future C201 probe, absolute loader/script/job paths and clean environment. C201 `readback.mjs` and `format_check.py` are not yet implemented. The historical probe reads absolute job paths and writes `job.result`; it does not itself check cwd. | Consistent future Node launch-plan paths only. This does not establish C201 probe behavior, result provenance, output confinement or actual-delivery compatibility. |

The qualified supervisor resolves a stage before launching. Since the validator admits only canonical absolute, non-symlink, disjoint output directories, resolving a valid stage must preserve its exact planned string. Binding both the outer process observation and underlying supervisor receipt to the same command eliminates the C206 fixture bridge's two different cwd meanings.

## Review boundaries

The `C201-NATIVE-CWD` blanket production-purpose rejection can be removed only after the path disagreement is corrected and independently checked. A `production-inputs` purpose is a classification of supplied bindings, not authorization to launch. Synthetic records carrying that purpose in CPU controls remain synthetic fixtures. The false native-authorization/readiness/admission results must remain false.

True process provenance, real host and dependency closure, complete aliases, durable trusted bootstrap, one-use coordinator sequencing, deadlines around actual processes, the separate Node/readback implementation, native readiness and final admission are still open gates. C199 and C200 schedules must remain closed. No new native, receiving, Node or lifecycle run forms part of this review.

## Planned independent controls

Exercise the modified validator and transaction code using temporary files, fixture geometry and blocked child-launch APIs. Verify each stage independently, including repository-cwd regression rejection, cross-stage aliases, wrong job paths, changed trusted launch plans, replaced output-directory identities, construction and receiving observation mismatch, accepted-source integrity and conditional promotion behavior. Intercept the actual qualified supervisor's `Popen` boundary and the worker/receiver main-function prefix without executing a child or Blender operation. Bind the exact candidate code, test helpers, qualified roles and frozen documents in the final result.
