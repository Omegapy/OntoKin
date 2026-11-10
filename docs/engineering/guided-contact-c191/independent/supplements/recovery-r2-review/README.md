# Independent C191-R2 recovery review

This review resumes published C191 head
`dc782500d74a8b269c3471121345d6c8566508eb`. It preserves the adopted contract,
the C191-A1 admission clarification, and every existing frozen fixture. Missing
earlier execution artifacts are not treated as recovered results.

## Published freeze and scope

[The freeze review](freeze-review.json) verifies all 6 semantic, 16 checker,
62 source-freeze and 11 adopted-contract entries before this reviewer inspected
C191 output. The 12 inherited C190 hashes also match the extracted handoff.
Published ancestry places the physical/checker freeze at `23069a5`, the exact
contract/source freeze at `a1cde0a`, the first validator at `61d14d3` and native
implementation at `270d658`. This proves published ordering and preservation;
it does not independently observe the earlier reviewer's private work.

The frozen expectations match the C190 proposal: stops at 380, 355 and 367.5 mm
imply ideal contact at 1.6, 1.4 and 1.5 s and left travel of 200, 175 and
187.5 mm. Disabling the left shoe collider requires 250 mm of travel and a
signed final gap of -50 mm. Every case retains 300 mm of right travel and
15 mm right clearance.

The final GLB must certify every one of its 480 interpolation intervals:
positive-case near-face penetration is at most 0.5 mm, and all twenty unrelated
visible-part pairs remain nonoverlapping under the fixed 0.001 mm numerical
contact allowance. The 0.5 mm/s residual-speed gate starts 25 ms after ideal
contact; the 0.1 mm rebound gate starts at ideal contact itself. Raw rotational
guide residuals have their separate native-sample and continuous raw-to-final
vertex mapping bound of 0.2 mm. Neither that bound nor the final playback
certificate covers unrecorded Bullet substeps or directly measured impulses.

## Initial recovered-code checks

At `dc782500`, the original source conformance runner passed 32 cases; admission
checks passed 7; lexical/resource checks passed 5. The analytic playback checker
passed its 8 positive, 54 negative and 3 continuous slab controls. These fresh
records are C191-R2 verification, separate from missing earlier outputs.

Source review found two unenforced delivery requirements. A native result could
report a carriage as `EMPTY` or a constraint as `MESH`, despite the declared
construction. It could also commit without a usable editable `scene.blend`.
The author reproduced these gaps with an audit-only A native build.

[The supplemental runner](run_native_artifact_edges.py) independently exercises
both concerns through the real API and supervisor. It copies an identified
native result into each isolated transaction, then changes one object type or
removes, empties or replaces the saved-scene bytes. The unmodified copy is its
positive control. Exact diagnostics, source spans, blocked levels, process
reaping, accepted-pointer behavior and preservation of previous artifact bytes
are checked. These are transaction probes, not fresh native solves.

The independent baseline run reproduced all five incorrect commits; the
positive copying control passed. The failed attempts remain identified under
`native-artifact-edges-dc782500` in the C191-R2 verification evidence. These
supplemental cases were written after recovered source inspection. They do not
claim to be part of the original pre-candidate freeze, change an acceptance
limit, or replace any earlier fixture.

The first correction rejected those five malformed candidates, but its header
check alone still admitted six incomplete or trailing Blender block envelopes.
Those failed probes are retained under `native-artifact-edges-header-repair`.
The completed correction scans the bounded uncompressed file through its final
`ENDB` block. Complete file structure is still distinct from scene semantics;
the independent native reopens establish the latter for the delivered files.

Review also found that an optional result destination could overwrite the
accepted state, an earlier artifact or the input source. The read-only validator
had an equivalent alias problem between input, canonical and result paths.
[Independent alias probes](run_output_aliases.py) reproduced 23 failures in 26
cases before correction. Their records remain under `output-aliases-de0e5d98`.
The correction checks direct, resolved and source-file aliases, keeps original
source rejections, and writes legal external outputs by atomic replacement.
A late unsafe receipt path cannot change an already committed outcome.

## Completed independent qualification

[The qualification receipt](qualification-review.json) identifies every final
report, hash, failed predecessor and observed measurement. The tested clean
reviewer revision is `de813a652ab5380a9c96f2a72ad9bd9ce5bbb96e`; its entire
prototype tree matches author commit
`0ef332d61812d8b48072a559574ffda58305f6f9`. All original frozen inputs remain
unchanged.

| Check | Observed result |
| --- | --- |
| Source conformance | 32 of 32 pass |
| Admission and lexical/resource boundaries | 7 of 7 and 5 of 5 pass |
| Saved-artifact edge cases | 13 of 13 pass |
| Output aliases and safe external controls | 26 of 26 pass |
| Fresh source builds | Nine pass: two each for A–D and one rename/reorder control |
| Fresh saved-scene replays | Nine pass; all 481 native records equal their original capture |
| Native/source/frame/raw-pose supplemental audit | Nine of nine pass |
| Complete lifecycle suite | 42 of 42 pass, covering all 19 frozen failure methods |
| Auxiliary receipt failure probes | Four of four pass |
| Analytic playback controls | Eight positive, 54 negative and three continuous slab controls pass; sealed control bytes reproduced |
| Portable evidence audit | Passes in place and from a physically relocated directory; original summaries unchanged |

Repeated canonical inputs, raw/final GLBs and native trace bytes are identical
for all four formal cases. The renamed/reordered source has a different source
revision but the same canonical input and final GLB as A. The disabled collider
control preserves every recorded base, stop and right-lane pose while changing
left travel from contact at approximately 200 mm to pass-through at 250 mm.
No `.blend` byte identity is required or claimed.

| Case | Left travel at 2 s, mm | Final signed left gap, mm | Maximum final-playback near-face penetration, mm |
| --- | ---: | ---: | ---: |
| A, stop at 380 mm | 200.000018 | -0.000007 | 0.011957 |
| B, stop at 355 mm | 175.000012 | -0.000007 | 0.011957 |
| C, stop at 367.5 mm | 187.500000 | -0.000007 | 0.007591 |
| D, left shoe collider disabled | 250.000000 | -49.999989 | Expected pass-through |

The right lane travels 300.000012 mm and retains 14.999983 mm clearance in every
case. Each final GLB certifies all twenty unrelated pairs across all 480
interpolation intervals. Maximum positive-case rebound is 0.011951 mm; sampled
finite-difference speed is zero from each ideal contact time plus 25 ms through
2 s. Contact-band entry is approximately 4 ms before each analytic contact time,
as expected for the frozen 0.5 mm band at 125 mm/s. These are derived geometric
and finite-difference observations, not direct Bullet collision-event records.

The maximum continuous raw-to-final vertex mapping bound is 0.085188226 mm and
the maximum native-sample-to-final bound is 0.081302036 mm. Both remain below
0.2 mm, with every native carriage X value and timestamp preserved. Measured
cancellation request to API return is 521.803 ms, below the 2,000 ms limit;
the native process and descendant were reaped. The largest formal attempt used
450,690 counted operations and 2,223.243 ms against its explicitly authorized
1,000,000-operation and 80,000 ms limits. These elapsed values describe this
environment, not a general performance guarantee.

## Portable evidence replay

The [offline replay script](replay_evidence.py) uses the existing frozen
checkers. It resolves each local artifact directory from the archived store's
relative state pointer, verifies its complete manifest, remeasures final
playback and raw/native mapping, checks all native reopen records and repeats,
and regenerates the analytic controls. The recovered-batch checker receives a
temporary relocated summary and directory view. The original absolute-path
summary remains immutable.

From the packaged handoff root, with CPython 3.12.14 and NumPy 2.3.5:

```sh
python3 -B independent/supplements/recovery-r2-review/replay_evidence.py \
  --formal evidence/r2/reviewer/formal-de813a65 \
  --contract contract \
  --out /absolute/new/replay-result.json
```

Offline replay inspects existing evidence; it is not another native solve.
Fresh native reconstruction uses `checker/run_formal_batch.py` against the
restored repository and pinned Blender executable, with a new output directory.
Khronos/Three.js readback, visual inspection, original-profile compatibility and
integration are separate coordinator gates against the same final hashes.
A passing finite adapter does not establish a production backend, general
contact, comparative authoring benefit or the full project goal.
