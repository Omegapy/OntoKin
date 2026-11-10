# C191 independent continuation review

**Decision: accept the assigned finite source, fixture, native-evidence and destination qualification scope. No blocker was found in this scope.**

The reviewed repository head is `2c140286a3b1ca0ef0d3b435f8280ccafaf03490`. This review verifies the surviving C191-R2 evidence and executes a fresh portable numerical replay plus the 32 public-CLI source-conformance cases. It does not claim new native builds or new saved-scene simulations. The original nine native builds and nine fresh-process scene replays retain their C191-R2 identity.

The machine-readable findings and hashes are in `AUDIT-RESULT.json`. `portable-replay.json` contains the fresh numerical results. `DELIVERY-MAP.json` identifies the exact A–D artifacts for the outgoing handoff. All new review files were written under this review directory; the adopted contract, frozen fixtures, historical controls, existing implementation and original evidence were not edited.

## Frozen expectations and provenance

The original semantic, checker and source seals remain valid. Their 6, 16 and 62 manifest entries all match; these counts include overlap between manifests. The source freeze is SHA-256 `3d19e48b080119172eb9793ea39065c3245317b6c00a1377a080fccf913d8a81`. Every adopted-contract entry and the separately reviewed C191-A1 admission amendment also match.

The chronology is consistent with the required independent freeze:

| Event | Recorded UTC time or commit |
| --- | --- |
| Semantic expectations frozen | 2026-11-10 02:56:22 |
| Playback checker and analytic controls frozen | 2026-11-10 02:59:44 |
| Exact source fixtures and diagnostics frozen | 2026-11-10 03:06:40 |
| Contract adoption published and read back | 2026-11-10 03:08:00; commit `a1cde0a1aed54513bac30037e8356dee8ef75f09` |
| First source implementation checkpoint | Commit `61d14d39d176af49ec3c02f9b63292a1e115d031`, a descendant of adoption |

The adoption tree contains no prototype implementation files. The freezes explicitly record that the independent reviewer had inspected neither implementation nor candidate output. Git ancestry preserves the adoption before implementation. This continuation inspected those expectations before reading C191 result artifacts, and created no replacement freeze.

The expected A/B/C travels remain 200/175/187.5 mm, derived from the initial 180 mm shoe face and the 380/355/367.5 mm stop faces. Their ideal contact times remain 1.6/1.4/1.5 s at 125 mm/s. Disabling only the left shoe collider requires 250 mm travel and a −50 mm signed final gap. Every case requires 300 mm right travel and a 15 mm right gap.

The fixed gates remain 0.5 mm maximum positive-case penetration, 0.5 mm/s residual speed after the 25 ms settling interval, 0.1 mm rebound, 0.2 mm projection deviation, and continuous nonoverlap of all twenty unrelated part pairs. Exact error codes, phases, UTF-8 spans, blocked levels, resource ceilings and rollback obligations remain sealed.

The twelve pinned C190/.22 historical checker, source and output controls match their inherited hashes. No old contact rejection or pass-through expectation was replaced.

## Archive integrity and implementation identity

Both committed evidence archives match the qualification receipt:

| Archive | SHA-256 | Verified manifest entries |
| --- | --- | ---: |
| `qualification-evidence.tar.xz` | `392cce364da6b4f589bd41c49076feac31792dbfb6c059d425488c9d56370495` | 7,339 |
| `author-recovery-evidence.tar.xz` | `0b071b12330601ca51cd312cac0fb7d5f8c3a7afca7c2b8f2ee3b52d924a523f` | 1,757 |

Every listed file was rehashed after extraction. The qualification archive covers 591,086,576 uncompressed bytes. Its historical summaries retain their original absolute paths; the portable replay uses a temporary relocated view and leaves the original summary unchanged.

The formal input lock identifies tested revision `de813a652ab5380a9c96f2a72ad9bd9ce5bbb96e`. All 60 prototype files, 14 contract files and 17 checker files in that lock match the reviewed current head byte for byte. The retained execution evidence therefore applies to these unchanged implementation and verification inputs.

## Native evidence and recorded output

The portable replay passed all nine formal builds: two each for A–D and one renamed/reordered E control. Each final GLB passed the original frozen checker, and each raw/final pair passed the preserved mapping audit. All 481 reopened native samples equal the corresponding build samples for all nine saved scenes. The saved receipts record cache clearing and no scene reconstruction or repair.

All repeated canonical inputs, raw GLBs, final GLBs and native traces are byte-identical. E has different source bytes while preserving A's canonical physical input and final GLB. Disabling the left shoe collider preserves the native base, both stops and the entire right lane, while the left lane changes from stopping to pass-through.

| Case | Native left travel at 2 s | Final signed left gap | Maximum positive-case penetration |
| --- | ---: | ---: | ---: |
| A: 380 mm stop | 200.000018 mm | −0.0000065 mm | 0.0119573 mm |
| B: 355 mm stop | 175.000012 mm | −0.0000065 mm | 0.0119573 mm |
| C: 367.5 mm stop | 187.500000 mm | −0.0000065 mm | 0.0075912 mm |
| D: collider disabled | 250.000000 mm | −49.9999886 mm | Pass-through is the required outcome |

Every final clip has 481 common keys and 480 intervals. All twenty unrelated pairs pass continuous nonoverlap checks across every interval. All enabled cases have zero measured finite-difference speed after their frozen settling boundary. Maximum rebound is 0.0119508 mm, below 0.1 mm. The right final gap is 14.9999829 mm in every case.

The largest continuous raw-to-final vertex-deviation bound is **0.0851883 mm**, and the largest native-sample deviation is **0.0813021 mm**. Both are below 0.2 mm. The mapping audit preserves every native carriage X sample and timestamp; it permits only the adopted removal of rotation and transverse guide residuals.

The fresh analytic-control qualification passed **8 positive, 54 negative and 3 swept-slab controls**, reproducing the sealed control bytes. Geometric contact-band timestamps and finite-difference speeds remain recorded-pose observations. These records do not establish direct Bullet contact impulses, manifolds, velocities or unrecorded substep trajectories.

## Source diagnostics and failure boundaries

Fresh public-CLI validation passed **32/32 cases** on the reviewed current head. This includes six valid/default/identity cases and 26 source negatives. Invalid-source results match exact code, phase, UTF-8 byte span and blocked-level expectations. Valid cases reproduce independently derived canonical input bytes. Validation commits no accepted source revision.

The surviving final lifecycle cohort passed **42/42 attempts**, covering every one of the 19 frozen failure methods. This review independently reread all 42 result envelopes and checked code, phase, exact expected span, contract blocked levels, unsuccessful/uncommitted status, and absence of successful blocked levels. The cohort covers the five runtime source negatives as well as cancellation, budget exhaustion, malformed native output, forbidden X/time changes and publication rollback.

The cancellation receipt records 521.803 ms from request to API return, below the 2,000 ms cap, with the spawned descendant reaped. The running-worker deadline case also records descendant termination. Invalid edits, exhausted/cancelled attempts, rejected native results and publication failures preserve the prior accepted pointer and artifact bytes. An unreferenced candidate directory remains failure evidence where permitted by the contract.

The archived final supplemental cohorts also pass: 7 admission checks, 5 lexical-resource checks, 13 native-artifact checks, 26 output-alias checks and 4 receipt-delivery checks. These supplements retain their declared post-inspection provenance and do not replace the original frozen acceptance set. Earlier failed attempts remain in the archives.

## Receiving applications

The receiving records are bound to the exact replayed artifact hashes. Khronos validation reports zero errors and zero warnings for **eight raw/final paths representing seven distinct GLB hashes**. D's raw and final GLBs are identical. Three informational findings identify retained unused rotation samplers in the enabled-case finals. The historical receipt field named `khronosUniqueFiles` retains its original value; this review states the precise path and hash counts separately.

Three.js r186 loaded eight clips and checked 24 poses. Pinned Blender 4.5.3 imported the four actual final GLBs and produced twelve measured renders at time zero, reference contact time and two seconds. Every image hash and final-GLB link matches its receipt. The largest imported-bounds error is 0.0000261 mm. This review also inspected the published twelve-panel comparison: A–C stop at their left stops, D visibly passes through, and the right lane continues in every case.

The receiving evidence covers recorded playback. It makes no browser/GPU capture claim and no live collision-physics claim for the GLB.

## Integration and remaining gates

This assigned-scope acceptance supports review of the isolated development increment under OK-ENG-009. The coordinator reports that both baseline `ec5c1fd` and candidate `2c14028` reproduce the original 30,000 ms .22 setup timeout. The full local driver is **FAILED**; **4,239 methods passed; 13 test methods NOT RUN**. This review does not relabel that outcome as a full driver pass or close the old-profile release.

The coordinator owns the integration decision and must verify the actual published main result. General contact, a production backend, the unexecuted compatibility/release roles, live destination physics, comparative authoring benefit and full OntoKin completion remain outside this finite qualification.

## Outgoing delivery and portable replay

Use the following directories relative to the extracted formal root `evidence/r2/reviewer/formal-de813a65`:

| Case | Artifact directory |
| --- | --- |
| A | `A-1/store/artifacts/f88d4343a88a404ca7fef40a4d61c309` |
| B | `B-1/store/artifacts/5af4b7f659b84da5a359bea233cb5341` |
| C | `C-1/store/artifacts/30671c2d1f68461e89a78c78bb34f119` |
| D | `D-1/store/artifacts/d499b75a0f35477497831c5b1b21c62e` |

Each contains editable `source.ok`, `canonical-input.json`, `scene.blend`, `raw.glb`, `final.glb`, native traces, settings and its manifest. The corresponding independent reopened traces are in each case's `reopen/` directory. `DELIVERY-MAP.json` gives absolute paths, exact sizes, hashes and accepted revisions.

Run from any directory, supplying a new result path:

```sh
python -B <repo>/docs/engineering/guided-contact-c191/independent/supplements/recovery-r2-review/replay_evidence.py \
  --formal <archive-root>/evidence/r2/reviewer/formal-de813a65 \
  --contract <repo>/docs/language-design/guided-contact-v0.1 \
  --out <new-output-path>
```

The replay needs the recorded Python/NumPy environment and the unchanged checker/contract files. It verifies frozen identities, artifact manifests, nine final playbacks, native-to-final mappings, saved-scene trace equality, repeated-build identities, renamed/reordered identity, causal-control invariants and regenerated analytic controls. It does not launch Blender or substitute for the retained native execution receipts.
