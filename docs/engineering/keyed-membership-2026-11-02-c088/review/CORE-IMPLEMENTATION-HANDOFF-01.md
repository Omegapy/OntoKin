# C088 core implementation handoff

The six assigned core paths are ready for a fixed source checkpoint. No source
file has been staged or committed by the core implementation agent, and no
candidate/product workload has run under this ownership.

## Public native API

```python
from ontokin.keyed_membership import has_key

result = has_key(collection, query, expected_type=leaf_type,
                 node=whole_call_node, ledger=admitted_ledger)
```

`collection` is the exact native `KeyedValue` payload. `expected_type` is the
resolved leaf `Type`, not `Keyed<T>`. `result` is a native `bool`. The evaluator
owns signature checks, abstract/unknown return, generated-taint guards and the
returned `Value(BOOL, result)` wrapper. The helper requires the actual admitted
`SharedExecutionBudget` and restores its prior stage even on failure.

## Assigned source changes

- `keyed_membership.py`: exact native tuple and wrapper admission; bounded
  depth-two type descriptors; canonical stable keys; captured immutable tuple
  and expected type descriptor; full admission before query validation; key-only
  scan; exact five-stage `n+k+3` charging and publication; no payload comparison,
  collection copy, fallback authority or String-quota use.
- `construction.py`: profile-aware predefined/name lookup; ordinary eager
  builtin signature and abstract behavior; inherited generated guards and
  callback identity; .21 String-addition inheritance; correct delivery target
  on construction failure. Existing dependency/provenance flow and cache
  eligibility remain unchanged; actual membership calls cannot enter constant
  or parameter folding allowlists.
- `linker.py`: declaring-unit reservation of `has_key`, earlier-unit refusal of
  .21 imports, and explicit .21 permission to import .20 while preserving older
  .20 import refusals.
- `profile_capabilities.py`: isolated membership profile and nested inherited
  capabilities, including the new String-concat capability family.
- `syntax21.py` and `syntax02.py`: explicit .21 header/profile dispatch and
  inherited grammar with no new token, syntax node or keyword.

All six source hashes and byte counts are in
`CORE-STATIC-COMPILATION-01.json`. Each was syntax-compiled under Python 3.12.14;
the compilation process imported no product modules. Scoped `git diff --check`
was clean. Dynamic behavior is intentionally unclaimed until the root closes
and authorizes execution of a fixed candidate source cut.

The separately authorized `tests/test_keyed_membership_interfaces.py` is also
ready. Its nine tests remain unexecuted; its static receipt is
`INTERFACE-STATIC-COMPILATION-01.json`.
