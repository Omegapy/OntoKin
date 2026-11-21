# Independent pre-execution review

**Accepted for guarded focused execution. No mandatory findings.** This is
static review; candidate behavior has not been executed by the reviewer.

The inspected module SHA-256 is
`0c2ef54a227e2e05a7eb1f71a4fedd934399aa27d98ec7a3845f93a4dbfbb612`.
Only the approved string-table mapping block differs from the exact original
source. The complete prefix and suffix around that block are byte-identical,
and all other top-level definitions are structurally identical. The existing
inspection test file is byte-identical to its original Git revision.

The implementation follows the accepted finite rule: clip file-backed segment
ranges to the table, sort their endpoints, require one distinct physical offset
per virtual interval, and join checked reads in virtual order. It preserves
coincident mappings and detects conflicting partial overlaps. Missing bytes,
BSS tails and zero-sized intersections have the intended meanings.

The original table/read/string bounds, all later dynamic/name/path policies,
interpreter checks, final identity comparison and descriptor cleanup remain
unchanged. Added callbacks check each segment and interval; the existing
reader and final-return callbacks remain active. The maximum program-header
count keeps mapping work finite, and the partitioned read lengths sum to the
declared table size.

Every one of the 40 compressed published fixtures decoded byte-for-byte to the
independent frozen binary. The published oracle also matches exactly. Both
inventory completeness and duplicate absence were checked. Compression changes
representation only; no fixture or expected value changed.

The new tests correctly materialize private inert files, inject short reads at
named piece offsets, preserve deadline exception identity, and alter only
private copies for drift scenarios. They retain reads, expectations, actual
outcomes, trigger information and initial/final identities in fresh evidence
directories. The drift recipe appends one byte; the byte value is irrelevant to
its frozen identity-change predicate.

The Director must run the test modules through the guarded phase harness so
process operations are forbidden before product import. The independent runner
already implements that guard. Source-backed review does not replace execution:
the exact published head and source identity must be supplied before the
reviewer's candidate run. The selected real Python image must still refuse
`$ORIGIN/../lib`; no H0/H1 or wider host claim follows.

`PREEXECUTION-REVIEW.json` records the exact four inspected deliverables, all
automated byte/structure checks and manual review criteria. The verification
script and its raw stdout/stderr are retained separately.
