# C268 focused selector-bound control update

The Director requested one additional control after the independent reviewer
found a mandatory R02 resource-bound defect: the prior reader performed pin-table
membership, and therefore string hashing, before bounding the endpoint selector.
The implementer added an exact-string length check of five or six characters
before membership. The existing `ENDPOINT` outcome remains unchanged.

The new method `test_overlong_endpoint_refuses_before_pin_lookup` replaces the
reader's pin table with a membership spy that raises if invoked. It supplies
the built-in string `before` followed by 100,000 ASCII `x` characters. Both
filesystem entry points are forbidden in the same call. The resulting typed
`ENDPOINT` refusal proves the length guard precedes pin lookup without relying
on a timing threshold. The input recipe and exact selector SHA-256 are retained
in the call ledger.

The [new run](run-04/results.json) passes **35 methods and 131 API calls**:
121 historical calls and 10 raw calls; 12 historical admissions, 9 raw successes
and 110 typed refusals. There are zero failures, errors, skips or untyped
exceptions. Code remained stable during execution.

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `endpoint_reader.py` | 14914 | `a7bb1f67398a54922e647d6d43062f89acb32c6e05a2fc653f5c30160f888157` |
| `test_endpoint_reader.py` | 52981 | `d7c426870348ab9e0976d46ee64b8624eb39c3e0b2f84a2159d2a91f66bf46c9` |
| `endpoint_control_fixtures.py` | 9181 | `b062555ea7816cb8425b1d73db949974838d6e00afe549dce91ab2b9ad22439d` |

All previous methods and expectations remain unchanged. `run-01`, `run-02`,
`run-03`, `discovery-01` and the previous author report remain intact. This
update changes only the assigned test, current coverage description and new
control evidence. No implementation or shared-state change was made by the
control author. The suite is frozen for the Director's clean candidate cohort
and the independent reviewer's follow-up.
