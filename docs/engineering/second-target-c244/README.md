# C244: reviewed capture-hook decision

C244 selects a narrow way to retain source identity when Godot replaces imported
mesh nodes. The [adoption record](ADOPTION.md) changes two capture-contract
boundaries together: one observer-only callback is permitted, and the original
live node map is followed through observed replacement identities to the final
live scene.

The original [C244/0.2.0 proposal](DECISION.md) and its [44 inert controls](test_decision.py)
remain byte-for-byte unchanged. Their historical draft and self-audit statements
describe the earlier authoring stage. The adoption record, [independent review](REVIEW.md)
and [results](RESULTS.md) give the current disposition.

This is a design decision. No observer, emitter, launcher or native proof is
implemented by this increment. R07, installed-build binding, rendering, complete
diagnostic coverage, resource enforcement and native admission remain pending.
After verified integration and saved handoff delivery, the [next bounded task](NEXT-TASK.md)
is held-source implementation of the narrow observation hook and external session
registry, without a Godot start.
