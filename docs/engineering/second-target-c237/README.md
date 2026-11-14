# C237: CPU semantic treatment and retained source

C237 checks the meaning reported for the original 18-part fixture and verifies that its original source and delivery files are actually retained. It compares complete declared semantic records and all 14 original feature treatments, while keeping provenance declarations separate from evidence of native behavior.

- [Predeclared contract](CONTRACT.md): finite schema, strict admission, provenance matrix and result meaning.
- [Results](RESULTS.md): exact source, author controls, failures and limits.
- [Independent review](REVIEW.md): separate oracle and complete report checks.
- [Next bounded task](NEXT-TASK.md): CPU admission of one combined observation envelope, in a separate scope.
- [Scope #207](https://github.com/Omegapy/OntoKin/issues/207) and [PR #208](https://github.com/Omegapy/OntoKin/pull/208): publication and separately confirmed handoff delivery.

Run from the repository root with the original extracted handoff and a separately supplied observation:

```bash
python3 -IB tools/second_target_c237/check_semantics.py --package-root /absolute/package --observations /absolute/semantics.json
```

The command emits one JSON report. Exit 0 means finite semantic/retention equality, 1 means measured loss in an admissible observation, and 2 means structural refusal. Actual native capture, loader mapping, action execution, live physics and source reconstruction remain unproved. Prior geometry, material, normal and pose checks remain separate.
