# Retained C257 evidence

`EVIDENCE-LOCATIONS.json` maps every retained audit file to its original relative
audit path, exact byte length and SHA-256. A `retainedPath` is relative to this
directory. A `repositoryPath` names exact bytes already retained elsewhere in
the same repository. The latter avoids copying the unchanged proof inputs.
Files marked `createdInRepository` were authored directly here and have no
invented audit origin.

The independent [retention manifest](independent-review/REVIEW-RETENTION.json)
requires 49 exact files. All are present through the location map, including
the three executed review scripts/results/logs, reviewed reader bytes or their
exact current repository counterpart, original failed inputs, a changed-owner
fixture, source witnesses and final approval. Original Markdown audit notes
are saved with a `.md.txt` suffix, retaining identical bytes while leaving old
relative links uninterpreted.

The full-size result JSON files preserve actual observations and refusal
outcomes. The earlier 85/90 and 106/106 runs remain separate from the final
107/107 run. The original author lexer failure, five independent reader
findings, independent baseline-harness failure and structural I/O failure are
all retained. Later success does not rewrite those outcomes.

## Recover the original review layout

To inspect an audit in its original layout, choose a new empty scratch
directory. For each location-map entry with `originalPath`, copy the named
retained/repository bytes beneath `<scratch>/audit/<originalPath>`. Verify its
length and SHA-256 before use. Repeated locations may copy the same retained
payload; no source or evidence bytes need reconstruction from prose.

The preserved independent scripts use the following sibling Git worktree
names. Restore the relevant exact commit using the repository history before
executing a script in the copied audit. Never execute in the retained evidence
directory: the scripts write fresh result files beside themselves.

| Preserved script | Scratch worktree | Exact reviewed commit |
| --- | --- | --- |
| `c257-reader-review/attempt-01/review_controls.py` | `<scratch>/c257-review` | `055d1e83f33586e488a35961d29f405b2884beea` |
| `c257-reader-review/attempt-02/review_controls.py` | `<scratch>/c257-review-c415fd7` | `c415fd752def78524cc1a8520e42887570933ff4` |
| `c257-reader-review/attempt-03/review_controls.py` | `<scratch>/c257-review-final` | `499a19d030a06609564390877a596d53dc015a7a` |

The current authored suite is simpler to rerun from the restored repository
using the command in the component README. The saved reviewer results already
establish what ran; a future replay is a new observation, not a replacement
for these immutable receipts.
