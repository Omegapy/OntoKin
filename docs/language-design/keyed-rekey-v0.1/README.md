# C086 bounded pure keyed renaming

The [selected decision](ADOPTION.md), [exact diagnostic/provenance reference](contract-details.json) and [grammar](ontokin-keyed-rekey.ebnf) define `rekey_keyed<T>(input, (old_key, value) -> new_key)` for explicit source .19 / keyed-rekey-0.1, Agent/0.19 and recorded GLB/0.19. It changes keys while preserving immutable payloads exactly. Complete input admission precedes canonical old-key callbacks. Computed keys use the inherited ASCII domain, and the first collision in old-key order fails before later callbacks. Successful output is sorted by new keys.

The operation supports explicit finite name maps and conditional String literals. It adds no String concatenation, overwrite policy, mutable container or physical authority. Changed generated keys change occurrence identities. Original payload entries, old-to-new lineage and all actual inherited contributors remain inspectable.

The [independent input freeze](INPUT-FREEZE.json) binds 177 core source cases, 118 explicit .18 core controls, seven Agent-source states, four explicit .18 delivery controls, ten lifecycle workflow groups and 68 applicable supplied-byte adversaries. These are input counts, not C086 passes. [Actual unchanged-C085 preflight](ADOPTION-DECISION.json) passed all 122 controls. The first preflight's one defective control and separately reviewed correction remain retained.

Historical draft labels in the exact copied source expectations record their preparation state. The separately published decision and freeze establish authority; they do not turn those labels into runtime evidence. [Acceptance requirements](acceptance.json), the [corpus guide](../../../examples/keyed-rekey/README.md) and the [preparation record](../../engineering/keyed-rekey-2026-11-01-c086-inputs/README.md) distinguish the frozen inputs, executed baseline preflight, pending candidate work and retained limitations.

No C086 runtime result or complete release is claimed by this packet. Every GOAL domain, current host ceiling, ordinary default, legacy fixture and retained gate remains in force. Hosted workflows remain manual-only with default-false opt-in.
