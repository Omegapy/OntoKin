# C047 evidence guide

The [capture report](checkpoint-047-l03-capture.md) and [handoff](HANDOFF-047.md) describe the current result and next bounded task. [The archive record](checkpoint-047.json) binds the exact ordered ZIP parts; [the manifest](checkpoint-047-evidence-manifest.json) binds every member by relative path, byte length and SHA-256.

From a complete checkout of the final C047 publication, run the unchanged existing recovery utility with fresh external output paths:

```bash
python3 docs/engineering/reach-recording-validation-2026-10-23/checkpoint-032-recover.py \
  --checkpoint docs/engineering/reach-recording-validation-2026-10-23/checkpoint-047.json \
  --manifest docs/engineering/reach-recording-validation-2026-10-23/checkpoint-047-evidence-manifest.json \
  --output /tmp/ontokin-c047-evidence \
  --receipt /tmp/ontokin-c047-recovery.json
```

The utility verifies all parts, the joined archive, exact membership, path safety, ZIP CRCs, every member hash and the restored bytes. It does not execute any archived script or product request. Both output paths must be new. This byte restoration does not claim preservation of filesystem timestamps.

| Restored directory | Contents |
| --- | --- |
| `c047-execution/` | Unchanged external capture driver, pair runner, active window, raw stock/capture streams and exits, complete source snapshots, failed original request reports, 154-key ledger, 311 ordered-cache snapshots, exact failure locals and unvalidated GLB. |
| `c047-recovery/` | Complete source recovery, authentic Git import, original remote observations and held-runtime bindings. Temporary authenticated download URLs are excluded. |
| `c047-driver-review/` | Independent exact preparation review and its 21 source/contract input bindings. |
| `c047-independent-comparison/` | Independent original pair audit, result, raw streams, command/input records, review and preserved failed audit attempt. |
| `c047-lifetime-review/` | Original source preparation, independently derived current coefficient/cursor census, source/data bindings and bounded lifetime review. |
| `c047-preparation/` | Root reconciliation records and disclosed transport/read preparation failures. |

The archive preserves original records and their original absolute command/input paths. Those paths are provenance, not instructions to overwrite the restored source or rerun a request. The independent comparison's original scripts are bound evidence; review their location assumptions before any separately authorized replay.

The captured GLB is **unvalidated reader input** from a failed original request. Neither it nor the first 153 provisional key returns may be presented as an accepted export. Exact archive verification establishes retained-byte integrity, not missing release roles or elapsed neutrality.

Actual published-core documentation and archive verification, independent final review, and final publication readback are separate from the archived product pair. They are recorded in `checkpoint-047-validation.json` and its appended validation directory.
