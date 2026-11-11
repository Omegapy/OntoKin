# C200 handoff tools

These tools package the exact committed C200 source and its retained Git history.
They do not qualify the adapter, admit a tray, run native work, or decide whether
a product release passed.
The coordinator supplies the measured result, remaining gates and integration receipts.

The tools are a separately identified adaptation of C199's portable tools. All
older tool bytes remain unchanged. C200 uses its own control filenames and
schemas. Current branch observations use `refs/checkpoints/c200-observed/` so
that inherited checkpoint references retain their original targets. The incoming
C198 descriptor contains 69 retained checkpoint references; preserve every
reference and exact commit while adding the current C200 observations.

## Seal an exact source

After restoring the source, the builder is at
`docs/engineering/static-tray-exporter-c200/handoff_tools/build_handoff.py` in that
checkout. The extracted package itself contains only the verification, restore
and replay entrypoints. Run the builder with explicit paths:

```sh
python3 -IB /absolute/path/to/clean-checkout/docs/engineering/static-tray-exporter-c200/handoff_tools/build_handoff.py \
  --repo /absolute/path/to/clean-checkout \
  --commit EXACT_40_CHARACTER_COMMIT \
  --branch snapshot-c200 \
  --controls /absolute/path/to/current-controls \
  --retain-refs /absolute/path/to/extracted-c198/source/snapshot.json \
  --staging /absolute/path/to/new-package-directory \
  --output /absolute/path/to/new-handoff.zip \
  --receipt /absolute/path/to/build-receipt.json
```

The controls must contain `README-START-HERE.md`, `HANDOFF-C200.md`,
`CHECKPOINT-C200.json`, and `NEXT-TASK.md`. They must identify the exact source
commit/tree and set `finalizationPending` to false. Existing output files and
nonempty staging directories are rejected. The source must be clean. No earlier
top-level handoff controls or duplicate archive payloads are accepted.

The builder takes tool bytes from that commit, creates a complete source bundle
with the declared shallow history boundaries, and verifies the directory and
ZIP inventories. The explicit retention input detects any changed inherited
reference; all referenced objects must already be available in the restored
checkout or a separately verified `--history-snapshot`. The committed README is
copied to `tools/README.md` and is a mandatory verified package member.
Its external receipt hashes the ZIP. The ZIP cannot include
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
not C200 adapter qualification or tray admission. Read the adopted C198
contract and measured C200 result separately. A recorded-audit pass cannot replace any future
implementation, native geometry, receiving-application or author-exercise gate.

The complete handoff must pass one fresh offline source restoration and the
recorded audit after sealing. Retain their exact-source receipts outside the
immutable ZIP, or include prior validation receipts while clearly identifying
the unchanged payload they checked. A successful package check does not erase
failed, pending or unrun product gates.

## Recovery provenance

C200 retains every reference from the supplied C198 snapshot and all available C199 remote commits. The interrupted C199 turn did not supply a saved handoff. Its original local-only commits are recorded by their observed identifiers in the committed C199 evidence, but missing objects are not invented or advertised as retained refs. The restored exact main source includes the original executable lock, consumed ledger, logs and captured partial scene. The C199 schedule remains stopped.
