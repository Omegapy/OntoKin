# P17 independent technical review

**Verdict: ACCEPTED for bounded design and inert-control adoption only. Mandatory findings: zero.**

Archive: 166,919 bytes; SHA-256 `d59d4d71a9f73065a000ae3de8233beb82ad5a33a3b526de93debb845f0d86c4`.

Reviewed candidate manifest SHA-256 `5561dcd3cf718362f0716bb0c3ebf7fcf273befa1f6348f9996331d151b7c89b`; expectations SHA-256 `9ec492d20fe2184414d818fca3ff37bcfdf1a20416dcb042d0bc2667456c9bd8`.

The proposed rule adds exactly `DT_FLAGS=24` for the newly selected, bound libc route. Lone `16`, other bits and duplicates remain refused. Distinct version routing preserves P16's `N16_flags_0x18_preserved`, older masks and diagnostics. The exact libc/loader pins, dependency-role proof, early ordering, fresh rechecks and unchanged flags-one rule remain mandatory.

The source evidence supports metadata recognition while expressly withholding TLS allocation, relocation and executable-safety conclusions. Synthetic positives and mocked binding/dispatch contexts cannot establish operational admission. Named callback controls require actual reachability, identical exception propagation and exactly one descriptor close during later implementation testing.

`AUDIT-ATTEMPT002.json` passes 1,555 independent static assertions: all 22 complete ELF byte reconstructions; all 41 complete literal expectations; 63 fixtures; 169 P16 payloads; 26 protected files; eight historical inputs; six exact source members; 80 active patches; and the 20,048-member token scan. `SUPPLEMENTAL-CHECKS.json` passes 100 source-copy and final-readback assertions. The candidate remains unchanged.

Attempt001 and its source are retained. Its failure was a reviewer reconstruction error: two string offsets omitted the preceding terminator. Corrected offsets reproduce the frozen bytes; no candidate revision occurred.

No product imports, parser/policy execution, tests, recovered execution or host observation occurred. Future adapters and combined P16/P17 implementation still require independent review. H0/H1, full routine, integration and parent closure remain unmet.

No active operations or unknown writes remain.
