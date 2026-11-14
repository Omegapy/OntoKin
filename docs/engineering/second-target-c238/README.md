# C238: combined observation envelope admission

C238 checks whether one finite set of observation files describes a consistent declared source mapping for the original 18-part fixture. Its six members contain geometry, materials, normals, poses, semantics and the declared corner map used by the normal observations. The checker reads actual bytes and compares exact lengths and SHA-256 digests across their bindings.

A result of `PASS_CPU_ENVELOPE_ADMISSION` means that the declared set satisfies the [C238 contract](CONTRACT.md). Every C222/C234/C235/C236/C237 component outcome remains `NOT_RUN`. Numerical accuracy, semantic equality, original-source retention and native provenance require their own evidence.

## Read and run

- [Predeclared contract](CONTRACT.md): schemas, inventories, source identities, dependency rules, safe reads and report meaning.
- [Results](RESULTS.md): exact source, executed checks and known limits.
- [Independent review](REVIEW.md): independent fixtures, complete report inspection and compatibility corrections.
- [Next bounded step](NEXT-TASK.md): combined execution of the existing CPU component checks.

From the restored repository, provide the extracted handoff as source authority and a directory containing one envelope and its six members:

```bash
python3 -IB tools/second_target_c238/check_envelope.py \
  --package-root /absolute/extracted-handoff \
  --envelope /absolute/observations/envelope.json
```

The CLI writes one JSON report to standard output. Exit 0 means admitted; exit 1 means a structured refusal; exit 2 means invalid command syntax. The API is `check_envelope(package_root, envelope_path)`. Each public call freshly runs C221 authority admission. No report-file write or component-validator execution occurs through this API.

The implementation uses Python's standard library and unchanged C221 authority code. The recorded checks use Linux x86-64 with CPython 3.12.14; they do not establish another operating system or interpreter.
