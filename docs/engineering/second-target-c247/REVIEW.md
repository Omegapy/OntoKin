# C247 held mesh-array source: independent review

**Approved for held-source publication only.** The independently checked author
commit is `58ac8c83880cb5dccd4f8d4a0d75098209dd593b`, tree
`6ffa45877e5e171764fc10b5c405cee0883ad890`. Its eight files are unchanged in this
publication candidate. The additional files record the review and its evidence.
Actual publication and saved delivery are recorded in [scope #223](https://github.com/Omegapy/OntoKin/issues/223).

This component captures positions, indices and normals from the 18 final live
mapped meshes after generation returns. It uses the unchanged C246 registry,
preserves native format and array types, raw encoding buffers and auxiliary
tangents, and refuses unsupported layouts. It preserves partial results and
explicit omissions instead of filling missing values from source expectations.

## Evidence

| Check | Observed result |
| --- | --- |
| Author CPU model | 34 methods passed |
| Author source/API bindings | 147 checks passed; 23 source records and seven authority documents |
| Independent model | 261 cases / 2,776 assertions passed on exact frozen source |
| Independent source/fixture inspection | 117 checks passed |
| Author documentation | 29 preserved sources / 233 sections passed |
| Author scoped whitespace | Passed |

[Author result](evidence/AUTHOR-RESULT.json),
[independent approval](evidence/APPROVAL.json),
[complete independent review](evidence/INDEPENDENT-REVIEW.md),
[adversarial results](evidence/ADVERSARIAL-RESULT.json), and
[source/fixture checks](evidence/SOURCE-BOUNDARY-RESULT-CORRECTED.json)
bind these outcomes. Full commands, logs, controls and licensed upstream sources
remain in the identified recovery and final handoff.

The initial partial-evidence finding was corrected: the reader now retains
inspected lengths and supported bounded values before cross-slot refusal.
Excessive buffers/arrays have explicit omission records. A reviewer suspicion
about a GDScript return type was not established by the pinned analyzer; the
explicit cast is a clarity improvement. [Original findings and correction](evidence/INITIAL-FINDINGS.json)
remain preserved. An independent source-copy newline error was also detected and
corrected without altering upstream bytes or project source.

## Meaning and limits

The current engine source can encode/decode normals and auxiliary tangents even
with import compression disabled. Keeping raw buffers and actual API arrays
allows later loss measurement; these checks establish no native fidelity.
Two equal reads detect lasting changes but do not establish an atomic snapshot
against concurrent mutation. Native calls may allocate before the reader checks
its bounds. Hard process/resource enforcement remains a later gate.

Godot parsing and every native/version/import/render/save/reopen operation remain
unexecuted. These Python model and source checks do not establish GDScript or
installed-engine behavior. `execution_admission` and `native_acceptance` remain
false; R07 is pending. The source stays on a draft branch based on held C246;
main integration is outside this scope. Materials, evaluated poses, serialization,
complete diagnostics, exact installed lineage, useful images, persistence and
reservation remain later work. All historical failures and limits remain intact.

After the verified successor handoff is saved, stop. The separately bounded
[next material-capture component](NEXT-TASK.md) is not started here.
