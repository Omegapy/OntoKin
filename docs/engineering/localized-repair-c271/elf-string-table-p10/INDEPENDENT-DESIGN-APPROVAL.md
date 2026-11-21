# C271 P10 independent mapping design approval

Reviewer and fixture author: `/root/elf_review`. Source basis: retained commit
`ffd234b17723e8370cc0afa6cf19c1a161719892`, with the unchanged inspector SHA-256
`b2f4c869fd03919047db797bd3a80616cbe16f6b17689fe61d40754b27f97a39`.
The Director confirmed the corrected early recovery gate at
`2026-11-21T20:11:29.084562+00:00` before this construction began.

## Accepted finite rule

Map only the half-open dynamic string-table interval
`[DT_STRTAB, DT_STRTAB + DT_STRSZ)`. A `PT_LOAD` contributes only its file-backed
interval, ending at `p_vaddr + p_filesz`; its additional memory is not file data.
Clip participating intervals to the table, partition at their endpoints, and
require exactly one **distinct file offset** for each nonempty partition.

Identical full or partial mappings are allowed. This preserves the old
`len(set(mappings)) == 1` meaning: multiple declarations can identify the same
bytes. Distinct offsets are ambiguous even if the two file ranges happen to
contain equal values. A partial conflicting overlap must also refuse; a larger
mapping cannot hide it.

At a partition's first virtual address `a`, each covering segment maps to
`p_offset + a - p_vaddr`. Every mapping advances by one file byte per virtual
byte, so equality at `a` proves equality throughout that partition. Concatenating
accepted partitions in virtual order therefore constructs exactly the declared
table. File offsets need not be contiguous or increasing.

Zero-sized intersections contribute no bytes. A segment ending exactly where
another begins has no overlap. Missing prefix, suffix, internal bytes, and
memory-only tails refuse with `CHI-UNSUPPORTED` and the retained reason
`Ambiguous/unmapped ELF string table`.

## Bounds and unchanged behavior

Retain the existing 256-program-header limit, 4 MiB string-table limit,
16 MiB per-read ceiling, checked file ranges, exact short-read check, final file
identity comparisons, callback propagation, 4096-character string limit and all
dynamic/interpreter/name/search-path guards. Read every selected piece through
the existing bounded reader. Invoke the supplied check callback during the new
mapping work and before every read; retain its final invocation.

At most 256 load declarations yield at most 514 clipped endpoints and 513
nonempty partitions. Checking each partition against those finite declarations
is bounded. Total selected table bytes stay at `DT_STRSZ`; an implementation
must not read overlapping bytes repeatedly into the final logical table.

Only the string-table mapping block is approved for production modification.
`PT_DYNAMIC` mapping, loader-token policy, host plans, process code, strict
schemas, helpers, original seven methods, source budgets and dependencies stay
unchanged. This approval is a design decision, not acceptance of unseen code.

## Independent corpus and proof

`frozen002/ORACLE.json` contains 40 cases: 16 positive cases, 17 refusals, and
7 fault scenarios. Tiny ELF64 headers and literal metadata declarations define
each case. The builder never imports or invokes the production module.
`CONSTRUCTION-PROOF.json` retains every encoded header, dynamic entry, logical
string-table byte and mapping declaration. Its independent coverage proof
enumerates each virtual byte and its set of physical offsets; it does not use
the proposed endpoint algorithm.

The maximum-header case has 254 one-byte string pieces plus the metadata load
and dynamic table. Boundary strings exercise `DT_NEEDED`, `DT_RPATH`,
`DT_RUNPATH` and `DT_SONAME`. Repeated mappings, conflicting inner mappings,
file-offset reversals, missing bytes, BSS, zero-sized segments, read faults,
deadlines and identity changes have explicit expected outcomes. Existing
inspection methods remain the broader unchanged-guard regression gate.

The fault scenarios are portable instructions for a later runner. Short reads
remove one returned byte at a named piece. Deadline callbacks raise the exact
predeclared `HostInspectionError` instance initially or after a named piece.
Identity faults append a byte to a private copy after a named piece; the frozen
input itself must never be changed. All outcomes and input hashes are frozen
before any candidate edit or parser execution.

## Selected Python boundary

`SELECTED-PYTHON-OBSERVATION.json` binds the separately retained 30,894,944-byte
image, SHA-256
`fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`.
Direct byte inspection confirms `DT_RPATH` is `$ORIGIN/../lib`. After successful
mapping, the unchanged token guard must therefore still refuse this image with
`CHI-UNSUPPORTED: Unreviewed loader token expansion`.

This is a static expected later refusal, not observed parser behavior yet. It
does not establish H0 readiness or authorize loader-token support. The image
has no execute bits. P09 recorded mode `0o600`; the recovered file's observed
mode is `0o644`. Exact bytes match. Neither this worker nor its builder changes
that restored file.

## Failure preservation and stopping point

`build001` produced the synthetic corpus, then stopped at the historical-mode
assertion. Its script, stdout, stderr and partial output remain unchanged.
`build002` records the historical/restored-mode distinction and succeeds. The
40 fixture bytes and oracle expectations are identical between both attempts.
There was no expectation adjustment to production behavior and no product
execution in either construction attempt.

After the immutable freeze, the Director may implement this bounded mapping
correction. Baseline/candidate execution requires a separate Director grant.
Independent exact-source review remains mandatory. No H0/H1, Node, `ldd`,
original-seven/full routine, native operations, main integration or parent
closure is covered by this approval.
