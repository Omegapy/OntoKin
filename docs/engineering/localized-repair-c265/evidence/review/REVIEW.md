# C265 independent code review

**Verdict: approve the exact candidate below for Director integration.** No
unresolved finding remains within the authorized source observer scope. This
is a code and source-control review; the Director still owns publication,
conditional integration, actual-main checks, packaging and saved delivery.

## Reviewed inputs and independence

Reviewer: `/root/independent_review`, separate from the implementation owner
and the independent broad-control author. The read-set is retained in
`INPUTS.json`; the published requirements/plan basis is
`38abfd44437958bd513e00a9e07115059dcc626c`. I read the complete initial source,
then each material change through candidate 5, the independent test source,
and relevant adopted lexical, visibility, identity and numeric provisions.

| Reviewed input | Bytes | SHA-256 |
| --- | ---: | --- |
| `source_hinges.py` | 37,570 | `04bea0f7c5f82a3e3e74610d3ee98755f44ed0905566c00eb063647e31abbf9e` |
| `test_source_hinges.py` | 42,875 | `467be9b930a77d6a82b56154c483f92747d554b354a5380687748b4e1a40821a` |
| Unchanged C257 `ownership.py` | 35,942 | `c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1` |
| Reviewer focused controls | See `REVIEW.json` | `e4907e7eba9fae0a3cc01151917d2980749d301f19e718384ca08a20188e45c7` |
| Reviewer boundary controls | See `REVIEW.json` | `88733c8b816188d5182ea451f9d396960c80047d50899783b39c10a2a8199cb1` |

Expected truth came from C260 and supplied source bytes. Reviewer controls
use only the public observation function and Fault type. No product compiler,
evaluator, exporter, producer data, artifact, baseline answer table or observer
internal supplied expected hinge values or associations. Static code review
necessarily examined implementation details without treating them as an oracle.

## Findings resolved

The first focused run retained three accepted namespace ambiguities: an import
key colliding with a class definition key, an action name colliding with an
object name, and an action key colliding with an object key. Each had returned
an apparently complete eight-hinge observation. Candidate 2 added complete
module and scene namespace accounting. The exact failures, input pairs and
initial source snapshot remain in `run-01`; none were overwritten.

Subsequent review tightened the classification of zero or materially nonunit
axes as malformed while retaining explicit unsupported refusal for valid
nonbasis axes. The exact six signed basis axes remain the entire admitted
axis set. A tolerance is used only to classify otherwise rejected axes under
the adopted validity rule; it does not admit, normalize or compare hinge data.

Candidate 3 added token-kind checks for consumed membership types, helper call
punctuation and the helper return keyword. Candidate 4 enforces public access
for an external override of the keyed membership parameter actually used to
construct identities. A private internal default remains legal. These checks
address facts consumed by this observer without claiming full source validity.

The implementer then demonstrated a complete-set defect in the unchanged C257
lexer: a valid bare-CR line-comment terminator could hide a second hinge and
return eight records instead of sixteen. Candidate 5 adds an explicit
unsupported-form refusal on that precise comment-token boundary, before
lexical observation. The original candidate 4 evidence is retained with its
author in `bare-cr-omission`. Reviewer controls verify the refusal and ordinary
CRLF acceptance. C257 itself remains byte-identical.

## Actual checks

All final controls below bind the exact candidate 5 and test hashes above.
The environment, input hashes, actual refusals and snapshots are recorded by
the named JSON results; execution used CPython 3.12.14 on Linux x86-64.

| Evidence | Actual result | Coverage and limit |
| --- | --- | --- |
| `../independent-controls/run-06/results.json` | 49 methods passed, zero skips; 189 calls, 62 observations and 127 typed refusals; zero host exceptions | Independent source-only cohort, numeric conversion and bounds, exact fields, identities, endpoint visibility, overrides, 128 hinges / 256 referenced sites and refusal boundaries. Reviewed evidence, run by the separate control author. |
| `run-04/RESULTS.json` | 45 / 45 passed | Reviewer public-API probes for lexical kinds, namespaces, hidden declarations, overrides, source byte spans, allowed pose witnesses, invalid versus unsupported axes, bare-CR refusal and CRLF acceptance. |
| `boundaries-02/RESULTS.json` | 9 / 9 passed | Exact site ID 32-component admission and 33-component refusal; rendered site path 512-scalar admission and 513-scalar refusal; dependency binding cases. |

The boundary run accepts the exact pinned dependency and refuses a missing
file, wrong size, same-size wrong hash and a symlink, all as `INPUT_BINDING`,
without exposing partial records. Static review confirms the loader executes
the same bounded bytes it hashes rather than rereading an unchecked import.
The source API does not resolve arbitrary ambient inputs or perform network
access. Exceptions in dependency access are translated to typed refusals.

The recorded boundary layout copies were renamed to data snapshots after
observation so they cannot enter ordinary Python discovery. Their exact tested
paths, bytes and hashes remain in `DEPENDENCY-LAYOUT.json`; the temporary test
symlink was removed and retained as `symlink.json`. This cleanup changed no
observed input bytes and performed no repository or dependency mutation.

Commands used from the repository root:

```sh
python3 docs/engineering/localized-repair-c265/evidence/review/run_review_controls.py --out docs/engineering/localized-repair-c265/evidence/review/run-04
python3 docs/engineering/localized-repair-c265/evidence/review/run_boundaries.py --out docs/engineering/localized-repair-c265/evidence/review/boundaries-02
```

Earlier focused results are preserved: run 01 passed 31 / 34 with the three
namespace failures; run 02 passed 34 / 34; run 03 passed 43 / 43. Boundary run 01
passed 9 / 9 before the control runner added automatic cleanup of its own test
symlink. Boundary run 02 verifies the final control bytes. The independent
cohort retains its own original fixture failures and corrected later runs.
None of these earlier results qualify changed source or test bytes.

## Decision and remaining limits

The implementation reconstructs all hinge occurrences within its explicitly
finite supported source forms, retains definition and occurrence identities,
uses source byte witnesses, enforces consumed endpoint visibility and site
compatibility, and refuses unsupported or malformed consumed forms without a
partial qualified set. Exact decimal conversion multiplies the rational unit
factor before one binary64 conversion; numeric resource caps precede expensive
operations. Review found no producer-derived answer path or authority leakage.

Approval is limited to C265's source observer. It does not qualify all four C260
interfaces, artifact agreement, historical byte admission, evaluated site or
world poses, dynamics, native execution, model trials, an accepted revision,
complete source validity, the full C255 semantic surface or a product release.
The pinned lexer's bare-CR limitation is an explicit refusal boundary.

No active reviewer operation, unresolved write, or unpublished file outside
this review directory remains. No Git/index/remote write was performed by the
reviewer. The Director must establish equality between these reviewed bytes
and the frozen published candidate before integration; changed relevant inputs
invalidate this approval until their effect is reviewed.
