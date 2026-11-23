# P23 independent H0 blocker decision

**Confirmed: `H0-RTLD-ABSENT-PARENT-001`. H0 remains unaccepted. Technical preparation stops here.**

The exact reviewed data collector ran once, returned 0 in 0.032 seconds and produced empty stderr. Fourteen independent capture, identity, observation and scope checks passed. Its output SHA-256 is `5bea4c400b5a5748956eab867ba6cfac975167a02b4eccdbe00ad0367b7cbc5c`. No public inspector, Node, ldd, loader or product workflow ran.

## Why the plan cannot be completed under the frozen representation

The current `/usr/bin/ldd` was read as stable data: 5,356 bytes, mode 0755, SHA-256 `7bcd61a279946cb376d36fd91f4938ab4f4aba48e793c652a9797319d23f8dd3`. Its literal RTLDLIST contains, in order:

1. `/lib64/ld-linux-x86-64.so.2`
2. `/lib/ld-linux.so.2`
3. `/libx32/ld-linux-x32.so.2`

Both the third candidate and its immediate `/libx32` parent were absent in two stable metadata observations.

At frozen source `527368bd5195c439762b43e2cc836ff9822213f8`, `_check_resolution` admits an absent RTLD candidate only when its declared parent equals its immediate parent **and that parent exists as a directory**. A file row cannot bind the missing file. The absent row cannot satisfy that parent condition. Omitting the candidate violates the required equality with the full ordered literal list. The existing first-absent-ancestor mechanism for origin variants is a different closed representation and cannot be substituted here.

This is a source-backed plan-representation blocker. The public validator was not invoked, so no runtime error, error ordering or product failure is reported.

## Related constraint from the same observation

The required `/lib64/ld-linux-x86-64.so.2` exists as a symlink whose target is `../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`. The frozen `_existing_chain` explicitly refuses `..` in symlink targets and requires a separately reviewed traversal model. That related constraint is retained from the same observation; it is not a new probe or a claim that this would be the first public runtime diagnostic.

## First remaining action

In a fresh bounded phase, make an independently reviewed, versioned design/adoption decision for these required candidate-path shapes: absence below a missing ancestor and bounded parent-traversing aliases. The decision may retain refusal. It must define concrete guards, closed schemas, finite traversal, inode/alias identity, drift checks, unchanged legacy behavior and frozen positive/refusal/fault controls before implementation is selected.

Creating global compatibility directories, editing ldd, changing system symlinks or dropping literal candidates would evade the frozen requirement; none is part of this remedy. No implementation or second technical phase starts in P23.

The successful earlier Python/libc/loader pin check remains valid within its limited scope. Current installation pairs, full author/import/metadata/ELF closure, operational source-review reuse, H1, original-seven/full routine, integration and parent closure remain unmet. Finish only documentary verification, publication and the verified saved handoff.

Exact source anchors, input hashes, observations and all checks are in `BLOCKER-REVIEW.json`.
