# C196 handoff tools

These tools package an exact committed source tree. They do not decide whether
the accepted-revision experiment passed or whether a candidate was integrated.
The coordinator supplies those findings in the current handoff controls after
reconciling the actual repository head and its evidence.

## Inputs and output

Prepare a separate controls directory containing:

- `README-START-HERE.md`: the current outcome, essential recovery instructions,
  remaining gates and the next useful action
- `HANDOFF-C196.md`: source, evidence, integration and provenance details
- `CHECKPOINT-C196.json`: finalized current machine-readable state
- `NEXT-TASK.md`: the reviewed next task for the delivered outcome
- Optional small current receipts under `evidence/` and previews under `previews/`

The checkpoint must contain these fields with actual observed identities:

```json
{
  "schema": "ontokin.c196.handoff/0.1",
  "finalizationPending": false,
  "repository": {
    "commit": "EXACT_FINAL_40_CHARACTER_COMMIT",
    "tree": "EXACT_FINAL_40_CHARACTER_TREE",
    "branch": "main"
  }
}
```

The placeholders above are documentation, not valid package input. Add the
actual outcome, verification receipts, remaining failed or unrun gates and
inherited-evidence labels. Finalization means the handoff state is complete;
it does not imply a full product release or passing legacy regression.

Keep large evidence archives in the committed source. The ZIP contains one
repository bundle with the complete current tree and its retained evidence.
It does not need an earlier handoff ZIP. The outer package contains only current
controls and helper files, avoiding another copy of the large source payload.

## Build after final integration and verification

The checkout must be clean and at the exact final commit. Commit these tools
and the recorded-audit entrypoint before final packaging. Use an external new
staging directory and a new ZIP path.

```sh
python3 -IB docs/engineering/accepted-revision-c196/handoff_tools/build_handoff.py \
  --repo /absolute/path/to/repository \
  --commit EXACT_FINAL_COMMIT \
  --branch main \
  --controls /absolute/path/to/current-controls \
  --staging /absolute/path/to/new-handoff-directory \
  --output /absolute/path/to/OntoKin_C196_Handoff.zip \
  --retain-refs /absolute/path/to/retained-checkpoints.json \
  --history-snapshot /absolute/path/to/identified-history/source/snapshot.json \
  --receipt /absolute/path/to/handoff-build-receipt.json
```

Use `--branch main` only for an observed main commit. The default restored
branch is `snapshot-c196`, which makes no main-integration assertion.

`--retain-refs` accepts either a JSON mapping of exact
`refs/checkpoints/...` names to commit IDs or a snapshot with a `checkpointRefs`
mapping. Repeat the option to preserve additional identified worker histories.
Every retained object must exist. Existing local heads, remote-tracking refs
and checkpoint refs are also retained under explicit checkpoint names. Their
names do not claim those remote refs are current. The builder never updates
the source checkout or its refs; it adds packaging refs only in a temporary
bare repository.

When a retained checkpoint's objects are absent from the working checkout,
`--history-snapshot` verifies that identified snapshot's bundle hash and size,
then imports its objects only into the temporary packaging repository. Its
checkpoint refs and declared boundaries are retained. The final bundle deduplicates
those objects with the current source; the old handoff ZIP is not included and
is not needed to restore the new package. Omit this option when every needed
object is already available. The final descriptor records which identified
history bundles supplied objects.

The source descriptor declares the exact retained shallow boundaries. Older
parents beyond those boundaries are omitted. The complete current source tree
and every tree reachable through the retained refs are included. No synthetic
commit is substituted for a real source identity.

## Verify, restore and replay

From the extracted handoff, verify its exact inventory:

```sh
python3 -IB tools/verify_package.py /absolute/path/to/handoff --require-finalized
```

The same verifier accepts the ZIP path directly. It rejects changed bytes,
missing or extra files, duplicate ZIP paths, unsafe member paths, symlinks,
competing top-level handoff controls and checkpoint/source identity mismatches.
The package manifest omits its own hash to avoid a recursive digest.

Restore the exact source in a new or empty directory:

```sh
python3 -IB source/restore.py /absolute/path/to/new-checkout
```

The restore verifies bundle bytes, advertised refs, exact HEAD and tree,
Git object integrity and clean checkout state, without a network or external
object alternates. Its existing-destination guard preserves other work.

Perform one recorded-only audit, using a replay destination outside the handoff:

```sh
python3 -IB tools/replay_recorded.py /absolute/path/to/new-replay-workspace \
  --repo /absolute/path/to/new-checkout
```

Omit `--repo` to let the wrapper restore the source first. It verifies the
committed `evidence/RECORDED-EVIDENCE.json` descriptor and the named archive,
extracts exactly its declared regular files and original modes into `work/`,
then calls the committed C196 `run_transition.py audit --work ABS --out ABS`
entrypoint. Unsafe paths, duplicates, undeclared files, links and mismatched
bytes or modes stop extraction. The replay reads retained numerical and provenance evidence. It does not request
new native construction, saved-scene simulation, receiving jobs or author work.
Python 3.12, Git and the recorded audit's NumPy dependency must be available.

Store the restore and replay receipts separately from the immutable package.
The build receipt explicitly records that those two checks still need execution;
successful ZIP hashing alone does not prove source restoration or the experiment.
