# C258 independent structural review

**Disposition: approved for the finite structural scope at commit
`2bca9f7d2cba8996043bbfeae0c2855def5d7076`.** The reviewed `follows.py` is
37,435 bytes with SHA-256
`397413d7c403693a349075711bc3dd77fab863d200b06a979cec2f0112114937`.
Its tree is `f14f27adc531a1de1d532b050fdbc5d134166024`.
There is no remaining structural blocker identified by this review.

This reviewer did not author or edit the reader. The review covers resource and
input boundaries, dependency admission, field origins, prohibited execution
paths, and public refusals. The separate reviewer owns numerical correctness,
follow semantics, and source/artifact mutation expectations. This disposition
does not substitute for those results or for repository integration and final
handoff validation.

## Finding and correction

One concrete I/O refusal defect was reproduced on the corrected semantic
candidate `1dfe9d022d0774e311a873ee5eb7a8ba33aab3be`, reader hash
`aea52fc143378ecc8a8237b732fd68ba4647958d04c75e3a086db1e2f51e9225`.
An ordinary repository path naming a self-referential symlink (`loop -> loop`)
caused Python 3.12 `Path.resolve()` to raise an uncaught `RuntimeError`.
The public API did not convert that exception into its documented `Fault`.
`SYMLINK-LOOP-ORIGINAL.json` preserves the observed exception and exact input
recipe. Its result remains a failure; it has not been rewritten as a pass.

The author added `resolve_path()`, which catches `RuntimeError` only around
`Path.resolve()`, and routed all three reader resolution sites through it.
Arbitrary reader `RuntimeError` exceptions are not broadly masked. The exact
production and authored regression changes are in
`reviewed-io-correction.diff`.

`probe_symlink_loop.py` reran the same filesystem recipe against the final exact
bytes. The API now raises `Fault` with code `IO`. The CLI exits with status 1,
prints a `REFUSED`/`IO` JSON object, retains `executionAllowed: false` and
`realTrialSuccess: null`, and emits no traceback or stderr. Results are in
`SYMLINK-LOOP-CORRECTED.json`. The worktree remained clean.

The original synthetic symlink was removed only after recording its target,
original failure hash, and reproduction script in
`SYMLINK-FIXTURE-LIFECYCLE.json`. The corrected probe uses a temporary directory
and confirms fixture removal. No project or inherited files were removed.

The preceding semantic correction reserved intrinsic instance names and
restricted assignments to supported declared or writable fields. Its exact
nine-line production delta is retained in `reviewed-correction.diff`; its
semantic acceptance belongs to the independent semantic reviewer.

## Dependency and execution boundary

The reader imports only Python standard-library modules. It has no product
parser/evaluator imports, expected-answer sidecar imports, process launch,
network or model calls, native trial, or rebuild route. Its sole dynamic
execution loads the C257 helper only after fixed-size and SHA-256 admission.
The pinned helper is 35,942 bytes at
`c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1`.
It is read with a 35,943-byte ceiling and validated before `compile`/`exec`.

Five independent helper controls passed on the semantic candidate and were
rerun on the final candidate because the dependency resolution callsite
changed. Missing, oversized, and symlink helpers are refused before opening;
a same-size altered helper is refused after one bounded read and is never
executed; the exact pinned helper loads after one bounded read. Original and
final reports are `HELPER-PROBES.json` and `FINAL-HELPER-PROBES.json`.
Changed helper input bytes and both drivers are retained. These five controls
do not claim numerical or source-semantic coverage.

## Resource and refusal assessment

The C257 dependency limits the two source files to 65,536 bytes and 8,192 tokens
each, depth 32, 128 objects, and 64 keyed entries. C258 bounds follows to 128,
aggregate expression work to 4,096 steps, helper calls to 64, and parameter
dependency depth to 32 with cycle checks. Follow graph traversal uses a finite
visited set. Source generators and admitted helper returns remain finite.

The 64-character numeric lexeme limit is followed by explicit exponent
admission in [-400, 400] before powers or rational construction. Nonzero values
also pass the documented adjusted-exponent bound. Numeric zero does not bypass
the explicit exponent limit. The projection seed examines exactly three
candidates; this review checked bounded work and truthful method labels, while
the separate reviewer owns rounding and comparison mathematics.

The helper bounds GLB input to 4 MiB and JSON to 2 MiB. Relevant follow rows have
exact fields and bounded counts; vectors and quaternions have fixed widths and
finite scalar checks. Historical source and GLB reads check fixed sizes before
reading at most size plus one, then check hashes. The public wrappers normalize
the documented ordinary structural, arithmetic, recursion, inherited-helper,
and I/O exceptions; the observed resolution gap is now corrected.

## Origins and authority

Follow fields come from the explicit source follow and its admitted parameter,
initializer, helper, and generator dependencies. Ownership supplies identity
and lexical context; it does not supply a follow parent or rigid offset.
Source witnesses retain actual file and UTF-8 byte spans. Artifact observations
retain the artifact hash and actual JSON pointers. Missing direct artifact
follow-definition and source-span authorities remain explicitly absent.

Raw artifact APIs remain untrusted. Source/artifact comparison invokes the
pinned helper's binding checks before reporting verified source association.
Only exact historical input admission can set `historicalInputsBound`.
The comparison allowance is labeled a C258 policy and makes no exporter error
bound claim; raw artifact quaternions are not silently normalized.

Output envelopes retain the explicit nonclaims for complete source/glTF
validity, complete C255 semantics, joint-wide authority, execution, real trials,
rebuilds, and release qualification. This review adds no authority in those
areas.

## Retained evidence and freeze

`REVIEW.json` records exact reviewed identities and observed results.
`ORIGINAL-SOURCE.json`, `original-source/`, `corrected-source/`, and
`final-source/` preserve the reviewed source checkpoints. The final contract,
field-origin note, and pinned helper were verified byte-identical to their
already retained versions. `MANIFEST-SHA256.json` covers every other regular
file in this audit directory. No symlink or source edit remains in the review
outputs. The parent owns integration and durable packaging of this evidence.
