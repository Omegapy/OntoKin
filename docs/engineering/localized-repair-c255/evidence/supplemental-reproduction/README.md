# Supplemental reproduction of the two C255 raw-angle faults

This is a **fresh reproduction** on preserved old author commit
`2eb3f6f7c263dbb5f215ad87bc93a03010d789aa`. It is not the overwritten original
probe output and does not relabel the reconstructed original record as raw
historical evidence.

The current unchanged targeted probe and its two unchanged independent helper
sources were copied into a new, previously nonexistent output directory. A
minimal temporary input tree was built from exact `git show` bytes at the old
commit. Its 22 frozen input bindings match the independent review's original
source hashes. Only the two requested probes ran.

Both old-source observations freshly returned `componentPass: true` despite
raw rotation exceeding the original angular bound. The same probe values in
the previously saved corrected evidence return `componentPass: false` with
`RAW_ROTATION`. Corrected source was not rerun. The current repository's head
and working status were identical before and after this reproduction.

| Bound source | SHA-256 |
| --- | --- |
| Old oracle | `8c2c6c75adfc2d61537c060ea03d87ada6f7b85940ccaf44b6b5d5b84ced7fd3` |
| Corrected approved oracle | `b7275bd40bd429397ce6db5608bc025493a5e92cfc378f70e05cc799f50ff593` |

The fresh result is
`fresh-old-run/unchanged-probe/targeted-gap-8c2c6c75adfc.json`.
The full command, interpreter/platform, input/source hashes, unchanged copied
probe hashes, prior corrected-evidence hash and comparison are recorded in
`fresh-old-run/REPRODUCTION.json`. Standard output and standard error are saved
separately. The exact old oracle bytes are retained in `fresh-old-run/old-oracle.py`.

The temporary minimal tree has been removed. Its exact frozen source inputs
remain available at the recorded commit in the restored repository; the
reproduction script reconstructs them without network access or a mutable
branch checkout. To repeat, choose a new output directory:

```sh
python3 reproduce_old_faults.py \
  --repo /absolute/restored-OntoKin \
  --review-dir /absolute/package/evidence/c255/independent-review \
  --output-dir /absolute/new-supplemental-output
```

No existing independent-review evidence or current repository file was changed.
The approval of the corrected exact files remains unchanged. This supplement
closes the recoverability gap by preserving a fresh exact-source reproduction,
while keeping the original-output limitation visible.
