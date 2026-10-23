# Bounded source field routes during reach construction

This isolated candidate starts from `d80c1c21` and is unexecuted. A neutral
ordinary P23 compilation matches all original counters and source identities
at 22,465 operations. Repeated `assignments` validation contributes 1,133
operations across 333 calls. No source fixture or acceptance limit changes.

## Retained information

The compiler can retain a validated route from native assignment names to
their original syntax nodes. The optional table holds at most 64 declarations,
each with at most eight fields. It retains source syntax and ownership receipts
only. It contains no expression values, object instances, computed geometry,
numeric results or poses; the existing 256-entry numeric LRU is unchanged.

The route was created by the complete original field validator, including path
normalization, allowed-field checks, duplicate rejection and missing-field
checks. Native node/data/list/path/step owners, step kinds and names, declaration
kind and the complete required-field set are checked before and after a reused
route's checkpoint. Strong references keep every retained owner alive. A
changed field route cannot match merely because a Python object id was reused.
Native syntax nodes permit direct attributes to shadow their data dictionary.
A direct `assignments` or `path` shadow therefore declines the optional route;
the ordinary validator consumes that actual attribute. Independent review
found this boundary after the first 14-method and 98-method passing runs at
`435239a5`; those runs do not certify the corrected, separately identified cut.

Every use returns a fresh mapping containing the actual original source nodes.
Callers still evaluate every expression in its own occurrence and lexical
context, with all original access, dependency, type, frame, provenance and
logical value accounting. A changed expression is read live by those callers.
The route never stores or supplies an expression result.

## Work and cancellation

A matching route avoids repeated path normalization and duplicate/required
set validation. Its bounded receipt and fresh map copy retain the first
ordinary assignment checkpoint at the same source span. No counter is reset,
decremented or given a larger limit. Unsupported shapes and a full source-plan
table retain the original field loop. Other source profiles do not use the
optional route.

The live assignment iterator and its first item are captured before that
checkpoint. If the callback changes a route, the original validator resumes
using that exact iterator and already-charged first row. It does not insert a
second callback before validating the first changed field. This preserves a
first-field failure before a later callback could restore it, and preserves
Python's original iteration behavior if a callback replaces the declaration's
assignment list. Subsequent ordinary rows still receive their own callbacks.
Original callback exceptions propagate by exact identity.

## Required verification

Dedicated tests compare complete P23 models, dependencies, geometry and logical
value counts; complete original P01 artifact bytes; source-route mutation and
callback ordering; errors for missing, duplicate and unknown fields; fresh map
ownership; work-limit source spans; bounded source metadata and unchanged
legacy paths. Focused construction cohorts and the complete original 28
recordings must follow before any integrated outcome is claimed.

## Corrected worker execution

Source `6823a00c7612af298fbe6443783d1357549325b1`, exact tree
`e8ae4303f6912d60ee9e7a71306eec71b031e936`, passes **18/18** dedicated
methods and **98/98** related construction, source, linker and conformance
methods, with stable inputs and no failures, errors or skips. Independent
read-only review found the direct-attribute shadow hole in the first cut;
the corrected cut retains four explicit warm/callback shadow cases. The
initial cut and all its executions remain separately identified. Root
integrates these three files before separate integrated correctness and
complete-original-recording execution. No complete P23 pass is claimed.
