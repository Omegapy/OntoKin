# C268 independent control author result

Worker: `/root/reader_controls`. Director: `/root`.
Assignment: independent R01–R04/H01/H03/H04/H26/H27 controls in the shared
`work/c268-historical-endpoint` checkout; no integration or shared-state writes.
Reported assignment base: `5de702710bf913f3c92c24451e9b8161ed431035`.

The final suite passes 34 methods, 130 API calls, zero errors/failures/skips and
zero untyped exceptions. Of 120 historical calls, 12 admit; the 10 raw calls
include 9 successes and one typed field disagreement. Total typed refusals are
109. Code stayed stable during the final direct run and the separate standard
discovery run. Full logs and exact identities are in `run-03/results.json`,
`run-03/unittest.txt` and `discovery-01/RESULTS.json`.

Checked final identities:

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `endpoint_reader.py` | 14883 | `f615f14f5d4bcee3a3ecdb20466fd60b0a04df2dcd13095d993baf20b1430086` |
| `test_endpoint_reader.py` | 51947 | `1a30beb61e33bbe597f5987be005f66e20f6f53c70f1913f7c0c4a553357691e` |
| `endpoint_control_fixtures.py` | 9181 | `b062555ea7816cb8425b1d73db949974838d6e00afe549dce91ab2b9ad22439d` |

Expected identities, fields and site facts were derived from original source
bytes and C260, independently of the new reader. A pinned independent C266
recipe helper supplies altered provenance only; no product producer executes.
The final source/GLB recipes, input hashes and unique changed byte snapshots
are preserved. Failed run-01 retains its 12 test-author errors and exact checked
code. Run-02 remains as the intermediate passing result. No implementation
failure was found by the exercised controls.

Actual mode-000 access failed at effective UID 1000; injected permission and
I/O failures are labeled separately. FIFO controls use five-second subprocess
deadlines. Read-race tests are deterministic interpositions rather than broad
concurrency qualification. Six injected comparison refusal categories check
outer propagation; one actual C267 field mismatch checks exception translation
using exact unchanged captured code.

Owned outputs are the control suite, fixture recipes, CONTROL-COVERAGE.md and
this evidence directory. No index, commit, branch, remote, STATUS or CURRENT
operation was performed. No child worker or persistent process was launched.
The Director owns independent review, full affected cohort, exact-candidate
publication/integration and final delivery. The control author's work is frozen
pending a concrete review finding.
