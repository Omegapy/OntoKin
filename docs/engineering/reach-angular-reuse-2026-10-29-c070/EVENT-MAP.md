# C070 angular events, authority and cache effects

This is a source map of baseline `20977e92945d767bc8047b36e0e697f53d2a886e`, not an executed candidate. [The binding](source-binding.json) and [derivation](derive_evidence.py) identify the actual files and definitions. Relevant code is in [reach_export.py](../../../ontokin/reach_export.py), [reach_numeric.py](../../../ontokin/reach_numeric.py), [gltf.py](../../../ontokin/gltf.py) and [reach_conformance.py](../../../ontokin/reach_conformance.py).

## Original event order

Let `q` be incoming `eq`, `r` be `nsr`, `w` be `width`, and `omega` be the angular speed read at its original position. Each arithmetic row is one actual `_exact` call. Nested expressions evaluate their arguments before the enclosing call.

| Event | Original operation or check | Obligation |
| --- | --- | --- |
| P | `ep = ep + nsp` | Preserve this positional addition before all angular work. |
| A1 | `e = q + r` | Adjust quaternion error using current exact inputs. |
| R1 | `e <= 1/2` | Preserve the current model's endpoint-range diagnostic. |
| Read | `bound.angular_speed` | This read first occurs after R1. |
| A2 | `p = omega * w` | Original multiplication guards. |
| A3 | `h = p / 2` | Complete the left chord branch first. |
| A4 | `u = 4 * e` | Then complete the right branch. |
| A5 | `c = h + u` | Form chord. |
| R2 | `c <= 1/2` | Preserve short-arc range diagnostic before arc calculation. |
| A6 | `s = c * c` | First arc intermediate. |
| A7 | `t = s / 4` | Original prospective division guard. |
| A8 | `d = 1 - t` | Form the divisor before the final division. |
| A9 | `a = c / d` | Preserve zero-divisor and width behavior. |
| R3 | `a <= ANGULAR_STEP` | Preserve the stored-arc diagnostic. |

The angular region has nine explicit arithmetic charges: two additions, three multiplications, three divisions and one subtraction. Its numerical outputs are `e` and `a`. Under passive native successful execution, the four exact inputs and identified formula determine those outputs. This numerical dependency statement does not identify the complete execution behavior.

Every `_exact` performs, in order: charge; operand guards; numerator/denominator width reads; prospective-width calculation, including the divisor test where applicable; prospective-width guard; selected Fraction operation; result guard. R1/R2/R3 are existing raw comparisons, not additional `_compare` charges. This record does not assign a new unit to every Python operation or silently price added checks as free.

## Why direct key construction is not sufficient

Constructing `(bound.angular_speed, width, eq, nsr)` immediately after P moves the angular-speed read before A1/R1. A conditional helper-entry witness exposes the problem. Assume passive work and ordinary positional inputs that complete P, incoming `q=3/4`, `r=0`, and a foreign `bound` whose angular-speed property raises an existing exception E. Original execution reaches R1's numeric-bound diagnostic before reading that property. The proposed eager key reads it first and raises E. This is an unexecuted source witness. It is not an observed stock request failure or a claim that ordinary source construction creates that foreign object.

Moving the lookup after A1/R1 avoids this particular hoist, but leaves eight arithmetic calls, with adjusted `e` rather than incoming `q,r` as a numerical dependency. That different placement still needs current guard, callback, authority and cost proofs. At a seam after A1's charge, the original guards and calculation are pending. A failed optional attempt must resume that continuation correctly; calling `_exact` afresh repeats its charge. An already consumed unit is not free payment for added inspection.

A custom work object, callback or observer can raise, mutate state or lower a domain at an original A1–A9 checkpoint. An unrestricted angular hit replaces those events with lookup/promotion. For example, a custom charge implementation that raises its marker at the first angular `recording_exact_mul` would not receive that event on a whole-region hit. This is another conditional source observation, not an executed hostile test. The native source driver and the Agent/direct/custom routes need their own accurately bounded treatment.

Replaying every original charged arithmetic/guard/range seam can preserve that broader class only if the original operands, operations, continuations and dispatch are also preserved. It saves none of these nine metered units before added cache work. This rejects complete replay as the proposed operation-budget saving mechanism. It does not deny the adopted permission for actual avoided arithmetic on a separately established passive native route. Such a route remains unproved here.

## What the existing cache already protects

`ReachExecutionWork.lookup` charges lookup and, on a hit, promotion. It synchronizes the operand cap before lookup and after promotion, and rechecks the key's presence. A changed cap clears the old domain's cache through a charged reset. Therefore a simple cap reduction does not automatically produce a stale warm hit through this implementation.

`remember` charges insertion and any required promotion or eviction before modifying values or order. It rechecks operand domain and cache generation around those callbacks. Incomplete calculations do not reach publication through `_reuse`, and a detected domain or reentrant-cache change refuses the pending publication. These are real protections; they do not authenticate all new formula, input, dispatch, observer or alias assumptions.

Native `charge` captures the observer, calls the external check, checks its operation/time limits, increments operations/category counters, then calls the captured observer. Callback exceptions retain their identity. The source driver uses a native construction-budget callback, which increments its shared counter before checking that limit. Native callback does not mean no callback. Arbitrary callback-sequence equivalence and permitted native checkpoint changes are separate obligations.

The added angular key would occupy the same bounded cache as other writer and reader entries. Export validation passes the same work object into the independent reader. Insertion, promotion and eviction can change later misses and later computational cost, even when the two angular numbers are identical. A signed complete-request difference is required. The independent reader must still establish its own claims from supplied bytes and source; writer numerical equality does not authorize it to accept a writer receipt.

## Path obligations and decision

| Path | Required treatment |
| --- | --- |
| Existing complete-group hit | The region already does not execute; do not count another saving or add an earlier angular lookup. |
| Cold angular miss | Preserve original order/guards/errors; charge actual lookup, insertion and any admission/eviction work. |
| Resident angular hit | Establish current exact identity, formula, domain and admitted authority; price fresh checks and both cache events. |
| Eviction or changed domain | Retain lookup/reset/recalculation/publication charges. Do not assume reuse persists. |
| Partial, refused or failed calculation | Publish no incomplete success. Retain all admitted attempts and the original first failure. |
| Foreign or mutated dispatch | Preserve original route/events or prove an explicit safe alternative. A saved flag is not its own authentication. |
| Downstream writer/reader | Account for cache occupancy and order, displaced entries, later misses and repeated/refused work. |

[Funding](funding.json) keeps these unknown costs explicit. Existing group-cache acceptance, C030 historical acceptance and C068 unadopted unit proposals do not supply a complete admission map for this new unit. No authority-safe positive complete-request schedule is established, so instrumentation and implementation are not selected.
