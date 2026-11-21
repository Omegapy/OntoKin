# Scoped learning decision

Retain these findings with P10 rather than changing general project rules.

1. ELF table coverage must be checked across every file-backed interval, not
   inferred from one containing load segment. A partial conflicting overlap
   matters even when a containing segment exists. Independent byte-level fixture
   construction caught both the rejected positive and hidden-conflict cases.
2. Removing an early static blocker does not qualify a runtime. The retained
   Python image exposes a later existing loader-token refusal. Preserve that
   refusal and stop at the declared boundary.
3. Review recovery completeness against all unique worker outputs. The first
   early package omitted unique intake-audit files; the corrected package and
   supplemental phase bytes were independently accepted before implementation.
4. Workflow task status and next-action status use different vocabularies.
   Preserve the invalid `in_progress` next-action observation and use the
   existing schema's `blocked` value for the unresolved prerequisite.

Evidence: the independent oracle construction, candidate report, early package
review and RECORD-CORRECTION.json. No broader memory or skill update is needed.
