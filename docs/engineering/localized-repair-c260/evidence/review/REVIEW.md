# Independent C260 contract review

**Decision: approve the corrected contract for integration as documentation.**
No hinge-observer implementation or implementation qualification is approved.
The reviewer did not author the contract. The exact seven approved files are
bound in [REVIEW-BINDING.json](REVIEW-BINDING.json). The approved contract SHA-256
is `39bf90c51256cb392b0b639c36f3325c76f8919bbea4e3e572937e9834f8cd6c`.

## Basis for the decision

The finite subset covers both frozen C253 endpoints: eight hinge occurrences
share one class-member definition, with sixteen source-associated endpoint
sites. The declared axis is a signed coordinate basis; limits and initial
values are literal Angles. The contract derives source facts independently,
keeps GLB rows as claims until comparison, and reserves historical admission
for exact original source/artifact hashes.

The review independently read the adopted core, construction and transport
rules, all three actual `.ok` inputs and both actual GLB byte streams. It did
not import the product parser, evaluator, exporter, C255 expected values,
producer sidecars or candidate reader code. The reviewer constructed occurrence
and definition identities directly from source module, class, root, collection,
literal-key, part, site and joint declarations. Actual artifact values and
source mappings agree with those fixed-input associations.

| Review obligation | Observed result |
| --- | --- |
| Exact source/specification/dependency/artifact bindings | All twelve match; five matching C253 pins also agree |
| Source byte witnesses | All 37 source hashes, byte slices and selected occurrences match |
| Hinge associations | All eight source-derived rows agree with all sixteen artifact rows across before/after |
| Object associations | Both complete eighteen-object maps match source; every repeated node/program mapping agrees |
| Declaration and definition spans | All 36 object instances across both artifacts identify the actual source class and declaration bytes |
| Canonical program identity | Both manifests/revisions independently recompute from exact source bytes |
| Missing artifact authority | No direct site table or joint/site definition/span fields are invented |
| Numeric meaning | Exact decimal × exact binary64 Pi64 / 180, rounded once; original 45 degrees gives `0x1.921fb54442d18p-1` radians |
| Future controls | All 28 listed cases remain explicitly planned and unrun |
| Final freeze | All seven final file hashes unchanged after inspection |

The [fixed-input inspection](INSPECTION.json) contains 242 passing assertions;
the [object-source mapping inspection](MAPPING-SPANS.json) contains 142.
These are document and fixed-byte audit assertions, not 384 implementation
tests. The source baseline remains `003b3a7827486405c3d00f039c1c9746c9be75fc`,
tree `325c7e50b42000e7c2976e3dd8c3babcec2649ba`; later root lease work changed
coordination state without changing any bound input.

## Findings corrected before approval

**R1 — authored stable keys need their adopted domain.** The first draft used
a generic 512-character text cap without separately imposing the adopted
ASCII 64-character stable-key grammar. Its H19 case also mentioned quotes as
if they were legal key content. The corrected contract preserves
`[A-Za-z0-9][A-Za-z0-9._-]{0,63}`, adds explicit invalid-key refusal, and limits
the larger cap to other consumed text. Legal dots remain opaque key content.

**R2 — empty keyed input was ambiguous.** The first draft did not state a
minimum input cardinality, while pinned C257 utilities reject an empty keyed
literal. The corrected contract explicitly selects 1–64 entries. An empty
typed keyed value remains valid language syntax but unsupported by this finite
observer. H19 now requires that distinction. Original draft files, hashes and
findings are retained in the author's attempt01 evidence.

## Numeric vector for the future H07 check

The already-required one-round rule can be distinguished from a common
premature-rounding implementation with `1.1[deg]`. Independent exact rational
arithmetic gives binary64 `0x1.3a8cdb28e1358p-6`. Computing
`float("1.1") * (Pi64 / 180)` instead gives
`0x1.3a8cdb28e1359p-6`. This vector is recorded in the inspection report to make
H07 concrete during implementation. It is a review arithmetic result; no
candidate implementation has been run on it.

## Limits and remaining gates

The contract explicitly leaves site-pose evaluation, world alignment, combined
pose authority, motion, complete semantics, accepted revisions, rebuilds,
native behavior and model comparisons unqualified. Its equality policy is
limited to the literal/basis subset and does not import the follow component's
quaternion tolerance or claim general exporter accuracy.

Root still owns applicable documentation preservation, guarded publication,
resulting-main checks, complete archive restoration and the confirmed saved
handoff. The reviewer's own inspection mistakes are preserved separately in
[REVIEWER-ATTEMPTS.md](REVIEWER-ATTEMPTS.md); they caused no contract changes or
product executions.

