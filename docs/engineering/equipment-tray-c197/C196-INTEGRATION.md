# Completed C196 integration

C196's accepted experimental result was still an unmerged draft when this
continuation opened the recovery handoff. This record closes that integration
before C197 begins. The completed native work was recovered and audited without
repeating author, construction, saved-scene or receiving trials.

| Identity | Observed value |
| --- | --- |
| Previous main | `055ebf330a77513c47bad4bb4c092f54190ff8d5` |
| Reviewed C196 candidate | `b5e8094f0af5557e8d52541884750a8febbc0e6f` |
| Candidate tree | `6988167ed8a6ab5238569a9b4b4b0cb91dd6198e` |
| New integration lease commit | `33ece59660d1c7fa82669e687708cc733f03494a` |
| Actual merge of PR #130 | `6cbcf9c8c136659def1aac94829330cb81872511` |
| Actual merge tree | `13eb2463217d3021c7783c6c6d8be749e8c2e145` |

The previous lease expired at `2026-11-11T01:01:06.131683+00:00`. Reconciliation
found unchanged main and candidate, with no later published coordination
activity. This did not establish the absence of unpublished work. The new owner
`c197-integration-7f9a31` acquired a bounded lease through a conditional nonforce
update, verified its exact STATUS readback, and preserved the original candidate.

The fresh independent [candidate review](evidence/c196-candidate-review/REVIEW.json)
verified all 911 archive files and their modes, all nine acceptance-record hash
bindings, and the two retained 481-sample runs. The documentation/preservation
checker passed with 29 preserved sources. All 13,789 earlier files except the
three current navigation/status documents retain their Git blobs and modes;
47 additions are confined to the C196 engineering record. Historical runtime,
tests, contracts, tools, workflows and 1,691 earlier evidence files are unchanged.

PR #130's stale preparation text was corrected and its draft status cleared.
The PR metadata initially continued to show the old base SHA after the lease
update; a direct Git fetch established actual main at the new lease commit
before the protected merge. The merge checked the exact candidate head. The
[merge receipt](evidence/C196-PR-MERGED.json) confirms actual merged state and
the returned merge identity. The lease and operation results are retained in
[C196-INTEGRATION-OPERATIONS.json](evidence/C196-INTEGRATION-OPERATIONS.json).

On actual main, the ordered parents are the new lease and the reviewed C196
candidate. The independent [resulting-main review](evidence/c196-main-review/REVIEW.json)
verified all 13,838 candidate files except STATUS by exact blob and mode. STATUS
differs only in the lease paragraph. Fresh documentation and recorded-audit
commands both returned zero, and the checkout remained clean. Both retained
runs preserve their 481 samples and 0.07451646802035088 mm continuous mapping
bound under the unchanged 0.2 mm allowance. C197's prerequisite is satisfied.

The inherited legacy driver and supplemental tail remain **FAILED**, with
**4,239 distinct passing methods and thirteen torque-read methods NOT RUN**.
This continuation ran no full regression and claims no complete release,
general contact, concurrent-writer safety, live destination physics or
comparative authoring advantage. The new lease continues only for the declared
C197 scope and must be released after its verified publication.
