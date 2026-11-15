# C240: GitGuardian source-identity false positive

**Date:** November 14, 2026, America/Denver.  
**Scope:** [#213](https://github.com/Omegapy/OntoKin/issues/213), security follow-up to [PR #212](https://github.com/Omegapy/OntoKin/pull/212).

## Finding

**Incident 40091648 is a confirmed false positive for the reported line.** GitGuardian flagged a Git commit identifier in the C239 source-equivalence record. A commit identifier is a digest of a Git object; it is not a service credential.

The original [bot comment](https://github.com/Omegapy/OntoKin/pull/212#issuecomment-6882759299) identifies line 4 of `docs/engineering/second-target-c239/evidence/SOURCE-EQUIVALENCE.json` in publication commit `676eecee857d5212d86340122f81b06f4c6791b1`. The field name is `author_final_execution_commit`. Its value identifies the separately retained execution commit `0d850f836e3f9ab4fe1f832b9e75db57501d49df`.

This conclusion applies to the reported value. It is not a whole-repository secret audit.

## Reproducible evidence

The actual Git object has type `commit` and a 259-byte payload. Recomputing SHA-1 over the Git object header (`commit 259`, followed by one zero byte) and the exact payload reproduces the flagged identifier. Its tree is `85734862971c4cff80f8ac8717d738a5f1604dd2`, also used by published scientific commit `d53e2f37101f7b989ee8a1be7130a5608bcadf9d`. The execution and publication commits remain distinct identities.

The original evidence file has SHA-256 `abccc3f6ce0e85cd76782069a1a68f44dcd02ab362633810e5dde5dd41b969d5`. It was byte-identical at the flagged publication and observed main `7dbc3300389820164cf7917e7299962df415962f`.

[Verification record](evidence/VERIFICATION.json) preserves the exact incident, source and observed external state. [The reproduction script](verify_git_object.py) performs seven read-only checks. Run it against the restored handoff repository, which retains the unpublished execution object:

```bash
python3 docs/engineering/security-triage-c240/verify_git_object.py /absolute/path/to/restored/OntoKin
```

An ordinary GitHub-only clone may omit that unpublished commit object. A missing object is a missing prerequisite; it must not be reported as a successful reproduction. The handoff source bundles preserve the object and its ancestry.

## Detector context

GitGuardian's [Generic High Entropy Secret documentation](https://docs.gitguardian.com/secrets-detection/secrets-detection-engine/detectors/generics/generic_high_entropy_secret) describes a heuristic that looks for high-entropy strings assigned to names containing terms such as `auth`. The field's `author` prefix contains that substring. This is a plausible explanation for the alert, inferred from the documented heuristic; the service's complete internal decision trace was not available.

Future evidence fields should use precise source-identity names such as `executed_commit` or `source_revision`. The pinned C239 JSON remains unchanged. No detector exclusion, scanner bypass, credential rotation or Git history rewrite is part of this follow-up.

## External disposition

At inspection, the bot comment still reported **Triggered**, and GitGuardian check run `132555866039` on PR #212's published head had conclusion **failure**. The public finding is explained by the proof above. **Dashboard disposition remains pending** because the available tools cannot change GitGuardian incidents.

An authorized GitGuardian user can open [incident 40091648](https://dashboard.gitguardian.com/workspace/489346/incidents/40091648?occurrence=312696087) and choose the targeted false-positive disposition. Depending on workspace settings, GitHub's check interface may offer **Skip: false positive**. [GitGuardian's GitHub workflow documentation](https://docs.gitguardian.com/internal-monitoring/prevent/detect-secrets-in-real-time-in-github) describes these options and optional PR-comment synchronization. A PR explanation alone does not establish that either the incident or the old failed check changed. Record the service's actual readback when that action is completed.

## Development boundary and next action

C239's combined CPU checker is already integrated. Its delivered handoff was independently reconciled through [scope #211's final receipt](https://github.com/Omegapy/OntoKin/issues/211#issuecomment-6883248963). C240 adds this security record and reproduction only. It does not change the runtime, existing numerical limits, frozen evidence, held branches or the meaning of any acceptance gate.

After the verified C240 handoff is saved, stop. The next development task remains the [C239 native capture protocol preflight](../second-target-c239/NEXT-TASK.md), with no native start. Reconcile any concurrent scope before claiming files or integration ownership. The original strict Blender normal failure and full R07 acceptance remain unresolved.
