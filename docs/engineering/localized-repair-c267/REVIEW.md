# Independent C267 implementation review

**Disposition: approve the inspected finite comparison increment. No blocking
implementation finding remains.** Reviewer: `/root/reconcile`, independent of
the comparator author `/root/comparator` and control author `/root/controls`.
This approves the identified implementation and control bytes for the declared
scope; required regression, integration, actual-main and saved-delivery gates
retain their separate evidence and ownership.

## Exact candidate and evidence

The comparator was published at `2d47c608a953dc0d2ffb09b67e0ce6f720b205eb`.
Its inspected SHA-256 is
`f98b9eab7a7f0cc75afa26eab0b672356d7e3275e3d713d16df214e68e69d71d`
(12,382 bytes). The [review receipt](REVIEW.json) and
[executed review results](evidence/review/run-01/RESULTS.json) bind the complete
review input set, command, interpreter and actual outcomes. Publication of
these same reviewed test bytes at a later checkpoint does not alter the reviewed
implementation; the Director must establish equality before using this review.

I read C267 requirements/plan, unchanged C260 CONTRACT, CONTROL-PLAN and
FIELD-ORIGINS, the comparator, C266 binding, C261 raw reader, relevant C265
source construction/output paths, and the independent fixture/control code.
Pinned dependency byte counts and digests match the reviewed source. No nested
AGENTS instructions apply to this path. The repository session and delivery
skills were explicitly read.

The final independent control-author run passed 25 methods and 123 API calls:
35 agreements and 88 typed refusals, with no failure, error or skip. I audited
that retained evidence rather than representing it as my own reexecution.
All implementation/control hashes and checked-code snapshots match current
bytes. Its preserved input ZIP passes CRC and content hashes; 361 reported
input-byte witnesses resolve to exact retained bytes. Every recorded expected
agreement/refusal matches its outcome. See the
[control-author results](evidence/control-author/run-03/results.json) and
[coverage qualifications](CONTROL-COVERAGE.md).

## Source and association review

The comparator calls the independently bound C266 prerequisite before emitting
comparison records, then checks equality of source/artifact input identities
across the separately read components. No product parser, evaluator, exporter,
motion fit, producer sidecar or expected-answer table supplies a hinge value.
The new component uses only the pinned source, raw-artifact and binding APIs.

Complete source and artifact joint identity sets and independently rendered
path sets must match. Every row is subsequently matched by its full identity
and exact path, so merely preserving the two sets while swapping identity/path
pairings cannot pass. The raw reader separately rejects duplicated IDs/paths;
empty agreement is permitted only when both actual complete sets are empty.

Joint owning objects and class definitions are tied to the complete C266 object
map. Joint occurrence and definition IDs append the literal key to their
separate source namespaces, while display paths append the lexical name.
Endpoint association checks the complete source-derived site record, exact
owning object and class, site key and independently rendered path. It never
splits quoted keyed paths on dots. Parent and child remain ordered and must
belong to distinct source object occurrences.

Raw numeric shape/type/finite/basis/range validation occurs in the pinned
reader. The comparator then requires exact numeric equality. It does not
normalize axes, ignore axis sign, clamp initial coordinates, sort limits or
borrow another component's tolerance. Signed zeros compare equally as C260
requires. Source literals retain C265's one-round canonical conversion.

Typed predecessor refusals propagate with bounded input hashes/byte counts;
unsupported artifact profile refusals remain distinguishable. Comparison
disagreement is `FIELD_MISMATCH`. No failed call exposes qualified hinge records.
The public controls confirm dependency hashes are checked again after a prior
successful call, including same-size mutations and missing/symlinked files.

## Independent supplemental probes

The initial controls exercised one joint definition at a time. I added a small
review supplement to challenge multiple declarations sharing sites. Its fixture
contains two independently specified joint definitions per class, with different
lexical names, opaque keys, axes, limits and initials, instantiated on three
owners with dotted/underscored/hyphenated keys. Expected fields and associations
come from explicit source recipes, not comparator output.

[The review program](evidence/review/review_c267.py) executed seven additional
API calls on CPython 3.12.14 / Linux x86-64. Two agreements and five
`FIELD_MISMATCH` refusals passed. The agreements contain six joints, two joint
definitions and six distinct referenced sites, correctly accounting for shared
sites. Reordered joint/node rows retain exact pointers. Removing an occurrence,
swapping cross-definition IDs or paths while preserving their complete sets,
changing the second definition's initial value, and swapping endpoint pairs
between owners each refuse. Exact inputs are retained in the
[review input archive](evidence/review/run-01/inputs.zip). All reviewed code
remained unchanged during the execution. No failed behavioral probe occurred.

## Authority limits

Direct artifact site definitions, site IDs/spans, joint definition IDs/spans,
site poses and compatibility values are absent. The result keeps source-derived
records separate from actual artifact path claims and JSON pointers. It retains
source-only compatibility authority and false direct-observation/pose flags.

The explicit C267 association decision accepts the unchanged C266 retained
source/program/object binding. Top-level module/scene, program collections and
other omitted metadata remain unobserved; a passing comparison does not certify
those fields or full artifact provenance. Deliberate contradictory data in those
unobserved fields is exercised without expanding the result's claim.

Historical `read_bound_endpoint` admission remains absent. Consequently H01,
H03, H04 and H26 are not fully qualified by this increment. Other broader
source/resource cases remain identified with their pinned predecessor controls.
This review does not certify site/world behavior, full source/glTF/C255 validity,
accepted revisions, edit atomicity, rebuild equivalence, native execution,
model trials, comparative advantage or a product release.
