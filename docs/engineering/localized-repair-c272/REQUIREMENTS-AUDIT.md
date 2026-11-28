# C272 requirements audit (TASK-031)

This is the Director's audit of the candidate `f955dafd6009ead2fc957ef8fd2cec5c40d3642f` and of
the records added at the audit's own commit. After the first independent review, `3c206ac7`
changed the scope's evaluator code and controls, and the evidence moved to the run at that
revision. The audit's preservation, model and C271 findings were checked again on the
corrected candidate and still hold: the same paths are unchanged, and nothing under `ontokin/`,
`tests/`, `tools/` or `examples/` changed. It was written against the evidence files
themselves. It is **not** the independent review that REQ-026 requires; that review follows
in TASK-032.

## Changed files and their requirements

`git diff --name-only 38ee8d18 HEAD` changes these paths:

| Path | Files | Requirement |
| --- | ---: | --- |
| `STATUS.md` | 1 | REQ-004, REQ-030 |
| `docs/workflow/CURRENT.json` | 1 | REQ-002, REQ-030 |
| `docs/workflow/tasks/C272/` | 4 | REQ-001, REQ-002, REQ-030 |
| `TRDs/trd_c253-…_2026-11-27.md` | 1 | REQ-002 (DEC-004: the approved TRD unchanged, SHA-256 `9102a137…7222db`) |
| `docs/engineering/localized-repair-c272/*.py`, `*.mjs` | 16 | REQ-008 to REQ-022 (traced in GAPS.md, G1 to G8, plus `validate_glbs.py` and `inspect_playback.mjs` for REQ-022, and `run_observer_regression.py` for REQ-024) |
| `docs/engineering/localized-repair-c272/*.md`, `START-STATE.json` | 8 | REQ-001, REQ-004, REQ-007 to REQ-009, REQ-019, REQ-028, REQ-029 |
| `docs/engineering/localized-repair-c272/evidence/` | the rest | REQ-012 to REQ-025, REQ-028, REQ-033 (MANIFEST.json lists them with SHA-256) |

Nothing under `ontokin/`, `tests/`, `tools/`, `examples/` or `pyproject.toml` changed. No
language feature, shape syntax, physical behavior, protocol version, transport or export
target was added. The work found no change of that kind to be necessary.

## Preservation

Each of these is byte-identical between `38ee8d18` and the audited commit; `git diff` lists no file under any of them:
- the C253 directory (protocol, scoring, run plan, corpus);
- the C210 proof files and the keyed-rack fixture;
- C255, C256, C257, C258, C261, C265, C266, C267 and C268;
- C270's and C271's directories and task records;
- `tools/package-lock.json` and `tools/local-environment.json`.

`observe.py` additionally refuses to load any reused component whose SHA-256 differs from its pin.

## Model and run plan

No component calls a language model, and the client is fixed in `runner.py`. `RUN-PLAN.json` is
unchanged: its model fields stay null, `qualifiedRoutes` stays empty, and no pin, seed or
token count was invented. No record of this scope is an attempt in the sense of the run plan.

## C271

The task's plan has no step that carries out, completes or depends on C271's phases P02 to P38,
the current-host readback contracts or gate MR. The branch started at `38ee8d18` and uses no
commit that only pull request 274 holds. The plan has no phase whose only result is a record
that no requirement needs.

## Requirement states

The states in [REPORT.md](REPORT.md) were checked against the files they point to. Each "met"
rests on a retained file, read here:
- `RESULTS.json` of the delivered run and the replay;
- each case's `score.json`, `rebuild.json`, `accepted-state.json` and `exchanges.jsonl`;
- `REPLAY.json`, the GLB validation summary, `PLAYBACK.md`, `VISUAL-PROFILE.json`, `CHECKS.json` and `CANDIDATE-CHECKS.json`.

Open at this audit:
- REQ-026, the independent review;
- REQ-027, integration and resulting-main checks;
- REQ-030, the local closing state.

REQ-024 is met by the driver at `d10c9f62`, whose result applies unchanged to this candidate
(CANDIDATE-CHECKS.json gives the reason). The observer regression with this scope's group,
the documentation verifier and the workflow check also passed on `f955dafd`.

## Failures kept visible

- The qualification attempt at `cad34f35` crashed (no RESULTS.json).
- The run at `4aff6024` failed P03 and R04; it is retained.
- The replay at `f0e4148f` was refused; it is retained.
- The driver's known baseline unit-test failure is recorded.
- Installing `node@22` broke the owner's default Node.js 25.9.0. It is reported and not repaired.

None of them is presented as passed.
