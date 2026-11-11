# Actual stopped C199 native execution

The frozen schedule stopped after N01, the first unexpected result. One native
construction process started and exited with status 1. The retained stderr
records the pinned glTF exporter's `KeyError: 'loglevel'`, following an action
filter callback error. N01 is **REJECTED**. The qualification result is
**STOPPED_AFTER_FIRST_UNEXPECTED_RESULT** and `qualified` is false.

Receiving starts, Node readback starts, delivered controls and accepted
transactions are all zero. N02 through N12 were not started. There were no
automatic retries. These counts describe the completed recorded schedule;
packaging did not launch another application, probe or test.

The process saved `stages/N01-build/scene.blend` before failing. Its retained
size is 547,575 bytes. The archive contains those exact bytes, but the scene's
geometry was not independently verified and it is not an accepted delivery.
No GLB is present in the captured directories. The archive also retains the
empty `stores/ontokin` directory. `MANIFEST.json` explicitly records that its
accepted pointer (`state.json`) and objects directory are absent, together with
the absence of N02–N12 results.

`receipts/` gives direct access to the unchanged qualification result, N01
result, append-only attempt ledger, construction process receipt and separate
stdout/stderr logs. `receipts/driver/` preserves COMMAND, STARTED, COMPLETED,
DISPOSITION and the captured `coordinator.log`. Separate coordinator stdout
and stderr files were not present and have not been manufactured.

`captured-native-execution.tar.gz` includes both complete original directories,
including empty directories, job/source inputs and the saved scene. The tar
uses fixed entry order and a gzip header with zero timestamp and no filename.
It preserves observed modes and link types; the manifest records every member's
hash, size and type. Archive headers and payload hashes were inspected without
extracting or executing the scene or captured code. Packaging generated no images.

Modes recorded in tar headers do not guarantee that an arbitrary extractor,
umask, filesystem or Git checkout enforces read-only permissions. Verify bytes,
modes and any link relationships explicitly when restoring this evidence.

The unchanged DISPOSITION names C200 as a separately reviewed exporter
compatibility repair with a newly frozen qualification protocol. This evidence
package neither repairs runtime code nor restarts or reuses the stopped C199
schedule. The frozen input and approval locks remain unchanged.
