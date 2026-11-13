# C231: ledger file identity and resource lifecycle

The run ledger must stop if its invocation marker or journal is replaced. C230
showed that comparing bytes and numeric device/inode values could miss a
same-content replacement. C231 retains the original file objects while a
capability is live, preserves the existing checks, and explicitly releases the
handles at terminal boundaries.

- [Results and limitations](RESULTS.md)
- [Versioned component contract](CONTRACT.md)
- [Independent review](REVIEW.md)
- [Scope and exact checked source](evidence/SCOPE.json)
- [307-method affected result](evidence/author/affected-run-03/RESULT.json)
- [Next bounded task: one fresh complete aggregate](NEXT-TASK.md)

The original ledger test file and historical bindings remain unchanged. This
checked repair is an experimental development increment; the complete R02
aggregate, native admission, destination acceptance and full release remain
separate gates. Publication and resulting-main checks are recorded after the
reviewed candidate is integrated.

Complete tracked-source inventories and all earlier attempts are retained in the
saved handoff. [Evidence locations](evidence/EVIDENCE-LOCATIONS.json) map the two
large external inventory files named by the original independent review.

[PR #195](https://github.com/Omegapy/OntoKin/pull/195) is merged. Fresh actual-main
checks pass all 307 methods; [the integration receipt](evidence/INTEGRATION.json)
records exact published identities, cleanup and remaining delivery steps.
