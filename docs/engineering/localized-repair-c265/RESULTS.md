# C265 source hinge observer results

C265 implements the independent source-only interface from unchanged C260.
The observer derives hinge occurrences, definitions and ordered endpoint sites
from supplied bytes, including supported changes to names, keys, membership,
axes, limits and initial coordinates. It is isolated under this engineering
directory and does not change product parsers, runtime, exporters or defaults.

## Exact scientific inputs and executed controls

| Input or check | Result |
| --- | --- |
| source_hinges.py | 37,570 bytes; SHA-256 `04bea0f7c5f82a3e3e74610d3ee98755f44ed0905566c00eb063647e31abbf9e` |
| test_source_hinges.py | 42,875 bytes; SHA-256 `467be9b930a77d6a82b56154c483f92747d554b354a5380687748b4e1a40821a` |
| Final independent source suite | 49 methods passed, zero skips; 189 API calls: 62 observations and 127 expected typed refusals |
| Original before/after source observations | Each yields eight hinges, sixteen referenced sites and eighteen objects; hinge identity/numeric projections agree across the original length edit |
| Execution environment | Assistant hosted Linux x86-64; CPython 3.12.14 |
| C257 dependency | Exact 35,942 bytes; SHA-256 `c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1` |

The [final independent run](evidence/independent-controls/run-06/results.json),
[coverage map](evidence/independent-controls/CONTROL-COVERAGE.json) and
[run notes](evidence/independent-controls/RUN-NOTES.md) retain actual commands,
input hashes, snapshots, earlier failures and corrected fixture expectations.
The [source observation receipt](evidence/source-observations/RECEIPT.json) binds
the two full returned source reports to the final implementation.

Independent review approves these exact source/test hashes. The reviewer
passed 45 focused controls plus 9 boundary/dependency checks, with no unresolved
mandatory finding. See the [review receipt](REVIEW.md).

## Preserved findings and scope limits

Independent review found namespace ambiguity, quoted-token syntax confusion,
invalid-axis refusal classification and private membership override access
issues in earlier candidates. These were corrected in the final candidate;
earlier code, inputs and review runs are retained. The pinned C257 lexer also
misses bare-CR line-comment termination. A reproduced additional-hinge omission
is retained under [implementation attempts](evidence/implementation-attempts/bare-cr-omission/FINDING.json).
C265 explicitly refuses that comment form as unsupported before invoking the
pinned lexer. Normal LF/CRLF comments remain supported. The inherited utility
is unchanged. This restriction is visible in the API limits and README.

Some early control failures were fixture mistakes: removing a keyed member
while retaining a reference to it, demanding a hash after the input-size bound,
and over-specifying a structural refusal category. Their original failed runs
and exact test snapshots remain visible. They are not recast as implementation
failures or erased by later passes.

Site pose expressions remain unevaluated byte witnesses. Interface and size
equality establishes source-only ideal compatibility, not manufacturing or
physical alignment. Source/artifact agreement, historical endpoint admission,
full source validity, accepted revisions, edit atomicity, rebuilds, native/model
trials, full C255 semantics and comparative advantage remain unqualified.
The source-only H groups and source portions are enumerated in the coverage
map; no complete four-interface C260 qualification is claimed.

## Regression and delivery gates

The five inherited observer cohorts passed 139 methods on the initial exact
unchanged inputs: C255 31, C256 29, C257 23, C258 28 and C261 28. Workflow and
documentation preservation passed. C253 initially stopped because the shallow
checkout lacked its old pinned Git commit; exact Git objects were restored
from GitHub and all fourteen corpus bindings then passed. See the
[restoration receipt](evidence/historical-baseline-restoration.json) and
[retained first run](evidence/baseline/CHECKS.json). This does not establish
complete historical graph retention.

Candidate and actual-main verification, independent review acceptance, merge,
branch disposition and saved delivery require separate receipts. A passing
component suite is not an integration or saved-delivery claim. Full product
regression, source execution/rebuild, visual/native checks, compatibility on
other Python versions, model trials and hosted CI are not run for this isolated
increment; historical failed and unrun obligations retain their states.

## Published candidate verification

Candidate `1e5b1c368fabc51ce22be6916aca6464f71f97cf` passes all nine applicable check groups: 188 methods (C255 31, C256 29, C257 23, C258 28, C261 28, C265 49), fourteen C253 corpus bindings, workflow validation and documentation preservation. Exact commands, environment, read-set and logs are in [candidate checks](evidence/candidate/CHECKS.json). Independent review hashes equal the published source/test bytes.

Exact tree reconstruction detected newline translation in six evidence files in the initial publication. The byte-preserving correction is part of this candidate; both commits and the failed verification remain in [publication recovery](evidence/publication/NEWLINE-RECOVERY.json). No scientific code changed during this correction. Integration, actual-main verification and saved delivery remain outstanding.
