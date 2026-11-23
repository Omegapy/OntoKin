# P24 evidence and limits

The adopted decision is a versioned design. Production implementation and runtime qualification remain pending.

| Gate | Actual result | Evidence |
| --- | --- | --- |
| Early recovery before substantial work | Saved and exact-byte readback confirmed | [Receipt](EARLY-RECOVERY-RECEIPT.json) |
| Independent exact design review | Accepted attempt004; three mandatory findings resolved; 12 manual groups and 101 documentary integrity checks | [Review](reviews/path/REVIEW-FINAL.json) |
| Director adoption | Exact accepted payloads and controls adopted for later implementation only | [Adoption](ADOPTION.json) |
| Frozen controls | 52 requirements: 5 positive, 34 refusal, 13 fault; 51 future primitive/mocked checks and one external-review-only condition; zero executed | [Matrix](reviews/path/CONTROL-MATRIX.json), [crosswalk](reviews/path/CONTROL-CROSSWALK.json) |
| Source and history preservation | 13 assertions passed; all production/test/tool/pin files unchanged, prior checks retained | [Preservation](PRESERVATION-FINAL.json) |
| First documentary attempt | Workflow and whitespace passed; two broken relative links in the recovered earliest draft | [Failed attempt](checks/candidate001/RESULT.json) |
| Corrected documentary attempt | Workflow, full documentation and staged whitespace passed | [Corrected attempt](checks/candidate002/RESULT.json) |
| Publication and final delivery | Pending at core source; exact observations are recorded separately | [Outcome](OUTCOME.json) |

The link repair adds labelled copies of already-preserved attempt001 companions beside the recovered earliest draft. It changes no accepted candidate or frozen control. [Companion provenance](history/pre-attempt001/COMPANION-PROVENANCE.json) states the historical limit.

No H0/H1, Node, ldd, direct loader, product test, full routine, installation or main integration occurred. R03-R05 remain not_done and P02 remains in_progress. After final delivery, stop this chat. The next technical action is a fresh bounded implementation phase under the exact adoption.
