# C268 independent historical endpoint controls

The independent control author implemented and executed 34 `unittest` methods
against the candidate reader. The [final author run](evidence/control-author/run-03/results.json)
passed with **130 API calls: 120 historical-reader calls and 10 raw-interface
calls**. Outcomes were 12 historical admissions, 9 raw successes and 109 typed
refusals. There were no failures, errors, skips or untyped exceptions. Checked
implementation, test, fixture and dependency bytes stayed unchanged during the
run. This is candidate control evidence; independent review, affected-cohort
checks, integration and saved delivery are separate Director-owned gates.

## Independent expectations and input construction

Expected identities and fields come from the original `before.main.ok`,
`after.main.ok` and `hinges.ok` bytes and the unchanged
[C260 contract](../localized-repair-c260/CONTRACT.md). The two original rack
memberships are written explicitly in the control fixture: three keys on
`first` and five on `second`. Each occurrence owns one `flex` hinge, with the
shared Finger joint definition, ordered `pivot` and `blade.base` sites, signed
axis `(0, 0, 1)`, exact canonical limits of plus/minus 45 degrees and initial
zero. Their 16 site occurrences have source-only interface `hinged.part` and
zero canonical size. Their pose expressions remain unevaluated byte witnesses.

The fixture helper transcribes all five historical size/hash pairs from
[C260 INPUTS](../localized-repair-c260/INPUTS.json). A control checks those
transcriptions against the contract and checks C260's matching source pins
against the frozen C253 corpus. Neither the C268 reader nor any product parser,
evaluator, exporter, semantic sidecar, motion sample or C255 expected record
supplies expected hinge values.

Two supported paired recipes change actual source and actual GLB bytes:

- The same-size recipe changes the signed basis axis from `(0, 0, 1)` to
  `(0, 1, 0)`. It updates the leaf import pin, source hashes and canonical
  program revision. Equal-width edits preserve source spans and GLB lengths.
- The different-size recipe changes initial zero to `0.25[rad]` and rebuilds
  the necessary declaration spans and source/program/object provenance. It
  reuses only the exact pinned independent C266 provenance recipe helper.

The raw source and artifact observers expose the changed fields. C267 compares
both supported pairs successfully. Their raw historical flags remain false.
C268 refuses the same bytes as historical inputs; additional isolated leaf and
artifact checks prevent the changed entry source from masking those refusals.

## Requirement and control coverage

| Requirement / control | Independently exercised behavior | Evidence boundary |
| --- | --- | --- |
| R01, H01 | Both original endpoints; `Path`, absolute string and relative string roots; exact per-file admission identities; eight complete joints, one shared definition, 16 sites and 18 objects | Only the frozen before/after inputs are historically admitted |
| R01 | Missing each selected file; other endpoint substituted under the selected name; unselected endpoint absent | No alternative source/artifact fallback; only the selected three files are necessary |
| R03, H23/H28 preservation | Source witnesses, ordered endpoints, whole identities, source-only compatibility, unevaluated child offset, absent direct artifact site/definition/span authority; C267 records/provenance/nonclaims unchanged | No site-pose/world, physical, complete validity, accepted-revision, edit-atomicity, rebuild, native, trial or comparative qualification |
| R03/R04, H03 | Same-size artifact-only initial change remains visible through raw observation; raw comparison gives `FIELD_MISMATCH`; historical admission gives hash refusal | Raw observation, field agreement and historical identity remain separate |
| R03/R04, H04/H27 | Same-size paired axis and different-size paired initial recipes; raw API historical flags remain false; historical entry, leaf and GLB checks each refuse | A supported changed comparison does not grant historical admission |
| R02/R04, H26 | Missing source/leaf/GLB, missing repository root, short/long declared sizes and same-size changed hashes for both endpoints | Typed whole-input refusals, bounded available identities, no qualified partial set |
| R02/R04, H26 | Symlink leaves, fixed-path ancestor, repository root and ancestor above it; self-referential file/directory loops; traversal, invalid selectors/types, path-length/component limits | Invalid selector/root controls deny filesystem calls; no ambient fallback |
| R02/R04, H26 | Directory leaves; endpoint and dependency FIFOs with no writer | FIFO probes run in separate processes with five-second deadlines; both returned typed refusals without hanging |
| R02/R04, H26 | Real mode-000 permission denial plus explicitly injected `EACCES` at open/read; injected `EIO` at stat/read | Author runtime actually denied the mode-000 file at effective UID 1000; injections are separately labeled |
| R02/R04, H26 | No payload reads for declared wrong sizes or sparse inputs beyond inherited source/GLB ceilings | The controller derives sparse-input hashes from deterministic zero-byte recipes without reading those files |
| R02/R04, H26 | Truncation after initial stat, growth before read and growth after read; bounded positive read sizes; no comparator call after failed admission | Deterministic interposition resolves these races; it is not an exhaustive operating-system race proof |
| R02/R04 | Open descriptors close on success, size refusal and hash refusal | Finite exercised cleanup paths only |
| R03/R04 | Each of the five pinned dependencies changes after a prior successful call; missing/wrong-size comparator; dependency symlink/ancestor/FIFO | Dependencies are re-admitted on each call; changed dependency bytes are archived |
| R03/R04 | Actual unchanged C267 `Fault` translation after labeled comparison-argument interposition; six additional explicitly injected categories preserve reason/pointer and captured identities | Interposition tests propagation; it does not imply an error in admitted originals |

These controls cover the historical part of H01/H03/H04/H26/H27 and preserve
related authority boundaries. They do not claim to rerun or fully qualify all
H01–H28 source, artifact and comparison behavior. The complete inherited cohort
and a separate candidate review remain required by R05.

## Reproduction and evidence

Run the evidence-producing command with a new destination:

```sh
python3 -B docs/engineering/localized-repair-c268/test_endpoint_reader.py --evidence-dir /tmp/c268-new-controls
```

Standard discovery is also supported and was
[executed successfully](evidence/control-author/discovery-01/RESULTS.json):

```sh
python3 -B -m unittest discover -s docs/engineering/localized-repair-c268 -p test_endpoint_reader.py -v
```

The direct runner records each call's API, input identities, expected and actual
outcome, refusal category, reason and available identities. It reports
`historicalCalls`, `rawCalls`, `admittedCalls`, `rawSuccessfulCalls`,
`successfulCalls`, `typedRefusals` and `untypedExceptions`; the exact accounting
is checked. Per-run `checked-code` contains the new implementation/control
snapshots. Pinned dependencies are identified by exact size and SHA-256.
`inputs.zip` preserves unique changed bytes; unchanged historical inputs are
referenced by their frozen paths, sizes and hashes. Sparse files, symlinks,
directories and FIFOs have explicit reconstruction recipes.

| Author run | Observed result | Preserved interpretation |
| --- | --- | --- |
| [run-01](evidence/control-author/run-01/results.json) | 34 methods; 108 calls; 12 test errors | Control-author mistake: a pose witness was assumed to contain text. Its actual byte-offset representation was retained. The correction slices the supplied bytes; it changes no expected source meaning or reader behavior. |
| [run-02](evidence/control-author/run-02/results.json) | 34 methods; 128 calls; pass, zero skips | Corrected witness check; complete historical and dependency controls passed. |
| [run-03](evidence/control-author/run-03/results.json) | 34 methods; 130 calls; pass, zero skips | Final suite adds direct raw-field assertions, sparse recipe hashes, bounded invalid-root cases and actual C267 refusal translation. |
| [discovery-01](evidence/control-author/discovery-01/RESULTS.json) | 34 methods; pass, zero skips | Standard discovery compatibility on the same final code; discovery does not export the detailed API call ledger. |

The original failed run and intermediate passing run remain unchanged. No
implementation, predecessor, historical fixture or contract was edited by the
control author.
