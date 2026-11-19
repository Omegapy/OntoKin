# C267 verified candidate results

The published candidate `1f369cb49f95f7df220ff91c78caa090dcbf2fcc`
passes all eleven declared groups, 247 test methods and fourteen C253 corpus
bindings. Checks ran in a clean isolated checkout on CPython 3.12.14 / Linux
x86-64 in the assistant workspace. No GitHub Actions or owner-machine run is
claimed. [CHECKS.json](evidence/candidate/CHECKS.json) records the exact commit,
tree, interpreter executable identity, commands, inputs, timings and log hashes.
All selected inputs and the tracked source tree stayed unchanged during execution.

| Group | Methods | Result |
| --- | ---: | --- |
| c253-corpus | — | passed |
| c255-oracle | 31 | passed |
| c256-reader | 29 | passed |
| c257-ownership | 23 | passed |
| c258-follows | 28 | passed |
| c261-hinge_glb | 28 | passed |
| c265-source_hinges | 49 | passed |
| c266-binding | 34 | passed |
| c267-comparison | 25 | passed |
| workflow | — | passed |
| documentation | — | passed |

The C267 public controls passed 25 methods and 123 API cases: 35 agreements and
88 expected typed refusals. The full preceding C266 cohort passed 34 methods
and 748 calls. All component suites have zero failures, errors or skips. The
C253 static corpus retains fourteen exact input bindings; it starts no product,
native or model execution.

## Independent review

The [separate reviewer](REVIEW.md) approved the exact comparator and final
control code. Its seven additional composition probes passed: two agreements
and five expected field-mismatch refusals. They exercise two hinge definitions
sharing sites, crossed ID/path pairs, removed rows and endpoint swaps. The
reviewer also audited 361 retained input-byte witnesses from the control author.
The [review receipt](REVIEW.json) binds fifteen inspected files; later metadata
publication must preserve those bytes. No blocking implementation finding remains.

## Preserved attempts and limits

The three control-author development runs all passed on their own recorded
bytes and are retained under [control-author](evidence/control-author/).
Initial workflow metadata checks failed on missing schema fields; their exact
reasons and corrections remain in [startup evidence](evidence/startup/workflow-initial-failure.txt).
Two terminal Git push attempts failed because terminal credentials were absent;
GitHub object creation and expected-head ref updates succeeded instead. A tiny
implementation-development harness initially called a fixture byte property as
a method and failed before comparator execution; its corrected probes passed.
None of these attempts is relabeled as an original success.

This isolated observer changes no product parser, evaluator, exporter, adopted
contract, fixture, dependency or hosted-job definition. Its complete affected
cohort is documented in the [plan](../../workflow/tasks/C267/PLAN.md).
Full product aggregate, source conformance/export, native/visual/model trials,
other Python compatibility and hosted workflows were not run. Historical
failures remain unchanged, including the older aggregate's thirteen torque-read
methods not run after its recorded setup timeout.

Agreement covers only finite hinge declaration fields, complete joint sets and
ordered endpoint associations. Historical admission remains absent. Site poses,
world alignment, full source/glTF/C255 validity, accepted revisions, atomicity,
rebuilds, native/model success and comparative advantage remain unqualified.
C260 H01/H03/H04/H26 therefore retain historical gaps, and no full H-group or
product release closure is claimed. [Coverage](CONTROL-COVERAGE.md) maps actual
assertions to inherited and still-unrun obligations.

Integration, resulting-main checks, branch disposition and required saved
delivery remain separate gates in the [task](../../workflow/tasks/C267/task.json).
