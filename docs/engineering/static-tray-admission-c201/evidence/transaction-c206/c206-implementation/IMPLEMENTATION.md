# C206 transaction component implementation

The local candidate is `afa0a9d40ab0ffbf88e6540bbb685d889a67d391`, tree
`2ab3ea43db443f3a33c1aed0cb3a8e36a28cf79d`, on
`work/c206-transaction-ad77b7`. Its worktree is clean and its base is the actual
C205 main `f90e012fa9b68a1111b97586c6462851e6166dea`. The worker made no remote
writes. Root owns integration and independently verifies publication.

## Implemented boundary

The three new files are the separate C201 transaction module, a dedicated CPU
control module and TRANSACTION-C206.md. Existing C205 validator, C204 ledger,
C199/C200 code and frozen protocol are unchanged.

The component validates exact references, lowers actual frozen or retained
editable source, verifies complete output and receipt closure, reuses unchanged
independent GLB/receiving measurements, seals candidate evidence, and conditionally
promotes an exact empty pointer. It explicitly preserves UNKNOWN if the pointer
may have changed across an interruption or lost reply. There is no child-launch
operation, Node/probe, ledger progression or complete coordinator.

## Production blocker

Inspection found that C205's declared command cwd is the repository root, while
the qualified supervisor and worker require the stage output directory. The
component rejects production input purpose with C201-NATIVE-CWD. It accepts only
validated fixture-only bindings, with the same restriction in its ordinary
constructor/session API. No original component was changed to hide this conflict.
The next bounded decision is a reviewed C201 command-cwd alignment; production
support and native readiness remain pending.

## Checks and original findings

47 actual CPU methods passed in 18.924 seconds, with zero skips, failures or
errors. They use real temporary files, actual source lowering, real independent
synthetic-GLB measurements and receiving comparison, actual sealing and pointer
replacement. Native containers, images, process observations and approval context
are explicitly synthetic fixtures; subprocess/fork/shell APIs are blocked.

Independent draft review identified omitted qualified startup/supervisor receipt
files, altered jobs accepted by the first draft, and a post-replacement
interruption risk. These are corrected in the candidate; original probes and
source snapshots belong to the independent review evidence. Local draft logs
remain unchanged. One intermediate run had two test-adapter errors from reading a
moved receiving receipt at its previous path; the adapter now follows its actual
sealed location. The following 46-method run and final 47-method run passed.

Tests ran immediately before the commit on the same input bytes. IMPLEMENTATION.json
binds the exact committed source/test/document hashes, log hash, command and
interpreter/platform. Root performs applicable existing checks and final review
on the committed candidate. No historical native or full regression was rerun.

Process receipt consistency is checked, but truthful process provenance remains
the future trusted caller's responsibility. Cooperative Clock checks are not an
external watchdog. Full native admission, schedule controls, Node, image review,
host/dependency sealing and independent readiness remain pending. The historical
full regression remains FAILED at its unchanged 30,000 ms setup timeout.
