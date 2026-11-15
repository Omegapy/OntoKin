# C246 native facts helper: final independent static review

**APPROVE for the held-source component only.** There is no remaining blocker in
the reviewed helper. Godot execution, GDScript parsing/compilation and native
acceptance remain unperformed.

| Source observation | SHA-256 |
| --- | --- |
| Initial reviewed helper | `3b09e1dc6a10674b6b4ebdab72c6f90ad67eb35a8b393d6d3e0b2ccffff543cd` |
| Corrected reviewed helper | `1fb4caeb9e36756c03b4cec0072c8a3a1decde0a554798c87a0895cf8ccd29f9` |

Both exact versions are retained beside this report. Approval applies only to
the corrected hash. `INITIAL-REVIEW.md` preserves the original HOLD rather than
relabeling the earlier behavior as passing.

## Correction and result

The initial recursive and outer loops could keep producing records and errors
after `MAX_VALUES` had been exceeded. The correction uses one shared visited-
record budget, retains only the first refusal, and stops nested and outer
metadata/signal/connection/property loops after that refusal. This resolves the
bounded-record defect found by the parent and independent reviewers.

The code now states precisely that this budget does not bound string bytes,
native API allocations, process memory or full output size. Those admission
limits remain later work. This is an explicit limitation of a held-source helper,
not a claim of hard resource enforcement.

Unexpected node scripts are refused before dynamic signal/property enumeration
or property getters. Resource script refusal precedes resource metadata capture.
The supported Variant cases produce detached scalar/container records, while
unsupported metadata, nonfinite floats and custom/invalid callables refuse.
The helper mutates only its own counters/errors and detached output containers.
It contains no native mutation, importer invocation, save or render operation.

## Evidence and limits

The six supplied API documents were matched byte-for-byte to their retained
tool content and Git blob identities at Godot commit
`35e80b3a8822a9df9be390814b62f44c0a9c69e8`. All queried signatures, property
accessors and connection dictionary fields agree with those documents.
`FINAL-RESULT.json` records these bindings, twelve static inspection conditions,
the exact helper hashes and the remaining limitations. `selected-api.xml.json`
contains the relevant API excerpts.

The overall observer/session reviewer separately confirmed caller liveness and
exact native-class checks under the frozen synchronous-extension assumptions.
Those caller files are outside this helper-only review, and neither review
establishes actual native callback/lifetime behavior. This helper continues to
label its result as phase-local identity/metadata facts rather than full C241 raw
capture. Geometry/material arrays, evaluated poses, complete diagnostics,
persistence and later native admission remain pending.

No Godot, GDScript parser, product or aggregate process ran. This review used
source inspection, XML reading and byte/hash checks only.
