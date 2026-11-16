# C249 independent review

**Approved for the bounded held-source publication and handoff.** This approval establishes no Godot execution admission, native behavior or R07 completion.

Exact final author commit: `feb5efe78c8c748fc51f455a59619a82ec5652d0`. Tree: `79b6988d2695a59b9fe7856b3e4fb476758d44f4`. Base: `bc235deca57c032fdd9a3b310274f1c130631e0e`. All eight changes are additions confined to `docs/engineering/second-target-c249/`; inherited source, fixtures, contracts and tolerances are unchanged. `EXACT-REVIEW-SOURCE.json` records each approved file's repository path, byte count and SHA-256, plus all 23 primary-source pins and 13 authority/dependency hashes.

## What was independently checked

The independently assembled synthetic fixture uses different native identities, names, resource keys and track order from the author's fixture. **197 cases / 3133 assertions pass.** The tests cover all 18 target identities, complete translation/rotation-role accounting, first-error partial records at every one of the 36 track position, compressed/executable routes before payload access, wrong/consumed registry state, predecessor refusal, metadata failures, wrong resource lookups, queued/scripted/mixed scenes, changed settings/resources/targets, final registry faults, receipt detachment and reader reuse.

The model tests ran on exact corrected commit `6d1b2cc8f9aef745ee29a60d183f38de3e294c40`. The final native source, model and author controls are byte-identical to that tested snapshot. `FINAL-SOURCE-CONSISTENCY.json` verifies this equality, all 23 primary-source pins, all 13 authority hashes and the eight-file isolated scope in **40 checks**. No unchanged model rerun was needed for the later documentation/binding additions.

**210 independent source/API/fixture checks pass.** They validate original GLB bytes and channel roles; exact upstream receipts; the generated player/default-library construction; the export-only status of GLTFState's player list; actual NodePath resolver semantics; public getter/property availability; enum/default values; and source ownership, refusal and no-execution boundaries. The author separately reports 41 model methods and 371 binding checks; those are author evidence rather than additional independent executions.

## Identity and selection judgment

The finite single-animation association is supportable under the exact source and pinned generation route. The importer constructs one AnimationPlayer under its returned root and inserts the one source animation into its default library. C249 observes actual player/library/Animation identities and checks the resource through both native lookup routes. It neither invents an identity from a source name nor asserts a nonexistent public pointer from GLTFAnimation to Animation. This remains conditional source-supported provenance, not installed-import attestation.

For admitted nonempty relative track paths with zero subnames, the component uses the same underlying node resolver as the pinned AnimationMixer transform route. The result must match the C248/C246 observed final node identity. Names and ordering do not rescue an unresolved, retired or foreign target. The special `RESET` key is refused because its name has mixer behavior. GLTFState's export-only player getters are never used.

The component reads an animation candidate and track inventory. It does not assign a playback animation or disable advancement. The detached player retains checked native active/idle defaults; actual assignment, advancement control and the 126 world-pose observations remain separate work. The documented model boundaries accurately state that fabricated resolver and metadata inputs do not emulate Godot.

## Findings and corrections retained

**C249-F01:** Initial native source `b2b8f98b2270df607a04c87536e7d6f44316b3bc` resolved an unsupported root path before checking its shape. The pinned detached-node resolver can emit an engine diagnostic for an absolute path. Corrected source validates and records the path first. Independent controls confirm zero resolver calls for rejected root paths, and the final static order check passes.

**C249-F02:** Initial model `049e4878327bf4f1a02e5e95dfe028a6bb095506` allowed strict settings metadata conversion to escape as ValueError. The initial independent run contained 194 cases, with 190 passing and 4 recorded failures. Corrected model `6d1b2cc8f9aef745ee29a60d183f38de3e294c40` preserves incremental settings/queue refusal evidence and returns the explicit failed receipt. The final 197 cases all pass. Earlier failures remain in their original reports.

An expanded reviewer static-check invocation ran before the author finished a new StringName retrieval receipt and stopped on its missing `bytes` field. That reviewer timing error is preserved in `source-boundary-pre-freeze-interrupted.log` and `CONTROL-CORRECTIONS.json`. After the author froze all 12 complete retrieval receipts, the 210 checks passed. It was not a production-source failure.

## Evidence and remaining limits

Primary results: `APPROVAL.json`, `EXACT-REVIEW-SOURCE.json`, `ADVERSARIAL-FINAL.json`, `SOURCE-BOUNDARY-RESULT.json`, `FINAL-SOURCE-CONSISTENCY.json`. Scripts, original failures, correction records and exact snapshot manifests remain alongside them. `SNAPSHOT-RESTORE-MAP.json` reconstructs temporary review copies from the preserved Git commits; duplicate working copies can be omitted after review completion.

No Godot/version/parser/native/product/aggregate start occurred. No key times or values, poses, rendering or persistence were observed. Rechecks do not prove atomicity or lifetime safety under concurrent mutation. Installed lineage, complete diagnostics, hard limits, raw sealing, serialization, launcher/reservation and full admission remain unresolved. R07 stays pending. The original strict Blender-normal failure is unchanged.

Review completed at 2026-11-15T23:05:46.477539+00:00 in the same shared Linux environment as the other workers. Main integration, publication readback, archive verification and confirmed saved delivery belong to the main agent.
