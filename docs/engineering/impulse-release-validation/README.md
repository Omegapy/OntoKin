# Source impulse release evidence

This record preserves the complete finite I01-I12 gate for source `0.4` / `impulse-0.1`, Agent/0.4 and recorded GLB/0.4. The [summary](validation-summary.json) and [full gate result](impulse-conformance.json) identify the tested implementation, actual source operations, inherited gates and exact CI. Integration into main is recorded separately in STATUS.md; publication alone is not a merge.

The [archive manifest](evidence-manifest.json) identifies every regular file and the [evidence archive](evidence.tar.xz). The archive retains complete accepted source snapshots, requests and responses, nine impulse GLBs, native geometry/PBR/motion reports, high-spin intermediate samples, browser harnesses, 24 individually reviewed native captures, fresh C20 browser input files and its separately reviewed capture, both executed 588-method suites, C01-C20, M01-M12 and I01-I12, and actual GitHub CI run/job payloads. Earlier source surface evidence is not modified. The visual observations were supplied after actual image inspection, not manufactured by the publishing job.

## Reproduce the retained-evidence audit

Use a new detached worktree at `da0eb32c789a6f631a0d39eb219cbb3a912c9dfa`. Verify the archive SHA-256 against the manifest before extraction. Extract at that worktree root so the archived `build/impulse-release-recovery/` and browser input paths retain their original meaning. A generated visual demo-data file is included for provenance and must not replace unrelated working changes.

```bash
git worktree add --detach /tmp/ontokin-impulse-review da0eb32c789a6f631a0d39eb219cbb3a912c9dfa
tar -xJf docs/engineering/impulse-release-validation/evidence.tar.xz -C /tmp/ontokin-impulse-review
cd /tmp/ontokin-impulse-review
python3 tools/run_impulse_conformance.py --external-evidence build/impulse-release-recovery/impulse-external.json --evidence-root . --output /tmp/ontokin-impulse-reaudit.json
```

Check all archive member lengths and hashes from the manifest. The final command executes the mapped source/operation tests and independently reads the retained source, decoded GLB and browser evidence. It does not rerun a browser or claim a new visual observation. Full external regeneration follows OK-ENG-005 and the exact pinned Node tools. The original GitHub source/visual job ran on all required Python versions and the recorded destination tools; its actual raw API records are inside the archive. The publication operator, authored reviews and selected input artifact identities are also retained there.

This finite release does not complete OntoKin. Contacts, continuous forces and torques, general dynamics, live destination physics and all other unmet GOAL domains remain open. Static captures cannot establish continuous or universal numerical accuracy. All records retain the tested profile limits.
