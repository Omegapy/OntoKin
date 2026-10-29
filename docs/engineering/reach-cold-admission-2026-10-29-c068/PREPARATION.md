# C068 source and preparation evidence

C068 began by reading the supplied README, handoff, final state, packet interface, source index and manifest. Independent attachment review found all five nonmanifest attachments byte-identical to their canonical manifest entries; the upload filename suffixes do not change content. Fresh GitHub reads matched C067 final main and confirmed explicit [scope and packet closure](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6511093850), the unchanged archive branch, zero open PRs and zero queued/in-progress workflows.

The original `OntoKin_C067_Handoff_2026-10-29.zip` was retrieved. Its 477,512,196 bytes hash to `358435a1b1956e7b1eb4e7965d4a8c2e8030ba2a15df93ee5b8f175c410ecd2b`; it has 3,682 regular members. Its manifest hash is `949224ed1ac75cc77bf0fc1255b7d95f203e57c66d0d0a484b89aec70a716d1b`. The original standalone packet-plus-ZIP verifier passed with empty stderr. [The fresh result](preparation/c067-verification.json) records all 3,627 source files, 621,973,113 bytes, zero omissions and the actual raw commit graph/check receipts. This rechecks recorded historical checks and bytes; it does not re-execute their documentation checks or product suites.

The packet's source index hash is `291a35d1a3b9e4c51ffb35b391b6deffe2c839995d4bd3d3f609e2ecc8e86017`. Complete source was copied into a separate working directory. The original final raw commit and complete tree were restored into a local Git repository with a shallow boundary at the actual C067 commit. The result is an exact identified source checkout, not a full-history clone and not a substitute synthetic baseline commit.

## Actual preparation corrections

The first archive transfer helper call failed because network access was unavailable in the initial sandbox. The authorized retry completed successfully. No duplicate or partial delivered archive was used as evidence.

A source-inspection command ran while archive extraction was still completing and reported that the verifier file was not yet present. Extraction then completed; the expected archive and manifest hashes matched before the verifier was read and executed.

The first fresh `git add` respected ignore rules and omitted 152 already-tracked historical log files from its unborn index. Its tree was `902ca1163cba235862ca33231998be46266fa080`, not the baseline. The assertion stopped reconstruction before any baseline ref was published. The complete source files themselves were present and unchanged. Adding exactly the missing baseline-index paths with explicit force restored tree `f1bfe1c770fd1fc1c0aca5fbeabf54d4ac1f0aa5`; all baseline blobs matched and working status was clean. [The exact correction receipt](preparation/git-index-correction.json) preserves the omitted path list.

The first static derivation attempt expected a literal `self.budget.tick` spelling. The actual constructor passes its `budget.tick` parameter across a newline. Its source-string assertion failed; no product code ran. The corrected derivation uses the parsed call's `check` keyword to bind the actual `budget.tick` expression. The [original script](preparation/derivation-attempt-001/derive_evidence.py) and [failure](preparation/derivation-attempt-001/stderr.txt) remain preserved. Later successful derivations have their own exact source identity and receipts.

These preparation events are not product failures or runtime experiments. No product imports, product requests, runtime suites, native trigonometry, meshes or hosted jobs were executed.

## Historical boundary retained

C068 freshly verified the complete original **C067** packet and ZIP. C067's older account remains unchanged: its original complete C066 packet/ZIP was unavailable and was not freshly verified; its complete C066 source was recovered and verified using the then-verified C064 packet and immutable GitHub paths. The new C067 verification does not rewrite that historical availability statement.

The current packet and repository retain all earlier source and archive evidence. They do not establish independent Git LFS hydration or finish historical payload migration.
