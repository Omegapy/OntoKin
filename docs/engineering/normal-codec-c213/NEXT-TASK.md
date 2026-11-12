# One next task: exact source-normal payload and explicit loss contract

Reconcile current main, ownership, [issue #154](https://github.com/Omegapy/OntoKin/issues/154), held [PR #155](https://github.com/Omegapy/OntoKin/pull/155), and the saved C213 handoff. Read AGENTS, GOAL, STATUS, [C212's decision](../normal-fidelity-c212/DECISION.md), and [C213 results](RESULTS.md). C213's finite characterization is complete; do not repeat it as another milestone.

Build one isolated CPU-only prototype of a separately versioned source-normal payload and loss-report contract for the accepted C210 GLB. The exact source program/GLB remains authoritative. The payload must bind each direction to an unambiguous source mesh/primitive/corner and winding, preserve original float32 normal values, and retain the artifact/source identities needed to reject stale or mismatched data. Existing accepted source, GLB bytes and C211 evidence remain unchanged.

Define two separate claims: exact authoritative source directions, and independently observed destination shading directions with component/angular differences and missing/invalid observations. Do not label a retained metadata copy as proof of actual shading fidelity. A CPU-only synthetic destination observation may exercise the reporting contract, but must be marked synthetic and cannot become receiving evidence.

Predeclare independent controls for exact payload round trip, duplicate/missing/ambiguous corners, changed winding, direction signs, nonfinite/zero vectors, sharp-boundary distinctions and stale source/artifact identity. Bind source, implementation, inputs and outputs. Require a versioned profile decision explaining how this proposed preservation/loss boundary differs from C211's original strict promise. Do not silently revise that promise or adopt a tolerance from a measured maximum.

Complete when this small payload/validator/report prototype and its proposed contract pass independent CPU checks, or when a precise blocker is established. This task does not authorize another Blender process, changing the held receiver, native shading acceptance, a second destination or the authoring comparison. A later native experiment still requires its own reviewed implementation/contract, bounded execution plan, native save/reopen and useful visual evidence.

Save recovery before substantial work, preserve all original failures and hashes, and deliver one verified offline-restorable handoff with confirmed save. Then stop.
