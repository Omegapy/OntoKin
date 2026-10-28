# Independent parsing of the retained clock axis

This candidate starts from checkpoint023 commit
`571ea01001643da91acf001ff64fec32b83dea30`. It changes only numerical-cache
bookkeeping during independent validation of the complete retained clock axis.
It is unexecuted at the initial review cut. The original source fixtures,
horizons, sampling rates, tolerances, 100,000-operation allowance,
32,768-bit operand maximum and 256-entry numerical cache remain unchanged.

## Exact computation and retained output

`verify_retained_clocks` already visits every actual authored record in order,
parses its exact rational identity and appends that result to the required
`authored` output list. A valid axis is strictly increasing. Its native string
pairs therefore occur once within this traversal. The earlier final-clock
admission is still separate, and repeated interval-width records continue to
use the ordinary bounded numerical cache.

The new internal `cache_parse=False` selection performs the original decimal
chunk parsing and exact greatest-common-divisor reduction. It omits only the
lookup, insertion, promotion and eviction of these one-shot results. Every
actual integer and reduction operation keeps its existing charge and callback.
The resulting rational is retained only in the existing required authored-axis
output; no extra result cache or history is introduced. No mathematical or
floating-point approximation is added.

Malformed, ambiguous, negative and unreduced strings still take the same
validation path. Native short-string results retain the final live operand
guard after reduction, including cap changes in its last callback. Longer
strings retain their existing chunked parsing path. The exact rounding-cell
checks, common-accessor equality, binary32 labels, semantic-boundary coverage,
ordered-axis comparisons and time tolerance checks remain unchanged.

Removing numerical-cache operations can change which unrelated entries remain
in the LRU. This is a performance effect to measure across complete requests,
not a reason to alter its limit or count estimated savings as execution.
Callback exceptions from every remaining operation propagate unchanged; no
partial parse is published to the numerical cache.

## Required execution

The dedicated module `tests/test_reach_retained_clock_parsing.py` checks exact
native and long decimal values, original malformed-input and operand failures,
changed supplied strings, cancellation at every surviving checkpoint,
late cap narrowing and narrow-then-widen ordering. It compares the complete
retained-axis result under empty and full cache contention and keeps repeated
width caching unchanged. An otherwise consistent forged accessor must still
fail the independent exact rounding-cell check.

Original P09, P11, P16 and L03 quarter-second source prefixes compare complete
GLB bytes and entire reports against a control that restores cached parsing.
Total request work, including construction and cache effects, must decrease.
Passing prefixes do not establish the complete original recording gate. An
accepted integration still requires related correctness and all original28,
with every remaining mandatory release role separately identified.

## Executed dedicated evidence

Independent read-only review found no blocking issue on source
`4f63671185707a76b680298afec914ad114fac1f`, tree
`79c307d7bb22565035f1cb4c787f966f790c4795`. That exact clean cut passed
**12/12 dedicated methods**, with zero failures, errors or skips, on
CPython 3.12.14. All tracked files were present and before/after input hashes
were stable. The complete log, named method inventory, driver, source receipts,
launch timestamps, stdout and stderr are preserved in
`execution/retained-clock/retained-focused-001` and sibling launch files in
the accompanying checkpoint archive. No failed attempt or source/test repair
preceded this result.

The unchanged development driver has SHA-256
`052518bda650883f83f24dd34bc1bda9144c27ee3ad6900f72242ca74f10ddf6`.
The actual command selected only `test_reach_retained_clock_parsing` and used
the clean candidate worktree. The original quarter-second prefixes retain
identical complete GLB bytes and entire export reports:

| Original source prefix | Cached axis parsing | One-shot parsing | Operations saved |
| --- | ---: | ---: | ---: |
| P09 | 39,752 | 39,681 | 71 |
| P11 | 66,905 | 66,891 | 14 |
| P16 | 48,907 | 48,872 | 35 |
| L03 | 35,731 | 35,705 | 26 |

These totals include construction, original end-clock admission, setup and
all cache effects. They do not establish complete-recording savings or a
full regression pass. The related integrated cohort and original28 must run
on the subsequently published integration; its source identity and results
remain separate from this dedicated run.
