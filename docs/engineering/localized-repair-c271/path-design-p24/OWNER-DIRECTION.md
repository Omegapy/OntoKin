# Owner-requested recommendation: finish C271 validation without creating a separate environment project

Date: November 23, 2026. Status: **proposed next-step guidance**, not an adopted specification or an implemented change. This note was added to a successor handoff at the owner's request, following P23 delivery. The frozen P23 outcome, source snapshots, tests, receipts, PR and issue states are unchanged.

## Why this matters

C271 is a bounded test of the missing actual source import digest. The isolated behavioral controls (R01 and R02) are complete. R03 (full required validation and independent review), R04 (reviewed main integration) and R05 (final delivery/closure) remain open. The affected regression cohort previously passed, but the mandatory broad routine did not finish successfully. Fresh ChatGPT chats have disposable hosts; historical runtime installations and paths are not reusable. P23 found **plan-representation constraints**, not a failed H0 inspector, H1 or product test:

1. `/libx32/ld-linux-x32.so.2` is required by the current host's literal `ldd` RTLDLIST, but `/libx32` itself is absent. The frozen plan schema can describe an absent candidate only when its immediate parent exists.
2. `/lib64/ld-linux-x86-64.so.2` is a loader symlink to `../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`. The existing traversal guard rejects a symlink target containing `..`. Ordinary filesystem syntax must not be conflated with proven unsafe traversal, but no unsafe resolution should be accepted without an explicitly reviewed safety model.

These exact observations and non-executed gates remain authoritative in `PHASE-OUTCOME.json` and the published P23 review. Do not claim H0 acceptance or any runtime/product validation from those raw observations.

## Recommended bounded course

**First:** In the **next fresh chat**, perform *one narrow, independent design/adoption review*, using the already-identified missing-ancestor and parent-traversing-alias cases. Give the reviewers explicit choices: (a) a versioned, closed representation that preserves all literal `ldd` candidates even when ancestors are missing, with an authenticated absence chain; (b) a strictly bounded traversal model that safely handles `..` aliases through canonical path identity and finite, cycle-resistant resolution; or (c) retain refusal with an evidence-backed alternative qualification route. Existing security restrictions, exact dependency pins, original tests, historical failures and frozen source contracts must remain intact unless a separately authorized, independently reviewed change is adopted. No blanket acceptance of `..`, guard bypass, fabricated `/libx32`, `ldd` rewriting, missing-candidate omission or host mutation.

**Then, if independently adopted:** Implement only the minimal versioned inspector/plan change required by that decision in a separately declared bounded phase. Add positive and refusal/fault regression controls for both cases, path-escape attempts, cycles, broken links, missing ancestor chains, order equality, and exact pin/readback behavior. Preserve legacy guard outcomes where they remain applicable. An adopted design is not itself implementation or H0 qualification.

**Immediately after the prerequisite is genuinely resolved:** Progress through the already-required verification sequence: complete H0 plan and actual H0 inspector acceptance, H1 as specified by the adopted contract, original required CPU/host methods and full local validation routine, independent review and R03 acceptance, then R04 reviewed integration/resulting-main checks, and R05 confirmed delivery/closure. Follow the project's one-bounded-phase-per-chat rule. Do not skip or reclassify failed or unrun checks.

**Control project overhead:** Avoid repeating previous-host filesystem hunts or redoing exact completed evidence without an identified changed input. Reconstruct only the current phase's indispensable versioned inputs on each fresh host. Keep one concise evidence table of what passed, failed, is blocked, and remains unrun. At the first concrete new blocker, capture it and stop; do not turn a new environment investigation into an indefinite sequence of milestones. Before selecting another host-only phase, explicitly reassess whether it is essential for C271 acceptance and whether a safer, simpler contract-compliant method exists.

## Decision and finish criteria

The next phase is successful if an independent reviewer accepts a closed and safe approach to both observed path cases **or** accepts keeping the refusal with one concrete alternative. The phase stops there; it does **not** implement the decision or run H0/H1 as a second phase. Subsequent phases should prioritize completion of R03-R05 rather than expanding the host-inspection subsystem. The broader OntoKin language, 3D generation and physics roadmap is not being changed by this handoff amendment.

## Source and precedence

- Frozen P23 outcome: `PHASE-OUTCOME.json` in this archive; [published outcome](https://github.com/Omegapy/OntoKin/blob/182d36d957d93161e351f41839bf2a6157fed3df/docs/engineering/localized-repair-c271/h0-plan-p23/OUTCOME.json)
- Confirmed original P23 delivery: https://github.com/Omegapy/OntoKin/blob/3bc46e80f3d59616110b218740a5f5f3dd688a57/docs/engineering/localized-repair-c271/h0-plan-p23/P23-DELIVERY.json
- Canonical governing procedure: current live GitHub `CHATGPT-START-HERE.md`, `PROTOCOL.md`, `HANDOFF.md`, task requirements, adopted technical contracts and safety guards. The live repository and higher-priority instructions supersede this recommendation.

Do not interpret this amendment as license to merge PR #274, close issue #273, rewrite historical receipts, change a frozen oracle, or claim a passed test.
