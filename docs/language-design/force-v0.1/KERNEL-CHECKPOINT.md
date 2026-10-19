# Force source-evaluator checkpoint

The source `0.5` / `force-0.1` parser, typed compiler and bounded analytical evaluator are **implemented** at `cd5a6f2131b1fe2c760ab851a11c2c5b3cf119b1`, tree `a92aac948bbb6e80e7adaa136d8a6098f0f17563`. The implementation-status field in the original adoption specification describes its pre-implementation publication; this record supplies the subsequent measured checkpoint. Explicit Agent/0.5, GLB/0.5 and the complete F01–F12 release remain **unfinished**. This is not a full-product completion claim.

## Contract and actual source checks

[ADOPTION.md](ADOPTION.md) fixed the source semantics before implementation at `676e5542c09b8af1cbc9e5f0b5bbb42a898b1e34`. The original 44-case [acceptance corpus](acceptance.json) remains byte-identical at SHA-256 `de423575e648ea9e14d8de8d5bb9b2bbe6330ae6fb01e182e34c3cb6df9d2ba2`. [Twelve supplemental cases](reviewed-acceptance.json) have SHA-256 `2311dc26425cd3257df33e71e3246e2b6e14bba887da55bddc4b26915492c420`.

[Source errata](source-errata.json), published separately at `26307378dd99b298bfa230bd13660dbe36eb1c1f`, retain all original files. S10/S11 use separately named corrected source files with the inherited required initializer braces. Their predetermined import-edge outcomes did not change. P09's before-zero velocity and angular velocity are explicitly corrected to zero, as independently confirmed by executing the unchanged source-0.4 projection before its authored start actions. After-zero/later expected values and all tolerances remain unchanged. All **56 effective source cases** now execute, including the specified success, numerical, type, frame, support and rollback outcomes.

## Executed verification

| Check | Local execution | Separate GitHub execution |
| --- | --- | --- |
| Complete regression suite | 677/677, 193.790 seconds | 677/677, 160.218 seconds |
| Focused source/evaluator/review suite | 89/89, 2.124 seconds | 89/89, 1.716 seconds |
| Original source conformance | 43 cases / 694 assertions passed | 43 cases / 694 assertions passed |
| Documentation preservation | 29 sources / 233 sections / 663 links passed | Same preservation checks passed |

[Publication run 39194062765](https://github.com/Omegapy/OntoKin/actions/runs/39194062765) reconstructed only the eleven reviewed source/test/specification paths from exact parent `26307378`, required the entire resulting Git tree to equal `a92aac9`, executed the checks, and published a new staging commit. The root process read back its parent/tree and advanced PR #13 with an expected-head nonforce update. No temporary publication workflow or staging payload was integrated.

The run's artifact `12161410669` contains source.bundle, its SHA256SUMS, revision.txt and the actual logs. Its ZIP digest is `e2e374d6d1e84497b27618a85335b00b80ecd63070c21664a44f85dbd81c8fb5`. The retrieved ZIP, bundle and local working tree were independently verified against those identities. Artifact retention is seven days; the identified source and executable tests remain in Git.

| Retained execution file | SHA-256 |
| --- | --- |
| focused-tests.log | `226d103cd38c1a5383f92bc529cc1ce116a193fca10b8830cd18362e937e1e30` |
| full-tests.log | `4557ad592014ab8d0146ec42ee42b13f9cd6f6b79418b1d017242382057729f1` |
| core-conformance.json | `4e5551f562e585f53809b9c94d4a04f0b9a1d8c8ef97cde961ef943523db5546` |
| documentation.json | `940e40294e65a583966d95f94652124143532fdc8b2b208ceae3faf5181ebd47` |

## Reproduction and remaining work

From the identified checkout:

```bash
PYTHONPATH=.:tests python -m unittest test_force_contract test_force_source test_force_evaluator -v
python -m unittest discover -s tests -v
python -m ontokin conformance --output /tmp/force-core-conformance.json
python docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

The source tests exercise the actual compiler and evaluator, not prepared Python geometry. Transaction tests probe cancellation at every observed boundary callback, completion and release rollback, exact endpoint ordering, nested history budgets, canonical finite aggregation and valid short-prefix behavior. The actual discovered test names preserve every earlier test identity.

Normal Python 3.11/3.12/3.13 and inherited GLB/browser CI, merge identity and resulting-main checks are recorded separately in PR #13 and STATUS. Passing inherited destination checks does not validate the still-unimplemented force delivery binding. The next work is explicit Agent/0.5 discovery/inspection/source repair and GLB/0.5 recording, followed by independent force destination/browser checks and the complete current-identity F01–F12 gate.
