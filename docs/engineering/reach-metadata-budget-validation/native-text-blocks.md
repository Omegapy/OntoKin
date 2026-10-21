# Bounded native encoding of metadata text blocks

This is a later implementation and measurement checkpoint. It preserves the
earlier [text reuse evidence](README.md), all frozen inputs, the original
100,000-operation request budget and the shared 256-entry cache. P24 delivery
still exhausts that request budget after progressing further through the
independent check; this record does not claim a successful P24 artifact.

## Exact operation and fixed bounds

The existing JSON walk forms an exact immutable cache key from at most **64
exact built-in strings**, each at most **128 Unicode code points**. Only a cold
cacheable block changes: `json.dumps` with `ensure_ascii=False`, finite-only
encoding and compact separators now performs the block's quoted/escaped text
encoding, followed by strict UTF-8 encoding. This replaces the Python loop over
every character in every short string. The original request is charged before
and after that bounded native operation. A cache hit retains its previous
lookup/promotion behavior; no new cache or increased limit is introduced.

For a block of `n` strings, subtract exactly `2 + n - 1` bytes for its array
brackets and commas. The remaining size is the sum of the complete JSON string
encodings, including every occurrence and both quotes. The maximal allocation
at `n=64` is:

```text
64 × (128 × 6 + 2) + 63 + 2 = 49,345 encoded bytes
```

Six bytes per code point is attained by an escaped control character. Strict
UTF-8 encoding rejects lone surrogates. Long strings retain the original
character scanner. The complete original value traversal still checks every
logical entry, exact type, number, byte, nesting level and cycle. Unchanged
128-entry walk checkpoints, cache bookkeeping and both native-operation
checkpoints use the same caller cancellation and remaining request budget.
Cancellation before encoding prevents the native call; cancellation on return
prevents insertion of a partial cache result.

## Actual P24 request comparison

The three actual Agent export attempts used base commit
`bb06627dc078bcb3a0ea66d3a7bcc5589c67dc38`, the unchanged frozen P24 source,
`end="0.25"`, `fps=2`, `helpers=false` and default tolerances. That base merged
root implementation `a57cdcb432816996b9d3c5905465ef7d575128d9`; candidate changes
were recorded as exact patches. Every run retained its complete Agent exchanges
and stable repository input hashes. All three requests returned the original
100,001-operation resource failure, with no successful artifact publication.

| Measured stage | Existing batch scanner | Rejected schema separation | Bounded native block |
| --- | ---: | ---: | ---: |
| Complete GLB encoding | 16,863 | 23,655 | 7,670 |
| Complete GLB reading | 6,210 | 10,018 | 6,210 |
| Combined | 23,073 | 33,673 | 13,880 |

The retained change removes **9,193 actual shared operations** from encoding.
The rejected alternative flushed field names separately from their values; its
additional small blocks increased work and it was restored before the native
block experiment. Two further isolated JSON microprofiles that flushed nested
containers also regressed and were not applied.

All three encoders produced identical captured bytes: **1,351,904 bytes**, SHA-256
`c0f68194950d9a6e1ede8d0a1a6ecda9cfc38210e8e20e3103740c390d5a7e39`.
These are explicitly unvalidated encoder captures from failed requests, not
claimed delivery outputs. Both JSON passes still report **1,310,058 bytes and
77,454 logical entries**. With the retained change, independent boundary-state
construction finishes at compiler counter 96,094; the request then exhausts
during later independent validation. The Agent's enclosing counter also retains
its original 287-operation offset.

## Regression result and exact raw identities

CPython **3.12.14** executed
`python3 -m unittest discover -s tests -p 'test_json*.py' -v`: **31 passed** in
0.650 seconds. The [raw log](native-text-block-tests.txt) includes the unchanged
GLB/shared-clock test, hostile warm-reader test, complete existing JSON suite,
the exact maximal escaped block, multibyte Unicode, lone-surrogate rejection,
and cancellation immediately before/after native encoding. Input hashes were
stable. The test patch additionally includes the two new regression methods;
the measured production implementation is unchanged from the third profile.

The raw records are retained under the identified `reach-checks` execution
directories. Their durable archive is pending a separately granted archive
window; the identities below allow exact reconciliation without rewriting any
earlier archive.

| Raw record | SHA-256 |
| --- | --- |
| `profile-json-blocks-001/report.json` — baseline actual Agent attempt | `8354bfc909228bc6f736a09b1647bac0960a76bc413a16f50da681e23afb1e7e` |
| `profile-json-blocks-002/report.json` — rejected schema separation | `cdf711d52d0d059780b644bf2071520148624113d918142a0c05a41a04dd3f4d` |
| `profile-json-blocks-003/report.json` — native block actual Agent attempt | `6813483a94ca1d75a35bf01e8334c7a910c94f06a3a58e3d4b2efa302cdcee6b` |
| `profile-json-blocks-003/changes.patch` — measured code change | `dab61cb019e97e40d04b32d10616d3212eee3297227fbbbf8fd58f97b6a055b7` |
| `profile-json-blocks-micro-001/report.json` — rejected child-flush microprofiles | `ba73d88b9e7bfb6146d5ca9bdce49cc7dfe029da61d874a78969690e46e0266c` |
| `json-block-tests-001/report.json` — test execution and input receipts | `364c911577b062d95155de192049cdf276ce0410799a45bca6d1b7766ed75b3b` |
| `json-block-tests-001/changes.patch` — tested code and new regressions | `8ae0aa2ee1f4bbcf18a03e03fe2468ef302b72d60fd6b08eaed63b5fec3a485c` |
| `json-block-tests-001/tests.log` — committed raw test log | `2d4e9210dbafaa82b24cdffcc69ca934aaf0c93ac02d06369b7dbd214373f1a8` |

Full P01 recording, all actual Agent delivery requests, the complete source and
destination corpora, reference/rate acceptance, compatibility and independent
release acceptance remain separate gates. The full project goal remains open.
