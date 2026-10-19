---
project: OntoKin
document_id: OK-ENG-006
title: Local Validation and Hosted CI Policy
version: 0.1
date: 2026-10-19
status: adopted-operational-policy
document_type: engineering-validation-policy
authority: project-owner-direction-2026-10-19
---

# OK-ENG-006: Local validation and hosted CI

## 1. Decision and scope

On October 19, 2026, the project owner directed OntoKin to avoid paid GitHub Actions execution and use a suitable local alternative. **Fresh, relevant, identified local checks are the normal requirement for routine branch integration.** Hosted continuous integration (CI), which runs checks on GitHub's machines, is optional. Direct Python and Node execution on a development machine does not consume Actions minutes.

This changes the execution location and integration procedure. All language semantics, predetermined expectations, numerical limits, source identities, independent verification requirements and the full [GOAL](../../GOAL.md) remain in force. A milestone with unfinished release requirements remains unfinished after its implementation is integrated.

The policy applies to current operational references to mandatory CI in GOAL and [AGENTS](../../AGENTS.md), including routine integration of the next Agent/force work. It does not convert a failed, blocked, skipped or unexecuted GitHub job into a passing result. Account budgets, payment settings, repository visibility and historical evidence are unchanged by this decision.

## 2. Required checks and the meaning of a result

Choose checks from the actual changed scope and the active engineering contract. The local runner provides a repeatable starting point; it does not decide release acceptance.

| Change or claim | Required evidence |
| --- | --- |
| Documentation or navigation | Preservation checker and current link checks. |
| Runtime, parser, semantics or source evaluation | Complete relevant regression suite, original source conformance and affected profile cases. |
| Agent operations or schemas | Actual protocol scenarios, including failure, repair, retry, cancellation and revision isolation; schema checks where required by the active contract. |
| Exporter, geometry or viewer | Fresh source-built artifacts, independent format/geometry/motion checks and review of the required captures. |
| Full supported Python compatibility | Separate identified execution on Python 3.11, 3.12 and 3.13. One interpreter establishes evidence only for that version. |
| A complete named release | Every required role and fixture, plus the versioned evidence audit described in section 5. |

Keep execution status separate from release status. Some conformance runners successfully execute their tests while reporting **pending external evidence**. Options such as `--allow-pending` change process handling; they do not pass those pending gates. A generated screenshot still needs actual visual review tied to its artifact identity.

## 3. Run checks locally

Run these commands from the repository root using an installed Python 3.11, 3.12 or 3.13. Ordinary reference execution uses the Python standard library. The runner does not install dependencies, start GitHub jobs, publish results or change billing settings.

List the planned checks without executing them:

```bash
python3 tools/check_local.py --list
```

Run the routine Python and documentation checks:

```bash
python3 tools/check_local.py
```

The [runner](../../tools/check_local.py) records commands, outcomes and evidence in its reported output directory. Read individual reports as well as its overall result. Preserve failures and pending gates in the branch handoff; do not describe a successful preflight as a completed release.

An isolated Python environment is optional. It can be kept outside the repository:

```bash
python3 -m venv /tmp/ontokin-validation-venv
source /tmp/ontokin-validation-venv/bin/activate
python3 tools/check_local.py
```

### Independent geometry and browser checks

Use Node.js 22 with npm for the existing verifier toolchain. The committed [package file](../../tools/package.json) and [lockfile](../../tools/package-lock.json) pin these verification dependencies:

| Dependency | Pinned version |
| --- | --- |
| esbuild | 0.25.10 |
| gltf-validator | 2.0.0-dev.3.10 |
| Playwright | 1.56.1 |
| Three.js | 0.180.0 |

Install them explicitly when preparing the machine, then install Playwright's matching Chromium headless shell. These preparation steps use the network. They are not performed automatically by the checker.

```bash
npm ci --prefix tools --ignore-scripts
node tools/node_modules/playwright/cli.js install chromium --only-shell
```

The browser command works with the macOS preparation path; Linux system-library setup, if needed, is a separate environment step. Do not add the Linux `--with-deps` option to routine macOS instructions.

Run the additional source/export and automated browser checks:

```bash
python3 tools/check_local.py --full
```

Use fresh output locations. Do not regenerate committed demonstrations or replace archived release evidence merely to run a check. Record actual Node, Python, browser and operating-system versions. Missing verification dependencies or unreviewed captures remain explicit limitations. `--full` does not run every Python version or certify every release requirement.

## 4. Evidence and routine integration

Before integration, retain a reviewable record containing:

- The actual source commit/tree, changed scope and dirty-state disclosure. For an extracted snapshot, retain a verified file manifest binding its bytes to the observed remote revision; never invent a local Git identity. Unbound execution is preflight evidence only.
- The runtime digest, relevant fixture/source inventories, tool versions, settings and selected checks.
- Actual commands, executed test identities/results, logs and report/artifact hashes, including failures and unexecuted roles.
- For delivery work, matching source/program/GLB identities and the independent numerical and visual observations required by that scope.
- The relevant GitHub job state, if any, labeled as hosted execution rather than reused as evidence for changed bytes.

Retain durable evidence in GitHub through an identified repository record or another durable linked result; a temporary local path is not a completed handoff. Keep source and verification inputs stable during execution. Reconcile any change before attributing results to a later revision.

Follow the integration lease and conditional-update rules in AGENTS. Review the actual branch and current main, resolve conflicts, and validate the resulting integration. Local success supports only the checked scope and environments. Pending GLB/0.5, force-release or other requirements remain visible in [STATUS](../../STATUS.md). This policy alone does not authorize claiming PR #14 or any release validated.

## 5. Existing release contracts and future evidence audits

The original CI wording remains visible in OK-LANG-002 CON-015 and its release report, OK-LANG-003 surface closure, OK-LANG-004 I12, and OK-LANG-005 F12. This policy replaces mandatory hosted execution for **routine integration**. It preserves all their regression, source/Agent, independent destination, visual and compatibility roles.

[OK-ENG-004](OK-ENG-004-native-surface-release-conformance.md) and [OK-ENG-005](OK-ENG-005-source-impulse-release-conformance.md) define release audits whose existing evidence schemas explicitly expect GitHub CI records. **Before accepting local results through a future complete release audit, adopt and implement a separately versioned evidence contract that accepts identified execution providers.** Preserve the old schemas, old reports and their original interpretation. Do not fabricate run/job IDs, relabel a local result as GitHub CI, remove required roles, weaken assertions or rewrite preservation hashes.

The new evidence contract must still verify exact implementation and input identities, complete required execution, Python 3.11/3.12/3.13 coverage where claimed, and independent destination/visual evidence. The local runner is an execution tool, not that contract or a certification. Historical successful releases remain tied to their recorded revisions; historical blocked jobs remain unexecuted.

## 6. Hosted workflows and cost controls

Repository workflow definitions are retained for deliberate manual use. They must use only `workflow_dispatch`, a boolean `enable_hosted_ci` input with default `false`, and a job-level guard requiring `inputs.enable_hosted_ci == true`. Every hosted job must have that guard. Ordinary pushes and pull requests against these updated definitions do not request hosted execution; leaving the manual input false schedules no guarded runner job.

These controls apply to revisions containing the changed definitions. **Existing branches can retain older automatic workflows until synchronized.** Creating a branch or committing this policy does not disable other branch definitions or change repository-wide Actions permissions. Manual opt-in remains capable of consuming allowance or incurring charges; it is not the normal validation path. GitHub documents the [manual workflow mechanism][manual].

For a settings-level stop covering the entire repository, an administrator can use **Settings → Actions → General → Actions permissions → Disable actions**, then save. GitHub states that no workflows run when Actions is disabled for a repository. **That repository-wide setting was not changed by this policy's adoption.** See [repository Actions settings][settings]. Individual workflows can also be [disabled reversibly][disable] without deleting their YAML.

The no-payment direction remains in effect. Do not increase an Actions budget or enable paid execution as an automatic response to a blocked check. A budget is a spending stop only when its blocking option is enabled; alerts alone do not stop usage. GitHub's [budget documentation][budgets] explains that distinction. Direct local execution avoids hosted-runner usage; it does not remove previously accrued artifact/storage charges. GitHub documents allowances, public/private repository differences and separate storage accounting in [Actions billing][billing]. This policy makes no new claim about the owner's account balance or exact failure cause.

## 7. Source and decision record

Official GitHub documentation checked October 19, 2026. Provider pricing and settings can change; verify them again before deliberately enabling hosted execution. The owner direction authorizes this local-validation policy, not a purchase or a visibility change.

[billing]: https://docs.github.com/en/billing/concepts/product-billing/github-actions
[budgets]: https://docs.github.com/en/billing/how-tos/set-up-budgets
[manual]: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
[disable]: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows
[settings]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
