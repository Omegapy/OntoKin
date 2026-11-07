# C092 implementation candidate 02

Candidate 01 was published and completely read back at
`0c93cd7b9723b6884ceeebe10410e7fa2b952c28`, tree
`b3aa8c0c29b3943fc27c5fe328fc864591900afe`. Before full acceptance, independent
review demonstrated that an original callback could append entries to the
caller-visible numerical LRU and leave 257 entries under a 256-entry cap.
The source result remained canonical, but the actual cache exceeded its bound.
The exact failed probe and candidate source remain preserved.

This correction admits the native positive cache cap and actual cardinality
before any point cache lookup, provenance scan or publication. An oversized
callback-written cache refuses `OKL-E-RESOURCE / execution_context_required`.
No cap, arithmetic rule, input or expected result is changed.

The same checkpoint includes six independently authored ownership regressions
that were written after candidate 01's tree preparation. The complete new
source module now contains 24 tests, including same-key forged payloads, wrong
elapsed and ledger ownership, in-place Fraction mutations, original exception
precedence and actual 256-entry eviction. All 24 passed their identified
pre-capacity-repair run; the repaired candidate requires its own fresh checks.

All other candidate 01 code and authority remain unchanged. The full frozen
acceptance sequence, main integration and torque release remain open until
their actual results are recorded.

Provenance clarification: adapter lookups and insertions prune owner metadata
against the actual LRU. Intervening ordinary-cache evictions can leave bounded
obsolete entry references until that next pruning point; those references
cannot supply a cache hit or bypass the current LRU. The owner metadata never
exceeds the same 256-entry bound. Candidate 01's wording that references are
always limited to currently present entries was stronger than this behavior.
