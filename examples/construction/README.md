# Pinned component and keyed assembly demonstration

This example exercises language `0.2` / `construction-0.1` through the separate `ontokin.agent/0.2` interface. One exact-pinned library supplies a reusable articulated component. The entry program generates two assemblies from immutable keyed inputs, then an agent-style client inspects, diagnoses, repairs, evaluates, and exports the complete program.

**Release status:** the experimental 0.4.0 milestone passed its complete local, destination and CI gate. The [identified evidence](../../docs/engineering/construction-validation/validation-summary.json) and [STATUS](../../STATUS.md) record the result and the next unmet goal. The [language contract](../../docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) and [program-agent contract](../../docs/engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md) define the promised scope; successful playback alone does not close that gate.

## Build and open the animation

From the repository root, using Python 3.11 or later:

```bash
python3 tools/build_construction_demo.py --help
python3 tools/build_construction_demo.py --output-dir /tmp/ontokin-construction-demo
```

The driver uses a fresh temporary local store and the [complete Rack fixture](../../docs/language-design/construction-v0.1/01-keyed-rack/program.bundle.json). It starts with the first middle finger's length set to `0.65[m]`, rejects `0.75[kg]`, and repairs that occurrence to `0.75[m]`. The accepted result must reproduce the separately specified fixture identity, dimensions, and 126 world poses. The shared library and the other assembly remain unchanged. Export and chunked retrieval use actual program-agent requests.

Open [the existing offline viewer](../visual/viewer.html) from a local checkout, choose **Open GLB**, and select `/tmp/ontokin-construction-demo/keyed-rack.glb`. To regenerate the files beside this guide, run the driver without `--output-dir`; its default is `examples/construction`.

The two-second animation has these intended observations:

- The left assembly has three keyed fingers; the right has five. Each finger contains its own blade, mounting follow, and prescribed hinge. Two racks, eight fingers, and eight blades make **18 objects**.
- The first rack moves `0.4 m` along world +Y. Its middle hinge turns through `45°` during the first second; the other fingers retain their own independent state.
- The selected blade is `0.75 m` long. The right assembly remains fixed and its blades retain the `0.6 m` default. All represented bodies in this fixture are massless; collection groups add no physical object or matter.

Use Play, pause, timeline scrubbing, orbit, and the object selector to inspect the result. The custom import route displays **“Local GLB · numerical status unknown”** and disables the source download control. That route loads only GLB bytes; it does not load this example's source bundle or export report. Use the separate files below for source and numerical evidence. The viewer reads local files without uploading them and plays recorded transforms without executing OntoKin physics.

## Source and output files

The builder writes the following files to the selected output directory. Their checkout copies are linked here when generated for the release.

| File | Role |
| --- | --- |
| [main.ok](main.ok) | Accepted entry source: two Rack occurrences, final keyed inputs, selected override, and actions. |
| [hinges.ok](hinges.ok) | Exact `example.hinges` version `1.0.0` library, containing public `three_mounts` and `Finger` definitions and a private `Blade`. |
| [program.files.json](program.files.json) | Explicit local file manifest loading the adjacent `.ok` files. |
| [program.bundle.json](program.bundle.json) | Complete inline snapshot of the accepted source closure, with the same logical filenames and exact source bytes. |
| [authoring.ok](authoring.ok) | Initial entry bytes with the selected length at `0.65[m]`; its complete request context is retained in the workflow. |
| [rejected-candidate.ok](rejected-candidate.ok) | Invalid entry bytes assigning `0.75[kg]` to a length; the previous accepted program remains intact. |
| [keyed-rack.glb](keyed-rack.glb) | Animation bytes exported and retrieved under `ontokin.glb/0.2`. |
| [keyed-rack.export.json](keyed-rack.export.json) | Artifact/program/source identities, conversion losses, tolerances, and decoded animation checks. |
| [keyed-rack.reference.json](keyed-rack.reference.json) | Agent-inspected poses, geometry expectations, and the identity of the independent formula oracle. |
| [workflow.json](workflow.json) | Complete actual requests and responses, accepted/rejected program identities, and checks performed by this driver. |

The [original entry](../../docs/language-design/construction-v0.1/01-keyed-rack/main.ok), [library](../../docs/language-design/construction-v0.1/01-keyed-rack/hinges.ok), [file manifest](../../docs/language-design/construction-v0.1/01-keyed-rack/program.files.json), and [independent expected results](../../docs/language-design/construction-v0.1/01-keyed-rack/expected.json) remain the fixed acceptance inputs. The driver reproduces those inputs; it has no arbitrary input-file option and makes no language-model call or authoring-efficiency measurement.

## Use local source files or an inline bundle

The editable program consists of its `.ok` files and explicitly supplied dependency manifest. An import names the package ID, exact version, and SHA-256 of the imported file's raw UTF-8 bytes. The resolver reads only supplied modules. It does not search ambient directories or download packages.

The two transport forms load through the same immutable `ProgramBundle` API:

```python
import json
from pathlib import Path
from ontokin.bundle import load_bundle, load_file_manifest
from ontokin.program_runtime import validate_revision

fixture = Path("docs/language-design/construction-v0.1/01-keyed-rack")
bundle = load_file_manifest(fixture / "program.files.json")
inline = load_bundle(json.loads((fixture / "program.bundle.json").read_text(encoding="utf-8")))
assert bundle.program_revision == inline.program_revision

result = validate_revision(bundle, level="evaluated")
print(result["outcome"], result["achieved_level"], result["program_revision"])
```

`load_file_manifest` accepts `ontokin.files/0.1`: an entry descriptor and dependency descriptors contain exact logical filenames and relative POSIX `path` values. All resolved source files, including symlink targets, must be regular files inside the manifest directory. Paths choose the local bytes to read; logical filenames, source identities, and hashes enter the program revision.

`load_bundle` accepts `ontokin.bundle/0.1`, with `source` strings in place of paths. `bundle.to_payload()` returns that exact inline representation for an agent request or stored snapshot. Editing `.ok` files does not automatically rewrite a previously saved inline bundle. Reload the local file manifest to form the new snapshot, and update every affected literal import digest when a library's bytes change. The agent service can validate those library and pin edits together as one candidate.

A source revision identifies one exact file. A program revision identifies the canonical manifest and every supplied source unit, including the entry and dependencies. Even an invalid, structurally well-formed candidate has a program revision for inspection. Runs, cursors, and exported artifacts retain the program they were created from; they are not reassigned when new source is accepted.

For direct compilation without durable agent state, `from ontokin.construction import compile_construction` supplies `compile_construction(bundle, level="constructed")`, whose `.model` is the normalized construction model. The `validate_revision` example above additionally validates the complete authored timeline at the evaluated level. The core `check FILE.ok`, `evaluate FILE.ok`, and `export FILE.ok` commands continue to use the single-source 0.1 parser.

## Use the program-agent interface

After loading `bundle` in the example above, a Python client can submit it through the durable service:

```python
from ontokin.program_agent import ProgramAgentService

request = {
    "schema_version": "ontokin.agent/0.2",
    "project_id": "my-keyed-rack",
    "request_id": "create-1",
    "operation": "create",
    "expected_program_revision": None,
    "requested_level": "evaluated",
    "bundle": bundle.to_payload(),
}
with ProgramAgentService(Path("/tmp/ontokin-own-program-state")) as service:
    response = service.handle(request)
    print(response["status"], response["program_revision"])
```

`handle` waits for the terminal response by default. `submit` returns a durable receipt, and `work_next` performs queued work. Repeat the same request identity with the same payload to retrieve its recorded outcome. A different payload requires a different request identity. Creating a new accepted head or editing an existing one also has the corresponding expected-program precondition.

For JSONL clients, select the new protocol explicitly:

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.2 --store /tmp/ontokin-program-state
```

Write one UTF-8 JSON request per line. This complete discovery request needs no source bundle:

```json
{"schema_version":"ontokin.agent/0.2","project_id":"my-keyed-rack","request_id":"discover-1","operation":"discover","profile":"construction-0.1","filter":{"name":"sphere"},"limit":5}
```

The default JSONL service returns queued receipts and processes work in a background worker. Use a fresh request identity to query the original request:

```json
{"schema_version":"ontokin.agent/0.2","project_id":"my-keyed-rack","request_id":"status-1","operation":"status","target_request_id":"discover-1"}
```

The outer status describes the lookup; `result.target.status` describes the work. For one request saved as `request.json`, wait for its result with:

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.2 --store /tmp/ontokin-program-state --request request.json --wait
```

Omitting `--wait` in one-request mode leaves ordinary work queued for a later worker. The protocol choice remains explicit: omitting `--protocol` selects `ontokin.agent/0.1`. The new service uses `program-agent.sqlite3`; the existing service retains its own `agent.sqlite3`, even when both use the same directory. Requests do not migrate between those stores by changing their schema field.

For an occurrence repair, inspect `source.initializer_target`. It supplies the selected root's writable identity and span, a typed `parameter_path`, valid `rendered_path`, and any existing assignment span. A key such as `"left.eye"` remains one key step. Each patch identifies its actual `source_id`, exact file `source_revision`, UTF-8 byte range, expected text, and replacement within the expected complete program. Generated occurrences and their shared library declarations have different edit authority. The [request](../../docs/language-design/agent-v0.2/request.schema.json), [response](../../docs/language-design/agent-v0.2/response.schema.json), and [diagnostic](../../docs/language-design/agent-v0.2/diagnostic.schema.json) schemas and [OK-AGENT-002](../../docs/engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md) define the complete operations and failure behavior.

## Supported scope and verification

| Boundary | This construction profile |
| --- | --- |
| Source | Language `0.2`, profile `construction-0.1`; at most 16 dependencies plus the entry and 2,000,000 aggregate UTF-8 source bytes. |
| Imports | One exact version per package, an acyclic supplied closure, at most eight import edges along any chain, explicit public aliases, and original definition identities. |
| Construction | Flat immutable typed `Keyed` inputs, at most 256 entries each, 1,000 actual objects, and 64 ownership edges along a path. Final public overrides resolve before nested generation. |
| Runtime behavior | The existing prescribed motion, joint, following, frame, and gravity/release subset. Collections cannot create or remove objects during animation. |
| Agent work | Bounded operations, time, result items, value materialization, and JSON envelopes; whole-program acceptance and revision-bound runs. |
| Delivery | `ontokin.glb/0.2`, retaining program and source provenance while playing sampled world transforms. Default position/rotation/time tolerances remain `0.001 m`, `0.001 rad`, and `0.000001 s`. |

The library definitions and generation recipe remain in `.ok` source. Export reports disclose the meaning retained only as metadata and what a GLB cannot execute. Contacts, general dynamic mechanisms, runtime topology changes, nested authored keyed inputs, rich geometry, controllers, and live destination physics remain outside this profile. The complete limits and type restrictions are in [OK-LANG-002](../../docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md).

The [C01–C20 manifest](../../docs/language-design/construction-v0.1/validation-cases.json) fixes positive, boundary, negative, composition, scoped-edit, lifecycle, and actual delivery expectations. The [module cases](../../docs/language-design/construction-v0.1/module-cases.json) include concrete invalid bundles and exact expected diagnostic origins. The [construction runner](../../ontokin/construction_conformance.py) can execute the adopted cases:

```bash
python3 -m ontokin.construction_conformance --help
python3 -m ontokin.construction_conformance --output /tmp/ontokin-construction-conformance.json
```

A run without the required identified external evidence leaves the actual-delivery gate pending and returns exit status `2`. Retained external reports are checked through the runner's `--external-evidence` option; loading them is separate from rerunning their validator or browser. The release also requires the full Python suite, unchanged core and agent cases, independent format and decoded-pose checks, actual viewer inspection, and relevant CI for the identified implementation. Follow [STATUS](../../STATUS.md) for that final gate and [the original agent demonstration](../agent/README.md) for the preserved 0.1 workflow.

### Optional independent JSON Schema check

After building the demo above, the [schema checker](../../tools/verify_program_schemas.py) validates all five published schemas, both bundle transports, and the actual workflow's request, response, and diagnostic records. Its development-only dependency is `jsonschema==4.25.1`. This recipe installs it into an isolated temporary directory; the OntoKin runtime continues to use only Python's standard library.

```bash
ontokin_schema_deps=$(mktemp -d /tmp/ontokin-schema-deps.XXXXXX)
python3 -m pip install --target "$ontokin_schema_deps" jsonschema==4.25.1
PYTHONPATH="$ontokin_schema_deps" python3 tools/verify_program_schemas.py \
  --demo-dir /tmp/ontokin-construction-demo \
  --output /tmp/ontokin-construction-schemas.json
```

The checker resolves schema references from an explicit local registry and records schema, workflow, implementation, and validator identities in its report. Schema checks complement the runtime's semantic, exact-byte, resource, and concurrency checks; they do not establish those results independently.
