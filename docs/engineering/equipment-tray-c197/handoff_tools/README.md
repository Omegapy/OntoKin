# C197 handoff tools

These tools package the exact committed C197 source and its retained Git history.
They do not decide whether C197 was admitted or whether a product release passed.
The coordinator supplies the current decision and integration receipts.

The tools are a separately identified adaptation of C196's portable tools. All
older tool bytes remain unchanged. C197 uses its own control filenames and
schemas. Current branch observations use `refs/checkpoints/c197-observed/` so
that inherited checkpoint references retain their original targets.

## Seal an exact source

After restoring the source, the builder is at
`docs/engineering/equipment-tray-c197/handoff_tools/build_handoff.py` in that
checkout. The extracted package itself contains only the verification, restore
and replay entrypoints. Run the builder with explicit paths:

```sh
python3 -IB /absolute/path/to/clean-checkout/docs/engineering/equipment-tray-c197/handoff_tools/build_handoff.py \
  --repo /absolute/path/to/clean-checkout \
  --commit EXACT_40_CHARACTER_COMMIT \
  --branch snapshot-c197 \
  --controls /absolute/path/to/current-controls \
  --staging /absolute/path/to/new-package-directory \
  --output /absolute/path/to/new-handoff.zip \
  --receipt /absolute/path/to/build-receipt.json
```

The controls must contain `README-START-HERE.md`, `HANDOFF-C197.md`,
`CHECKPOINT-C197.json`, and `NEXT-TASK.md`. They must identify the exact source
commit/tree and set `finalizationPending` to false. Existing output files and
nonempty staging directories are rejected. The source must be clean. No earlier
top-level handoff controls or duplicate archive payloads are accepted.

The builder takes tool bytes from that commit, creates a complete source bundle
with the declared shallow history boundaries, and verifies the directory and
ZIP inventories. Its external receipt hashes the ZIP. The ZIP cannot include
its own checksum without changing that checksum.

## Verify, restore and audit the delivered handoff

From an extracted package, use new or empty output locations:

```sh
python3 -IB tools/verify_package.py /absolute/path/to/extracted-package --require-finalized
python3 -IB source/restore.py /absolute/path/to/new-checkout
python3 -IB tools/replay_recorded.py /absolute/path/to/new-audit --repo /absolute/path/to/new-checkout
```

The verifier also accepts the ZIP path. The restore checks the bundle hash,
advertised references, exact commit/tree, Git objects, and clean checkout without
network access or external object alternates. It does not change remote Git refs.

The replay wrapper verifies and extracts the unchanged 911-file C196 archive,
then runs its recorded-only audit using the delivered source. It requires Git,
Python 3.12 and NumPy; this continuation uses CPython 3.12.14 and NumPy 2.3.5 on
Linux x86-64. It requests no new native construction, saved-scene simulation,
receiving job, author or full regression. Its scope is inherited C196 evidence,
not a C197 tray qualification. Read the C197 decision separately.

The complete handoff must pass one fresh offline source restoration and the
recorded audit after sealing. Retain their exact-source receipts outside the
immutable ZIP, or include prior validation receipts while clearly identifying
the unchanged payload they checked. A successful package check does not erase
failed, pending or unrun product gates.
