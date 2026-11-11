# C200 execution protocol

**Revision:** `OK-QUAL-STATIC-TRAY-C200/0.1.0`  
**Authority:** [ADOPTION.md](ADOPTION.md), effective for actual starts only after independent approval of the exact input lock  
**Machine-readable definition:** [QUALIFICATION.json](QUALIFICATION.json)

## 1. Recover and freeze before native work

Preserve C199's actual stopped result. Its original N01 consumed one failed
construction; N02–N12 remain unstarted and permanently closed to continuation.
Verify the ten failure-evidence bindings in QUALIFICATION.json, including the
captured archive containing the partial `.blend`. Do not open that partial
scene in another native process. The original 280-file executable source
closure is checked against the retained equal published tree. Do not claim
recovery of an unavailable original local Git object merely because its source
bytes match.

Review the repaired worker against exact pinned exporter source, including the
complete execute path, active debug state and callback lifecycle. Commit the
actual candidate before sealing. The immutable lock binds both frontends,
shared worker/settings, reader and corruption writer, receiver, transaction
and store code, all source/expected fixtures, protocol and coordinator bytes,
full Blender distribution, host runtime/libraries, Node/dependency closure,
expanded commands/environments, new output paths and preserved failed cohort.
No installed dependency is modified.

`inventory_host.py` takes explicit output and Blender paths. It reobserves the
actual host interpreter, standard library, loader configuration and the bounded
overinclusive system shared-library set. Trusted `ldd` inspection does not
invoke Blender main. `prepare_inputs.py` reuses the exact C199 distribution-
relative inventory and checks every current installed file, directory, mode and
link through the full verifier. Copying the relative inventory does not by
itself assert the new installation matches.

The three synthetic readback controls have their own prior reviewed harness
and input binding, no retries, and separate actual start counts. The unchanged
historical test file must not silently skip because it contains old absolute
paths. The new harness supplies only verified current paths and preserves the
underlying test/expected behavior. These synthetic controls do not satisfy any
actual-delivery acceptance gate.

## 2. Independent approval and one coordinator invocation

After preparation, the reviewer runs the full read-only input verifier and
reviews the exact protocol gate. The approval keeps the existing
`ontokin.static-tray.input-approval/0.1.0` readiness/evidence fields and adds:

- `qualification_revision_id`: `OK-QUAL-STATIC-TRAY-C200/0.1.0`.
- `qualification_revision_sha256`: SHA-256 of the exact QUALIFICATION.json.
- `preserved_c199_input_lock_sha256`: the original failed C199 lock hash.
- `authorization_scope`: exactly QUALIFICATION.json's `allowance` object.

Every readiness gate must cite actual immutable receipts. The approval is
created by a reviewer independent of the producer/preparation author. A
fixture, mock or installed-file inventory cannot substitute for actual native
qualification.

The sole authorized entrypoint is `run_qualification.py --lock <exact-path>`
using the lock's actual CPython interpreter, `-IBS`, and exact host environment.
The lock records this full command. The wrapper checks C200 revision identity,
the old consumed evidence, complete approval and absence of the new schedule.
It exclusively creates a separate invocation receipt before entering the
shared runner. An existing invocation receipt blocks a second call even if
the prior outcome is unknown or the schedule directory is absent. Investigate
such an outcome through retained process/ledger/store evidence; do not clear
receipts or restart.

The shared coordinator verifies the same input lock again and uses the original
nonretrying production transaction implementation. Its result remains bound to
the lock hash. The C200 wrapper records separate and cumulative C199/C200 start
counts without relabeling C199 as successful. A measured pass still leaves
actual visual and independent result review pending.

## 3. New finite schedule

Slot names are local to the new C200 lock; C199's identically named slots stay
in their immutable failed cohort. The construction order is unchanged:

| C200 slots | Case and purpose | Order |
| --- | --- | --- |
| N01–N02 | Q01 baseline | OntoKin, direct Python |
| N03–N04 | Q01 clean regeneration from retained baseline source | OntoKin, direct Python |
| N05–N06 | Q02 minimum/maximum dimensions and placements | OntoKin, direct Python |
| N07–N08 | Q03 finite rotations and composition | OntoKin, direct Python |
| N09–N10 | Q04 scoped left repair | OntoKin, direct Python |
| N11–N12 | Q05 left reuse with retained accepted revisions | OntoKin, direct Python |

Each slot permits at most one construction start, including failure, timeout,
cancellation and unknown outcomes. A valid construction can trigger at most
one receiving process, which reopens the saved native scene, imports the final
GLB, measures both and renders at most one assigned image. Required receiving,
cleanup and sealing checks precede accepted-pointer promotion. Promotion is
only transaction acceptance; the whole profile still requires the complete
cohort and its independent review.

After each accepted transaction, one separately bounded Node process performs
Khronos and Three.js checks on that actual delivery. There are at most twelve
such starts, with the original 30,000 ms outer and 28,000 ms child-work limits.
The nine retained D01–D08 corruption variants run on copies of actual delivery
bytes at their original assigned points, including both D08 variants. They
make no new native construction and must preserve the original accepted
closure. All classification requirements remain those of the unchanged
[C198 controls](../static-tray-mapping-c198/CONTROLS.json).

Stop the whole schedule at the first unexpected transaction, external
readback, corruption, cleanup, persistence or identity result. Do not rerun a
slot, resume its later stages after a reported stop, change inputs mid-cohort,
repair a receipt or relax an expectation. Retain the partial result and propose
a separately reviewed later revision if a repair is needed.

## 4. Limits and complete outcome

The source 100,000-operation/30,000 ms limits and complete 65,000 ms transaction
structure are unchanged. A stage can start only when the remaining original
clock permits its full allowance. Mandatory group cleanup and reaping precede
promotion. Original native-output, GLB, result and log caps, 50 ms polling,
500 ms termination grace and 2,000 ms cleanup allowance remain enforced.
No deliberate actual-Blender cancellation trial or extra process-lifecycle
cohort is authorized.

Technical qualification requires all twelve valid raw/final deliveries;
independent geometry/identity/clearance evidence; paired and clean-regeneration
equality; unchanged right siblings; accepted-source preservation; the nine
actual-delivery corruption outcomes; twelve receiving measurements and
Khronos/Three.js checks; actual review of all required images; and independent
result review. Preserve failed and skipped gates. A stop or a missing required
receipt keeps the profile unqualified.

Later public tray admission is separate and still limited to four exports
total, one baseline plus one clean regeneration per route including failures.
No timed author exercise belongs to this protocol. Historical regression,
contact/live physics, external roles, comparative advantage and full-product
acceptance retain their current unmet status.

## Preparation commands

Use the execution checkout's committed scripts and new output paths. In the
commands below, replace the absolute placeholders with observed local paths;
the final lock records the fully expanded values.

```sh
<python> -IBS <repo>/docs/engineering/static-tray-exporter-c200/inventory_host.py \
  --output <repo>/docs/engineering/static-tray-exporter-c200/evidence/preflight \
  --blender <blender-root>/blender

<python> -IBS <repo>/docs/engineering/static-tray-exporter-c200/prepare_inputs.py \
  --repo <repo> \
  --output <repo>/docs/engineering/static-tray-exporter-c200/EXECUTABLE-INPUTS.json \
  --schedule-root <new-c200-schedule> \
  --blender-root <blender-root> --blender-archive <exact-blender-archive> \
  --host-inventory <repo>/docs/engineering/static-tray-exporter-c200/evidence/preflight/HOST-RUNTIME-INVENTORY.json \
  --preflight-directory <repo>/docs/engineering/static-tray-exporter-c200/evidence/preflight \
  --dependencies-root <verified-retained-readback-root> --node <exact-node-executable>
```

These commands create no approval or geometry output. Once sealed, the lock is
immutable. Preserve any failed preparation output and make a separately named
replacement preparation record rather than overwriting an attempted lock.
