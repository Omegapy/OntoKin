# Reproduce the public spacer worker

Each participant command ran in a new QEMU guest. The guest had a serial command channel, its route's read-only C181 tool disk and one disposable ext4 work disk. The shell ran as UID/GID 65534, with only loopback available. The hosted participant also had access to ordinary host tools. Staying on the relay was an assignment constraint. The overall hosted interface therefore remains unsuitable for an unseen comparison.

## Stage and boot

Restore the C181 runtime as described in `operator/c181/README.md`. Use the pinned common volume for OntoKin and the pinned Blender volume for Blender. The public worker checks their SHA-256 digests and the guest initramfs against the C181 execution card. Obtain the public practice, the source checkout and a fresh output directory for each route.

Set `KIT` to the extracted handoff. Set `TOOLS` to the directory with this bridge. Set `PRACTICE` to the public practice directory, `CHECKOUT` to the restored checkout, `QROOT` to the extracted QEMU runtime, `ROLE` to the role, `VOLUME` to its read-only disk, and `BASE` to an existing, empty directory dedicated to that role. Use Linux x86-64 with CPython 3.12.14 and e2fsprogs.

```bash
python3.12 -B "$TOOLS/stage_practice.py" --kit "$KIT" --practice "$PRACTICE" \
  --checkout "$CHECKOUT" --role "$ROLE" --out "$BASE/stage"
python3.12 -B "$TOOLS/public_worker.py" serve --kit "$KIT" --qroot "$QROOT" \
  --tool-disk "$VOLUME" --role "$ROLE" --stage "$BASE/stage" --out "$BASE/run" \
  --seconds 900 --actions 24 --bytes 98304 --invalid 3 --initial-text "$PRACTICE/TASK.md"
```

Run the serve command in a separate terminal or supervised subprocess. Wait for `run/ready.json`. The common task, checker, editable starter and empty submission folder are under `/work` inside the guest. OntoKin uses `JOB=/work/job`. Its Python launcher points to the native CPython on the tool disk. Blender uses `BLENDER=/opt/blender/blender`. For the standalone checker, use `python3.12`.

## Participate

Send one raw model reply per call through stdin. Use exactly one JSON object with a nonempty string field named `command`. Standard JSON escapes support multiline commands and quotes. The bridge also accepts a single unlabelled, JSON or text Markdown fence around the entire response. Prose outside an action is rejected. A final standalone `SUBMIT` is accepted as plain text or within such a fence.

```bash
python3.12 -B "$TOOLS/public_worker.py" action --out "$BASE/run" <<'ACTION'
{"command":"cat TASK.md"}
ACTION
```

A command's nonzero shell exit is returned for a corrective attempt. Every submitted reply consumes one of the 24 actions. Three consecutive malformed replies end a session. The 900-second clock starts as the guest becomes ready, continues between replies and kills the guest during an active command when it expires.

The byte guard admits up to 98,304 bytes across the initial common task, raw replies through the bridge and compact JSON responses. A reply that would exceed the remaining allowance is refused before guest execution. An output too large to return is withheld and the run closes. Fixed terminal notices reporting a byte-limit stop are excluded from the count. The host's model prompt envelope, earlier conversation, tool wrappers and hidden reasoning are outside these measurements. Actual hosted model usage is recorded as null.

## Recover and audit

The bridge retains raw reply text and guest outputs in `transcript.jsonl`, host command dispatches in `dispatch.jsonl`, the input inventory in `configuration.json` and the final disk digest and shutdown result in `finish.json`. Successful submission invokes the C181 collector, which copies the stopped disk, recovers its journal, and extracts regular files in `/submission` from that disk into `run/submission`. All runs, including early stops, leave the untouched final image at `run/worker.raw` in the local session. To recover partial files after a stop, run:

```bash
python3.12 -IB "$KIT/operator/c181/pilot/collect.py" "$BASE/run/worker.raw" "$BASE/partial"
```

Use `check_bridge.py --help` to replay the harmless controls. Give it the same kit, QEMU runtime and both frozen volumes with a new output directory. Each test creates its own guest. The legacy controls under C181 used real Qwen token receipts. They serve only to test the original controller.

The practice evidence folder includes a verified compressed original start and final disk for each participant. Use `xz -dc` to a fresh file and compare its SHA-256 against `disks.json` before independent recovery. The disk without a journal replay is the sealed original.

## Clean rebuilds

Use `rebuild_practice.py --help` with the staged template for the route, the submitted editable source, and the received GLB for the post-run byte comparison. The rebuild script stages only the reviewed source, public ruler and route runtime. All three successful builds began without a GLB. The normal invocation uses a fresh source path. Adding `--same-source-uri` to the OntoKin invocation stages the source under its original guest path. `compare_export.py` compares the complete decoded GLB JSON and SHA-256 of every other chunk. These two OntoKin runs distinguish a change to the source URI in the export metadata from a change to the geometry.
