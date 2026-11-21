# Independent H0 review

**Accepted result: concrete H0 blocker. No operational plan is approved.**

The independent archive checks passed for all 730 C195 members and both Node members, including unmapped history. Every member's size, SHA-256, mode and type is frozen. Archive bytes stayed unchanged during inspection. These inventories do not approve an installation target map.

## Confirmed blocker

The existing selected Python executable is `/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12`: 30,894,944 bytes, SHA-256 `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`, mode `0o755`. It matches the engineer's inert snapshot.

ELF is the executable-file format. Its dynamic string table starts at 4,191,704 and occupies 42,266 bytes, ending at 4,233,970. It crosses two loadable segments: [4,190,208, 4,194,304) and [4,194,304, 4,328,816). The accepted parser requires the whole table to fit inside one segment. Its mapping list is therefore empty.

Forty-three independent static checks passed. Existing `readelf` corroborated the address and size and exited 0. The accepted implementation's exact hash is `b2f4c869fd03919047db797bd3a80616cbe16f6b17689fe61d40754b27f97a39` at source `2c6bbfb7aa1d402ce47ffdc24adb4d89b8a81c1e`. Its mandatory Python prerequisite would reject these bytes with `CHI-UNSUPPORTED: Ambiguous/unmapped ELF string table` before helper imports, Git reads or observation.

That rejection is a source-backed inference. No product parser was invoked, and the finding does not classify the executable as corrupt or its runtime behavior as failing.

## Disposition

The engineer's first reader assertion failure and later successful raw diagnostic remain separate, preserved attempts. No preparer, installation, Node/ldd, checker, product test, alternate-interpreter work or source repair occurred. Install plans, Python metadata, remaining loader closure and an executable inspection plan remain unfinished. The evidence-only Python helpers did not establish the operational clean-launcher environment.

The Director should finish this phase's partial checkpoint and verified saved handoff. A fresh bounded review may examine finite string-table mappings across adjacent segments while preserving bounds and refusal semantics. This review does not authorize that change or H1 observation.

Detailed evidence is in `REVIEW.json` and `PYTHON-BLOCKER-VERIFICATION.json`, with raw `readelf` output, source predicates, complete archive inventories and retained engineer artifacts. The reviewer is stopped with no unresolved operation.
