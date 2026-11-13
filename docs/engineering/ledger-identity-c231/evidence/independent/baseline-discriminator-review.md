# C231 baseline discriminator observation

The independent CPU harness ran two fresh temporary-authority controls against clean source `099339f9b320a2c47a0ca2d275468c6e5f1b09e9`, tree `e940be2a1a9bb7def41d20daf06fdf9736942585`. Its ledger SHA-256 was `0b4cee3520ba7a0002ec6958b37511e4b541a9823c8a1bc955214ec132924243`. The exact harness SHA-256 was `4598edfe60c6522326176026728b360710a8bd77f3aba97a7a0c29ac1222cd63`.

For each authority file, the harness saved the original bytes and numeric device/inode identity, unlinked the path, recreated identical bytes, and patched only numeric identity observations for the recreated file to report the original pair. Real directory identities, byte checks, filesystem file-kind/link-count checks and persistence code remained active. This does not claim that the filesystem actually reused an inode in these two runs; it deterministically represents that documented failure condition.

Both original marker and journal cases returned a construction reservation and left the capability live. Those are reproduced defects, not passing product behavior. The harness's `passed: true` means the predeclared baseline-defect expectation was observed. It completed two groups and seven assertions in 0.003787 seconds under CPython 3.12.14. Product child-launch seams were blocked. Three Git subprocesses collected provenance before the product controls began.

The candidate must reject both equivalent conditions, independently report STOPPED on a subsequent mutation, and release original held descriptors. Candidate results are pending. Original test methods, consumed C229/C230 plans, historical ledgers and previous outcomes were untouched.

Evidence: `baseline-discriminator-result.json`, `baseline-discriminator.stdout`, `baseline-discriminator.stderr`, and `independent_controls.py` with the hash above.
