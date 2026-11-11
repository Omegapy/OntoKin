# C196: promote a repaired revision in the accepted store

Reconcile the actual C195 merge, acceptance, evidence archive and current
integration lease before work. Read GOAL, AGENTS and STATUS. Restore and hash
recorded evidence; do not repeat completed author trials to recover a thread.

## Question and prior coverage

Can the accepted OntoKin design advance from the preserved 375 mm revision H
to the already accepted 365 mm repair G, then reject a request based on the old
revision without disturbing the new accepted design? This qualifies the
accepted-source workflow required by GOAL. It introduces no new geometry,
language feature, backend or authoring comparison.

The earlier controls remain authoritative:

| Existing evidence | What it established |
| --- | --- |
| C193 `T01-invalid-edit-rollback` | Reject an initial-overlap candidate while preserving accepted case A. |
| C193 `T15-atomic-publication-failure` | An injected error at state-file replacement leaves A accepted; a renamed candidate directory is not acceptance. |
| C193 `T16-stale-revision` | Reject an expected revision of 64 zeroes against accepted A before native execution. |
| C193 namespace controls | Reject each incompatible C191/C193 store namespace without native execution. |
| C195 ownership recovery | Reject the malformed candidate in a copied H store, preserve H, and construct valid G and regenerated H in separate fresh stores. |

These cases are specified in
[C193 lifecycle fixtures](../guide-repair-c193/native/lifecycle/frozen/lifecycle-fixtures.json)
and recorded in its [42-case result](../guide-repair-c193/native/lifecycle-results/summary.json).
The [lifecycle runner](../guide-repair-c193/native/lifecycle/checker/run_lifecycle.py)
seeds `ok-A-1`, requires every attempt to be unsuccessful and uncommitted, and
requires the original state bytes to remain unchanged. Its stale case supplies
`"0" * 64`; it does not first promote a distinct valid revision. The
[namespace checker](../guide-repair-c193/native/lifecycle/checker/check_store_namespaces.py)
contains only the two incompatible-store rejects. C196 adds the successful
H-to-G transition followed by rejection of the real, formerly accepted H
revision. It does not repeat the earlier failure matrix or claim that generic
transaction rollback was untested.

## Freeze the exact continuation

Use a byte-identical copy of C195's OntoKin `accepted-run/store`, including its
recorded ownership-rejection receipt. Retain the accompanying accepted H source,
original acceptance record and full prior artifact closure. The original C195
evidence remains immutable. Use C195's actual accepted `authors/ok/repaired.ok`
as G, not a newly edited source. Verify these source identities:

| Revision | SHA256 |
| --- | --- |
| H, preserved 375 mm | `2143515f358e36c1dd9a1deef83dba2519a99be6141b64d8bd9dae987761fbd0` |
| G, repaired 365 mm | `ba105a8ca6e9c19dfd06fabd7a06a2254c4ba14d76042dfa88ca365d5de6f7ee` |

Before native work, an independent reviewer must approve the input manifest,
state/artifact snapshots, protocol and exclusive execution ledger. Pin the
unchanged C193 source/runtime/contracts/readers, C195 acceptance and delivery
identities, and the qualified Blender executable. Preserve every C195 numerical
and provenance gate. The copied state must resolve to H's retained `source.ok`,
canonical input and manifest; the recorded negative must show zero native work
and preservation of that state. Reuse this rejection evidence rather than
execute it again.

## One promotion, stale rejection and readback

1. **Promote G in the copied accepted store.** Invoke the existing transaction
   interface once with the exact G source and `expected_revision=H`. Use the
   real native constructor, without test hooks or substituted artifacts. Record
   the command, receipt, time, costs and before/after inventories. Require
   `successful=true`, `committed=true`, `previous_revision=H` and
   `accepted_revision=G`.
2. **Prove one coherent accepted state.** The resulting `state.json` must name
   G and a new artifact directory. Its canonical-input hash and manifest hash
   must match the actual retained files; manifest and retained source must
   identify G. All files that existed before promotion remain byte-identical,
   with unchanged modes and sizes, except the intentionally replaced
   `state.json`. Keep its exact prior bytes in separate evidence. Old H source,
   artifact closure, acceptance and rejection receipt remain intact. Enumerate
   every added attempt/artifact file. Review the unchanged sole `os.replace`
   commit point; reuse T15's failure evidence without claiming a new crash or
   concurrency experiment.
3. **Reject the real stale revision.** Submit the preserved valid H source
   against the now-G store with `expected_revision=H`. Require
   `C193_E_STALE_REVISION`, the actual source span and publish-phase diagnostic,
   `successful=false`, `committed=false`, and both revision fields equal G.
   Require zero scheduled native substeps, native elapsed time and native output
   bytes, no new staging/artifact output, and unchanged G state plus both H/G
   artifact closures. Only the separate failed-attempt receipt may be added.
4. **Regenerate through accepted-state readback.** Resolve the authoritative
   state pointer, read G's retained `source.ok`, hash it and copy those exact
   bytes to an independent input location. Use that readback as the source of
   one clean build in a fresh store. Do not select the original prepared G
   source by name. Neither the readback nor the rebuild may change the promoted
   store.

Allow at most **one native promotion construction and one independent clean
regeneration**, including failures, with no automatic retry. Each retains the
1,000,000-operation and 80,000 ms ceilings and 100-second outer watchdog. Reserve
one independent saved-scene replay for each new delivered scene separately;
these two readback executions do not authorize more constructions. Record all
attempts. Stop on the first failed required gate and retain the reached state.
No new authors or direct-Python trial are required for this product-specific
accepted-store qualification.

## Artifact checks and evidence reuse

Use unchanged independent readers for both new deliveries, including every
one of the 481 samples, unrelated parts, source and implementation provenance,
and saved-scene correspondence. Canonical input, native transforms, raw GLB and
final GLB must equal one another and C195's accepted G files byte for byte.
Require independent replay of each newly produced `.blend`; its identity may
differ, so prior saved-scene evidence cannot substitute for that replay.

When raw/final GLB hashes and their destination-profile/checker bindings match
C195 exactly, reuse the matching accepted Khronos, Three.js, Blender-import and
visual receipts. Publish a receipt-to-artifact hash map and call this inherited
evidence, not a new receiving execution. No new receiving/import/render jobs
are needed for identical files. A changed GLB or incompatible receiving binding
fails this predetermined reuse gate: stop and propose a separately reviewed
validation plan. Do not weaken equality or add unplanned executions to rescue
acceptance.

Publish the independently reviewed transition result, explicit construction and
replay accounting, inherited-evidence map and complete handoff. This closes
only the observed accepted-revision workflow. General contact, production
backend expansion, comparative advantage and the 30–50-task study remain
deferred. Preserve the inherited FAILED legacy driver/tail, 4,239 distinct
passing methods and thirteen torque methods NOT RUN.
