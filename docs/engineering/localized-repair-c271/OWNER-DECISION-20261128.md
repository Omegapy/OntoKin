# C271 close-out: the owner's decision of 2026-11-28

On 2026-11-28 (UTC), C271's pre-merge work had run for eight days. The owner judged that process out of
proportion to the task, asked "Can we do just merge like normally?", and then selected "Just C271's
result". This record states what that decision means. It is the owner's direction, and it governs C271's
remaining requirements.

## What merges into main

C271's own result: the H22.02 isolated missing source import-digest control. R01 and R02 were met on
2026-11-20 ([results](RESULTS.md)).

The merge carries:
- the files of this directory as they stood at the result's delivery record, commit `88bc8b51`;
- C271's task records under `docs/workflow/tasks/C271/`, updated for this close-out;
- this decision.

All of it is documentation. **Main's code and tests do not change.**

**One difference from those files.** Two GitHub API snapshots,
`evidence/independent-review/PUBLISHED-CANDIDATE.json` and `PUBLISHED-EVIDENCE-STATE.json`, held commit
metadata with the owner's full name and email. In main's copies those values read `<owner-name>` and
`<owner-email>`. The digests that the audit records give for the two files are the originals' digests;
the originals stay unchanged on the old branch.

## How the remaining requirements close

- **R03.** The merged result is documentation-only. For that, the project's [check table](../../../AGENTS.md#verify-the-actual-change)
  requires the documentation verifier and the workflow check, and both run on the close-out.
  - The independent candidate review passed on 2026-11-20.
  - By this decision, the complete routine driver and the complete affected observer regression are
    not required, because the merge changes neither code nor tests.
- **R04.** A normal pull-request merge into main, followed by the same two checks on main.
- **R05.** Local-mode closure: the push, these records, and the scope issue closed with the completion
  record.

## What does not merge

Phases P02 to P38 do not merge. They are the work that followed the result to meet the pre-merge checks:
- the current-host readback contracts `ontokin.current-host-readback/0.1.0` and `0.2.0`;
- their implementation, preparation and host qualification;
- gate MR's two attempts and P37's correction.

They stay unchanged, with their records, on branch `work/c271-missing-import-digest-control` and in
draft [PR274](https://github.com/Omegapy/OntoKin/pull/274), for history. Nothing is deleted. None of
their claims becomes a claim of main.

## Limits

- This close-out qualifies nothing new. It merges the evidence that R01 and R02 already established.
- Main's routine, tests and their outcomes are unchanged by it.
