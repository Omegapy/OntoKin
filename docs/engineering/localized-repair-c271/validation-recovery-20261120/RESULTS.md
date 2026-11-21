# C271 P03 validation recovery result

The isolated-workspace copy defect is repaired on candidate `fea1aa6fb3712c5283dde197295b2d3cbf925d36` / tree `d4fe9aa7f2166a46d7a141ad001b13c71d43a6b6`. C271 remains **blocked and open** because the unchanged historical readback prerequisite refuses the available Node binary. The complete routine driver was not rerun without qualified inputs. Its P02 failures remain preserved and unwaived.

## Verified change

The driver now copies `.agents`, `CHATGPT-START-HERE.md` and `ROLE.md` through its existing isolation mechanism. The new regression test first failed on the original driver with exactly the five omitted paths, then passed after the minimal correction. No existing test was changed. All 31 local-driver methods passed, with no failures, errors or skips. A fresh clean-candidate run reproduced that result.

The actual driver workspace builder then copied the complete source and retained its commit/tree with an independent Git index. All five targets matched their source bytes. The driver's exact isolated documentation command passed. Workflow structure and native-reader setup checks passed. Source bytes and Git state stayed unchanged. These are focused checks, not a complete routine-driver pass.

## Prerequisite outcome

All seven Python verification packages installed in a clean external virtual environment using the unchanged hash-locked requirements. The current Node build is v24.22.3. The official v24.22.1 download also differs from the historical binary's pinned bytes. The unchanged C225 no-apply preflight returned exit 1 with a runtime binding refusal; it installed nothing and executed no Node/native/product test.

The required historical Node SHA-256 is `61ab14cd750fc24d5db53490ec5fc40f756e4b6e136b78cf7004265471d9bd1d`, 126,939,688 bytes. The official same-version download is `e32e2d16081cf644f88392934288086e7662529d0d43277c34f7aad2207cfafb`, 126,879,696 bytes. Version equality does not establish byte identity. A bounded search of C262's 16,422 physical members and 246 selected JSON manifests identified no directly retained matching binary. This does not prove global unavailability. No runtime mount or shared-runtime replacement occurred.

Historical complete aggregate timings support a proposed 3,600-second outer command cap once preparation succeeds. No timeout default, required tests, dependency pins, frozen expectations or 100,000-operation/30,000-ms per-source limits changed.

## Phase boundary

R01/R02 remain done; R03–R05 remain not_done. P01 remains done and P02 remains in_progress. PR274 stays draft/unmerged, issue273 stays open, and the branch is retained. No main lease or integration occurred. Independent review must keep R03 unaccepted. This phase finishes only with a verified saved partial ZIP, matching prompts and separate receipt.

First remaining action: In a fresh bounded C271 validation-preparation phase, obtain the authenticated historical Node build with SHA-256 61ab14cd750fc24d5db53490ec5fc40f756e4b6e136b78cf7004265471d9bd1d (126939688 bytes) and establish unchanged C225 runtime/path/alias checks. If those bytes cannot be recovered, define a separately reviewed current-host qualification approach while preserving all frozen historical records and expectations. Only after prerequisites pass, run the complete required routine driver with a justified 3600-second per-command timeout and obtain independent R03 acceptance. Retain per-source limits and every required test; no blind rerun or pin replacement.

## Independent acceptance

Independent reviewer `/root/intake_review` approved the narrow repair for retained partial delivery and found no mandatory code issue. Its [acceptance record](FINAL-ACCEPTANCE.json) keeps R03 unaccepted, integration unapproved and the parent open. Seventy-three evidence predicates and 18 working-record predicates passed; these counts are inspections, not product tests. The original review, prior checker error/correction and complete source bindings remain in the raw evidence archive.
