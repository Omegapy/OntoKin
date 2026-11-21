# C271 P11: loader-path decision and inert controls

P11 accepts a finite design and 97 independently reviewed inert controls. Implementation and host qualification remain later work. The unchanged selected-Python RPATH refusal still blocks H0; C271, R03–R05 and integration remain open.

## Authoritative accepted artifacts

- [Adoption and exact identities](ADOPTION.json)
- [Accepted decision](design/candidate004/DECISION.md)
- [Control contract](design/candidate004/CONTROL-CONTRACT.md)
- [Frozen candidate manifest](design/candidate004/CANDIDATE-MANIFEST.json)
- [Expected outcomes](design/candidate004/EXPECTATIONS.json)
- [Independent review](review/REPORT.md)
- [Future implementation surface](design/candidate004/FUTURE-SURFACE.json)
- [Lossless raw-evidence transport](GIT-TRANSPORT.md)
- [Private inert-file materialization](design/candidate004/MATERIALIZATION.md)
- [Current phase outcome](PHASE-OUTCOME.json)

Candidate004 is the sole adopted candidate. Its rule covers only the exact selected direct author Python and `$ORIGIN/../lib`. It requires a verified execution origin and complete path/variant/dependency proof that the added directory cannot supply a declared dependency. Actual host eligibility is unestablished.

The variant document uses the existing 16 MiB bounded reader, callbacks, identity checks and canonical JSON validation. The separately proposed 4 MiB cap and reader were withdrawn after review of the user's question. No executable code was changed to make this decision.

The seven legacy, eight new positive, 76 refusal, three recheck and three callback controls are proposed future outcomes, not passing product tests. All 93 original expected records remain unchanged. The 1,149 author and 1,675 independent checks verify static artifacts and evidence only. The existing 175 inspection/mapping methods were not run in P11.

## History and stopping point

The full author history, candidate001 failure, candidate002 review findings, withdrawn 99-case candidate003 and reviewer helper correction remain retained. Source-time records can say delivery is pending; only the separately saved/read-back matching P11 delivery receipt supersedes those fields.

Finish the declared P11 delivery and stop. In a fresh chat, reconcile the exact handoff, matching receipt and live GitHub before selecting the bounded implementation described by the adoption. Preserve H0/H1, full routine and parent/integration gates. Do not substitute another runtime or rewrite the frozen oracle.
