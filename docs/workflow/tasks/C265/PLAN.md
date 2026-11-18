# C265 implementation plan

Owner: `c265-root-b4cbf4ea8454`. Branch: `work/c265-source-hinge-observer`. Base: `82c998eb17a12cc0dfa04bad45fe728e82764704`. [Scope256](https://github.com/Omegapy/OntoKin/issues/256). Machine-readable state: [task.json](task.json).

## P01. Publish bounded scope and recoverable starting checkpoint

Requirements: R01, R02, R03, R04.

Verification: Reconcile pinned startup files, live refs and source archive manifest.

## P02. Implement the source interface and independent source controls

Requirements: R01, R02, R03, R04, R05.

Verification: Execute independently specified source controls and manual byte-witness inspection.

## P03. Verify exact candidate and resolve independent review

Requirements: R01, R02, R03, R04, R05.

Verification: Run C265 controls, inherited C253/C255/C256/C257/C258/C261 component cohorts, workflow and documentation checks; no runtime/exporter changes are planned.

## P04. Integrate under the verified lease and check actual main

Requirements: R06.

Verification: Read back PR merge and main tree, verify code/input equality and rerun applicable focused checks; verify branch retention and deletion.

## P05. Freeze, verify and save handoff, record receipt and close

Requirements: R07, R06.

Verification: Verify exact ZIP and fresh extraction against pinned Git snapshots, save in existing OntoKin folder and inspect returned identity, publish receipt and release lease.

## Ownership and sequencing

The Director owns task records, documentation, evidence integration, STATUS/CURRENT, Git index, all remote writes and delivery. The source-observer worker owns only `docs/engineering/localized-repair-c265/source_hinges.py`; an independent control worker owns only its separate source control file. A separate reviewer receives the published candidate and acceptance contract. Shared checkout disjoint edits are allowed; workers do not commit or write main. Publish this plan before implementation, checkpoint actual bytes after implementation, review, integration and delivery, and preserve any unknown write identifiers before readback.

The source observer changes no released runtime/import route. Required regression is the complete relevant independent observer cohorts and source corpus validation. Broader full product/visual/compatibility release runs are not applicable to this isolated component increment and remain not-run, with historical failures unchanged. If implementation touches shared product machinery, revise scope and run its complete inherited obligations before integration.
