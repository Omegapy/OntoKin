# C256: finite GLB geometry and sampled-motion reader

C256 supplies the artifact traversal missing from the previous offline
checker. It reads the existing C210 binary 3D files, measures eighteen local
triangle meshes and 126 world poses per endpoint, and traces those measurements
to actual binary elements. It separately checks each complete occurrence key
and reused definition key against the exact authored source. The two existing
endpoints pass the unchanged C255 geometry and delivery-pose predicates.

This is a **partial observation producer**. It does not output a complete
C255 observation or qualify the source semantic graph, revision handling,
rebuilds, native execution or a model trial. A passing C256 endpoint establishes
only the finite geometry, sampled transforms and source identity associations
described in the [contract](CONTRACT.md). Comparative advantage is unproven.

## Read and run

1. [Contract and limits](CONTRACT.md).
2. [Field origins](FIELD-ORIGINS.md), including actual binary values,
   interpolated values and source identity joins.
3. [Executed results](RESULTS.md) and the preserved original failures.
4. [Next separate task](NEXT-TASK.md).

All commands run in the assistant's hosted workspace. The module uses only
Python's standard library and does not start another program or access the
network. It writes its result to stdout; collect evidence outside the source
tree.

```sh
python3 -IB docs/engineering/localized-repair-c256/reader.py --repo . --endpoint before > /tmp/c256-before.json
python3 -IB docs/engineering/localized-repair-c256/reader.py --repo . --endpoint after > /tmp/c256-after.json
python3 -IB docs/engineering/localized-repair-c256/test_reader.py
```

The public Python entry points have different authority:

| Entry point | What it establishes |
| --- | --- |
| `measure_glb(raw)` | Actual geometry and sampled transforms from supplied bytes; identity labels remain untrusted. |
| `associate_glb(raw, source_files)` | The same measurements plus full-key and definition associations to one of the two exact frozen source closures. The GLB need not be a historical endpoint. |
| `read_bound_endpoint(repo, endpoint)` | The same traversal and associations after exact historical source and GLB byte admission for `before` or `after`. |

Only the third entry point sets `historicalArtifactBound` true. None sets
`semanticQualified`, `completeC255Observation` or `executionAllowed` true;
`realTrialSuccess` remains null. Valid corrupted GLB payloads can produce
different measurements through the first two entry points. That permits
detection of geometry and motion mistakes beyond rejecting an unfamiliar
hash. The historical entry point rejects those changed bytes.

The producer imports no product parser, evaluator, exporter or C255 expected
function. Its tests import C255 only as an independent consumer of measured
arrays. No sidecar supplies geometry or motion. Exact source pins make the
small identity recipe specific to this already public family; it is not a
general OntoKin parser or unseen evaluation corpus.

Source work is tracked by [scope #241](https://github.com/Omegapy/OntoKin/issues/241).
Publication, actual resulting-main checks and branch cleanup are recorded
separately from author and reviewer source identities.
