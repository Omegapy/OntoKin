# C265 independent source control runs

Independent worker: `/root/reconcile_state`. All writes were limited to the
independent test file and this evidence directory. No product compiler,
evaluator, exporter, artifact, baseline answer table or new observer internals
supplied expected hinge fields. Expected IDs and associations were specified
from C260 and actual supplied source bytes. Numerical expectations use a
separate high-precision decimal calculation and fixed binary64 values.

## Final observed result

Run 06 passed all 49 methods with zero skips in 3.036 seconds on CPython
3.12.14, Linux x86-64. Its 189 public API calls returned 62 observations and
127 intentional typed refusals. No host exception escaped in these calls.
Exact environment, input hashes, command and each supplied source hash/size
are in `run-06/results.json`; the complete unittest output is retained.

The checked observer SHA-256 is
`04bea0f7c5f82a3e3e74610d3ee98755f44ed0905566c00eb063647e31abbf9e`.
The checked test SHA-256 is
`467be9b930a77d6a82b56154c483f92747d554b354a5380687748b4e1a40821a`.
The immutable C257 dependency remains
`c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1`.

`CONTROL-COVERAGE.json` maps all H01–H28 groups. The source-only requirements
of H06, H09, H11 and H15–H19 were exercised. Other assigned groups have only
their source portions exercised. H03, H10, H21, H23 and H26 concern other
interfaces and remain unrun here. This is not complete C260 four-interface
qualification. No artifact comparison, historical file admission, source
execution, pose evaluation, native application or model trial was run.

## Retained attempts and corrections

| Run | Actual result | Resolution |
| --- | --- | --- |
| 01 | 48 methods; 1 failure and 5 errors | Five intended valid membership fixtures removed `middle` but retained an override targeting that missing key. The fixture editor now updates references to a surviving key. The failure overrequired a source hash after the source byte resource bound. Oversized bytes retain their size; hashing beyond the bound is not required. |
| 02 | 48 methods passed | Corrected fixture and bounded-hash assertions on the initial implementation. Subsequent independent review required namespace and token-kind defenses and a more precise invalid-axis refusal category. This earlier pass does not qualify later bytes. |
| 03 | 48 methods; 1 failure | On the revised implementation, the new ownership relocation fixture correctly refused an unavailable direct ordinary part as `UNSUPPORTED_SOURCE_FORM`. The test had overrequired `MALFORMED`; C260 H20 permits this structural refusal. The assertion now allows either explicit structural category. |
| 04 | 48 methods passed; zero skips | The candidate 3 bytes and their exact test snapshot passed. Later review identified the private membership access boundary and required a focused correction. |
| 05 | 49 methods passed; zero skips | Candidate 4 passed the complete suite, including private owner membership default admission and external private-parameter override refusal. |
| 06 | 49 methods passed; zero skips | The unchanged suite passed candidate 5 after the separate reviewer demonstrated the pinned lexer bare-CR comment omission and the implementer added a precise unsupported-form refusal. The reviewer owns the targeted guard case. |

Each run retains its original log, source/input hashes and exact test/observer
snapshots. Run 02's test snapshot was reconstructed from the retained run 01
test plus the two documented corrections, then proved identical to run 02's
already-recorded SHA-256 before saving. Run 02's observer was identical to
run 01 and likewise checked against its recorded hash.

Starting with run 03, the runner captures the implementation bytes before
loading and executes exactly those bytes. Evidence hashes and snapshots bind
that captured input, so subsequent edits cannot relabel an earlier run.

The H09 assertion now distinguishes a zero or materially nonunit invalid axis
(`MALFORMED`) from a valid unit nonbasis axis outside this finite profile
(`UNSUPPORTED_SOURCE_FORM`). Exact admission remains the six signed basis
vectors. No general normalization behavior was added to the test's promised
support.

## Reproduction

From the repository root, run the following with a new output directory:

```sh
python3 docs/engineering/localized-repair-c265/test_source_hinges.py --evidence-dir /tmp/c265-source-controls-fresh
```

The evidence directory must not already exist. The runner refuses to overwrite
an earlier run. The Director owns final Git publication, actual-main checks,
handoff packaging and completion; this control report does not certify them.
