# C087 adoption: bounded pure String concatenation

**Decision:** `OK-DEC-STRING-CONCAT/0.1.0`  
**Date:** November 1, 2026 (America/Denver)  
**Scope:** Experimental source `.20` / `string-concat-0.1`, Agent/0.20 and recorded GLB/0.20.

This record adopts the exact reviewed [specification](SPECIFICATION.md), SHA-256 `2c72d8c104d8c6db924b3b42291c05431011df3e575e11d6a85f4b6f78cd4432`, and all 546 files (11,313,625 bytes) in the [input manifest](freeze/INPUTS-MANIFEST.json), SHA-256 `b3a11de3aaaf4a6237e0526123b28da15e10ef5fa3a05353bd13885abb7187d4`. The specification retains its original review-draft label as immutable review evidence; this separate adoption establishes its authority without rewriting reviewed bytes. Runtime implementation is authorized only after this packet is published and every frozen byte and mode has been read back and verified.

The [independent review](freeze/review-transport-agent02-final.json) and [root review](freeze/ROOT-REVIEW.json) accept the exact contract and inputs for publication. [Preflight gates](freeze/PREFLIGHT-GATES.json) report 122 passing observations across 115 distinct controls on unchanged C086 main `5d83b07354296a891c1a6acd70efc77322d2127f`. The [control transfer](freeze/EXACT-CONTROL-TRANSFER.json) binds those observations to the final inputs. Original failed preparations and superseded drafts remain in the complete C087 handoff; no candidate result supplied an expected value.

The new operation is exact immutable String + String, with a 65,536-byte UTF-8 result cap and 4,194,304-byte cumulative request reservation. Declaring units own semantics. All four stages use the original admitted shared ledger, including cancellation and current authority. Other operators, earlier versions, defaults, stable-key rules and release limits retain their existing meanings.

Implementation, source/Agent/hostile/native validation, independent candidate review, integration and resulting-main checks remain separate execution obligations. This adoption does not establish experimental-feature release acceptance or full-product acceptance. All retained C086 failures, external requirements, missing history, storage uncertainties and every domain in [GOAL](../../../GOAL.md) remain in force.
