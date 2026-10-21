# Bounded reach metadata scan continuation

This records a scoped implementation checkpoint, not complete reach acceptance.
Implementation `1c340903c7a82ac38e7ac9a3e00acc35986f129d` keeps the existing
100,000-operation request limit and all frozen source and acceptance inputs.
The next full-recording blocker remains inside independent reference work.

## Actual change

[JSON preflight](../../../ontokin/json_limits.py) now reuses the encoded size of
an exact sequence of at most 64 strings, each at most 128 characters. The
sequence includes repeated field names, exact-clock strings and carrier
identities. Nested sequences combine only within those fixed bounds. The
original shared 256-entry cache charges lookup, promotion, insertion and
eviction through the same request callback. A hit removes the repeated Unicode
and escape scan; a miss executes the original character checks. Long strings
retain the ordinary scanner and its unchanged checkpoint cadence.

Every logical value and repeated occurrence still takes the complete walk.
Numeric finiteness and integer-width checks, exact container/scalar types,
entry counts, depth, cycles and the final encoded-byte limit remain mandatory.
Only immutable string sequences are cached; containers and numerical values
are not trusted through a cache hit. Pending references are bounded at 64 per
nesting level and do not copy string contents. A changed string changes the key.

The [GLB encoder](../../../ontokin/gltf.py) also forwards the original work
object to authored-clock rational serialization. The previous call omitted
that argument and could create separate arithmetic work for each clock. This
fix accounts for that work within the original request instead of replenishing
it. Encoding order, metadata content and binary buffers remain unchanged.

## Measured full-recording comparison

Both development measurements used the unchanged P01 source, a three-second
endpoint, 2 fps, no helpers, and default tolerances. Both already included the
authored-clock work fix. The comparison isolates the text-scan change.

| Stage | Before text reuse | After text reuse | Removed operations |
| --- | ---: | ---: | ---: |
| Complete encoding | 10,952 | 8,159 | 2,793 |
| Complete bounded GLB reading | 10,170 | 1,658 | 8,512 |
| Combined | 21,122 | 9,817 | 11,305 |

Each JSON measurement returned exactly **517,025 bytes and 17,471 logical
entries**. The two instrumented, unvalidated full GLBs were byte-identical:
566,956 bytes, SHA-256
`760219341932962e670dc39f0bb7c1abbd1bc13602bdd75d32409871eac724ad`.
These bytes were captured inside encoding for comparison; neither failed
request returned a successful delivery. Both full attempts exhausted the
original request at 100,001 operations. After reuse the independent check
advanced further, into `ReachReference._source_basis`.

The preserved profiling wrapper records actual callback sites and text. Its
`text_callbacks.kind` field identifies direct key calls only when their caller
was the old `object_keys` function; after batching its `value` label includes
field names too. The measured counts and exact text remain valid, and the
comparison above uses actual shared operation counters rather than that label.

## Successful clean-commit prefix

A separate run on the clean implementation commit exported P01's **0.25-second
prefix at 60 fps**, with no helpers and unchanged tolerances. It completed
source construction, recording and the independent supplied-byte checker at
**86,292 shared operations**. It retained 16 keys, checked 96 carrier poses and
90 complete interval certificates, and passed complete source-boundary
histories and source geometry/material/provenance comparison.

The resulting GLB is 228,688 bytes, SHA-256
`4e1fe8b3d4c9a9f3f134158c4d0956fb3bd470a522e972b59adc0ad255135a6c`.
This is current prefix evidence only. Actual native/browser execution for these
new bytes, the full source and Agent corpora, full compatibility and the release
audit remain separate. The [first native/browser evidence](../reach-first-destination-validation/README.md)
retains its earlier artifact and numerical basis without being relabeled.

## Executed checks and preserved attempts

The [new regressions](../../../tests/test_json_text_reuse.py) cover byte identity,
shared authored-clock work, nested/repeated metadata, exact byte/entry limits,
long strings and wide schemas, a smaller cache, changed and invalid strings or
numbers, depth, cycles, cancellation identity, the unchanged operation limit,
and invalid supplied bytes after warming the reader cache.

- `python3 -m unittest discover -s tests -p 'test_json*.py' -v`: **28 passed**.
- `PYTHONPATH=tests python3 -m unittest test_export test_reach_recording_budget.BoundedSchemaReuseTests -v`: **29 passed**.
- `profile_metadata.py <checkout> <fresh-directory> 3`: the compared full runs
  failed at the original budget, with the measured stage results above.
- `profile_metadata.py <checkout> <fresh-directory> 1/4 60`: the identified
  clean-commit prefix passed.

All executed repository inputs remained stable during each measurement/check.
The interpreter was CPython 3.12.14. The first profiler setup incorrectly
targeted a locally imported reader symbol; it stopped before export. The first
new hostile-reader test asserted the adapter code in the transport-code field;
the reader rejected the artifact correctly, and the assertion now inspects
`diagnostic.details.export_code`. Both failed attempts remain preserved.

[execution-001.tar.xz](execution-001.tar.xz) contains 22 regular files: raw
profiles, exact dirty patches, both compared full byte streams, the successful
prefix, test logs and before/after input receipts, profiler/archive scripts and
the internal file manifest. Every archived member was checked against its byte
length and SHA-256 after creation. The archive is 83,440 bytes, SHA-256
`0ead3bff74a89fd8224da1fbdd8ad4f2b6bb20d1df9b1f12c6b0657c73c0733e`;
[archive.json](archive.json) records that receipt. The full product goal remains
open.

After archive creation, the documentation preservation/navigation checker also
passed: 29 preserved sources, 233 sections and 1,051 local links, with no
failures. Its separate [execution receipt](documentation-verification.json) and
[raw result](documentation-result.json) retain that later check without changing
the archive.
