# Fresh-chat recovery exercise

Worker: `fresh_chat_exercise`, started without the parent's conversation
history. Input: the candidate checkout, its stable entry file, and a read-only
request to recover current work, identify the next action and explain recovery
from a lost merge response. The worker made no repository or remote changes.

## Observed behavior

The worker explicitly read all eight startup files, the C263 task/requirements/
plan and all three repository skills. It recovered C263 under scope252 as the
active workflow task and identified the source hinge observer as a separately
queued scientific step. It correctly stated that the observer must not start
during or automatically after C263.

Live read-only observations found main at
`bbe30e2f5863d743bd2393466341511b4924ad9d`, the work branch at the published
plan commit `bd26f6e814b89158bfff0c9d96f5b9bd14f20501`, open scope252, no open
PR, and no main lease holder. Local source edits were correctly identified as
uncommitted candidate work. The worker distinguished exposed write tools and
repository permissions from operations actually exercised.

The tool's actual check and brief ran on Linux/CPython 3.12.14. The worker
treated them as structural/local checks, not a remote CI or product pass.
The main entry URL was absent before integration; this was correctly retained
as an expected pre-integration state, not described as a delivered workflow.

## Navigation defect corrected

The documentation index's current-checkpoint paragraph still requested C261
delivery and C234 cleanup. The Director corrected that paragraph to the
verified completed state and linked C263/CURRENT. The worker reread it and
confirmed the correction. Corrected docs/README.md SHA-256:
`4100c343da6df4b858598d202c31624be4dbf1c98ca9815398596a2634c6c5e0`.

Historical sections retain their original observations. The correction affects
the section explicitly labeled current, preventing an old task from taking
precedence over the new owner request.

## Interrupted-write response

The worker's recovery procedure retained intended base/head/tree, target PR
and operation; inspected live PR merged state, merge SHA, main and ownership;
continued verification if the merge already existed; and reconciled new work
before retrying if it did not. It did not interpret timeout or lease expiry as
proof of failure or stopped execution.

## Qualification limit

This is an actual isolated worker reading the candidate and live repository,
not a new user-created browser conversation after publication. It supports
instruction usability and recovery decisions in the available environment.
It does not guarantee behavior in every ChatGPT product surface or install
tools. The final integrator verifies that the published main entry and linked
records exist after merge.
