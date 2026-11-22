# C271 P17: libc flags compatibility decision

P17 adopts the reviewed finite flags design in [ADOPTION.json](ADOPTION.json). Technical work is complete. Documentary publication and a verified partial handoff remain separate gates at this source snapshot.

The new `/0.1.3` profile adds exact `DT_FLAGS=0x18` only for the already bound retained libc/loader pair. It does not widen the existing global mask. Standalone `0x10`, extra bits, duplicates and old profiles remain refused. P16 and all older expected results are preserved. This metadata decision does not establish TLS allocation, relocation or runtime compatibility.

Read [the decision](design/DECISION.md), [control contract](design/CONTROL-CONTRACT.md), [future surface](design/FUTURE-SURFACE.json), [independent review](review/REVIEW.json) and [phase outcome](PHASE-OUTCOME.json). The exact author archive is `design/CANDIDATE001.zip`; readable mirrors are byte-identical. All 41 controls, 22 inert ELF images and 63 fixtures are frozen future test obligations. Seven author integrity groups and 1,655 independent static assertions (1,555 primary and 100 supplemental) passed; no product tests or host qualification ran.

`DESIGN-EVIDENCE.zip` and its manifest preserve complete author/reviewer work and failures. Source bodies, license and inert fixtures remain inside the archive. The startup archive, rejected early attempt receipt and prior evidence remain unchanged. Recovered scripts and binaries are data; do not execute them automatically.

Stop here after documentary publication and saved delivery. The fresh next phase may implement P16 and P17 together with independent adapter/source review and every inherited/frozen control, stopping before H0/H1 or the first concrete design blocker. No implementation begins in P17. C271 remains blocked/open with R03–R05 not_done, P02 in progress, PR274 draft/open, issue273 open and no main lease or integration. The later `P17-DELIVERY.json` records actual saves; source-time pending fields alone do not authorize a retry.
