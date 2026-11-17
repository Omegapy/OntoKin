# C258 supplemental review: filesystem resolution refusal

**Approved current scientific input:** commit
`2bca9f7d2cba8996043bbfeae0c2855def5d7076`, tree
`f14f27adc531a1de1d532b050fdbc5d134166024`. The reader SHA-256 is
`397413d7c403693a349075711bc3dd77fab863d200b06a979cec2f0112114937`.

The same **118 independent scientific controls pass** on these exact bytes.
An additional actual hosted self-referential repository symlink control now
returns the required typed `Fault` with code `IO`. This gives **119 passing
independent controls for the current candidate**. Both executions verified a
clean checkout before and after. No source was edited during review.

## Why this supplement was necessary

The previous independent review approved the finite scientific component at
`1dfe9d022d0774e311a873ee5eb7a8ba33aab3be`, after its 118 controls passed.
A separate static reviewer subsequently found that Python 3.12 `Path.resolve`
raises `RuntimeError` for a symlink loop. That exception escaped the public
typed-refusal boundary. This concrete later finding blocked integration even
though the earlier scientific cohort had passed.

The original finding is copied unchanged as `original-symlink-failure.json`.
The original 82-entry independent evidence manifest, prior approval and
namespace-defect failures remain unchanged in the sibling
`c258-independent-review` directory. They describe the inputs actually tested
at those earlier checkpoints. They do not approve later bytes by implication.

## Corrective delta

The production delta adds a small `resolve_path` wrapper that converts
`RuntimeError` to `Fault("IO", ...)` only around `Path.resolve`. Three existing
resolution callsites use it. This does not broadly convert arbitrary runtime
bugs into I/O refusals. One authored regression method was added.

`DELTA-REVIEW.json` binds the exact old/new readers and records the structural
comparison. Apart from the new wrapper, only `dependency` and
`read_bound_endpoint` change. All 25 other top-level functions/classes have
identical syntax trees, including the source, numeric, identity, graph,
metadata and comparison logic. The same 118-control suite was still rerun to
bind its passing result to the actual new module bytes.

`symlink_control.py` creates an actual self-referential symlink in the hosted
audit area, calls the public bound API and records the observed exception.
The link is removed after the probe; its exact recipe and script are retained
instead of placing an active symlink loop in a handoff archive. The successful
result is in `SYMLINK-CONTROL.json` with a complete log beside it.

## Authority and evidence

The finite scientific boundary and all previous nonclaims remain unchanged.
There is still no direct artifact follow-definition/source-span authority,
complete source/glTF qualification, joint-wide validation, execution, accepted
revision or rebuild authority. This supplement does not prove publication,
resulting-main checks or saved delivery.

`FINAL-REVIEW.json` is the current exact-code approval. `attempt-03` contains
the full 118-control results, complete execution log, reviewed reader bytes,
scripts and selected changed fixtures. `REVIEW-RETENTION.json` binds every new
evidence path and identifies exact duplicates in the previous frozen review.
The old reader bytes must remain explicitly retained: their former suggested
repository equivalent no longer matches the current `follows.py` hash.
