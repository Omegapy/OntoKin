# C266 dependency admission supplement

**Result: all five targeted experiments passed.** The inspected C266 implementation remained SHA-256 `68849dbe3339c158eac7ec43fb1defcbd2993c37c6a0a5ee813d2da71fb03dda` throughout. Each experiment created an isolated temporary copy, imported the candidate, called its public API successfully for 18 objects, changed a dependency, then called the same loaded API again. No real checkout file was changed.

| Experiment after successful call | Second call |
| --- | --- |
| C265 source observer: final newline replaced with a space, unchanged byte count | Typed `INPUT_BINDING` refusal |
| C261 raw reader: same-size byte mutation | Typed `INPUT_BINDING` refusal |
| C257 identity utility: same-size byte mutation | Typed `INPUT_BINDING` refusal |
| C261 raw reader removed from isolated copy | Typed `INPUT_BINDING` refusal |
| C257 replaced by a symlink to an identical-byte sibling in the isolated copy | Typed `INPUT_BINDING` refusal |

Every refusal retained the exact supplied source hashes and artifact hash. Thus a previous successful call and populated module cache did not bypass the next call's dependency checks. The symlink case verifies path admission independently of byte equality. These are five two-call experiments, not five newly qualified language cases.

The structured `RESULTS.json` records original and modified identities, byte counts, refusal details and the CPython 3.12.14/Linux environment. `original-code` retains the four exact implementation/dependency files. Three modified dependency files, all per-case receipts and the exact before source/GLB bytes are retained. Temporary executable copies were removed after each experiment. The original independent review evidence ZIP remains unchanged.

## Exact command

```sh
python3 -B /workspace/scratch/2593880e88fd/independent-review/review_dependency_pins.py --repo /workspace/scratch/2593880e88fd/OntoKin --output /workspace/scratch/2593880e88fd/independent-review/dependency-supplement
```

Use a new output directory to reproduce. The accompanying script checks pinned original source identities before import and proves the real checkout files still equal their pre-experiment bytes afterward. This supplement closes only the identified dependency reload/cache risk. No further optional tests were run.
