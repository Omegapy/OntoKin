# C193 explicitly selected guided-contact prototype

This prototype selects the [C193 contract](../../docs/language-design/guided-contact-v0.2/SPECIFICATION.md).
It uses source `c193-experimental-0.1`, backend `blender-bullet-c193-0.1`, and the
unchanged `guided-box-contact-0.1` / `glb-guided-contact-0.1` meanings. The original
v01 package and its historical evidence remain unchanged.

Only the native GENERIC guide iteration overrides change physically: both use
400 instead of 100. World and motor iterations remain 100. The source controls
geometry and relationships; Blender/Bullet still controls motion. There is no
programmed stopping time or position, and recording retains native X/time.

The new package is an explicit fork of the finite v01 implementation. Its
source/backend selectors, contract location, native/store/diagnostic namespaces,
generator label and retained package path identify C193. Constructor, solver
capture, parser validation, transaction, supervisor and projection algorithms
remain inherited. This duplication keeps original bytes and entry points stable.

## Run

Use the pinned Blender 4.5.3 executable with SHA-256
`5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397`.

```sh
python -m prototypes.guided_contact_v02 validate \
  docs/language-design/guided-contact-v0.2/examples/E.ok \
  --host-max-operations 1000000 --host-max-elapsed-ms 80000

python -m prototypes.guided_contact_v02 run \
  docs/language-design/guided-contact-v0.2/examples/E.ok \
  --store /tmp/c193-E --blender "$BLENDER" \
  --host-max-operations 1000000 --host-max-elapsed-ms 80000 \
  --result /tmp/c193-E-result.json
```

Use a distinct store for the new `ontokin.c193.store/0.1` envelope. An attempt's
`state.json` is its accepted-state pointer. Failed attempts retain their exact
source and partial diagnostic artifacts; a file named `final.glb` is accepted
only when the transaction commits and every required independent gate passes.

`run --reopen PATH/scene.blend` preserves the original native-replay semantics.
The same source must match the stored scene. `--expected-revision` and
`--cancel-file` retain the original atomicity and bounded cancellation behavior.
Ordinary defaults remain 100000 operations and 30000 ms. Qualification limits
must be explicitly authorized by the host as shown above.

The new binding is qualified only to the extent established in its separately
identified C193 evidence. It does not establish general contact, all admitted
stop coordinates, a production backend, comparative authoring advantage or a
complete release.
