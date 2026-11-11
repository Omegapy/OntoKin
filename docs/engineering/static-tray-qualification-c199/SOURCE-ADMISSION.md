# C199 direct-Python source admission

This preparation decision names the direct-Python execution surface
`ontokin.static-tray.python-finite/0.1.0`. It requires independent review before
the executable closure is sealed or a native qualification slot begins. It does
not change the C198 geometric contract, accepted parameter ranges, binary64
rounding rules, canonical record schema, or the ordinary OntoKin compiler.

The direct route executes two authored files, `main.py` and `tray.py`, through a
finite Python harness. It does not promise to execute arbitrary Python programs.
The authored reusable `make_tray` function must actually run twice, once for
each delivered tray. Calls made from inside that function also count. The two
delivered records must match snapshots of those two actual function results.

## Why this decision is needed

Source tracing alone cannot interrupt a long C-level operation. For example,
`sum(range(1000000000))` can do substantial work between two Python source trace
events. The original preparation implementation also read complete candidate
files before checking their size. Both behaviors conflict with the existing
finite source budgets. C199 therefore adds guarded operations and bounded file
reads before any native execution. It adds no process allowance or retry.

## Fixed resource accounting

The direct route keeps the existing maximum of 100,000 charged source operations
and 30,000 milliseconds. The caller's earlier transaction deadline is checked
through the existing `check` callback. Every source trace event, guarded iterable
step, bounded value traversal and numeric limb charge uses that same operation
counter and callback. The report records the total and the source trace count
separately because CPython opcode notification behavior can vary between
compilations. Neither counter changes arithmetic results.

Guarded containers and iterables permit at most 4,096 elements; guarded strings
and byte values permit at most 32,768 elements. Integer and rational operands
permit at most 32,768 bits, and guarded value nesting permits at most 32 levels.
Arithmetic checks the combined operand bit allowance before an intermediate
calculation. Repeated references are charged on each traversal. Cycles are
rejected. Reusable helper results and the final record are checked before JSON
serialization, so aliasing cannot expand an unchecked value into large output.

The manifest and each source are read with a maximum of their byte cap plus one.
The source allowance remains 32,768 bytes per file and 65,536 bytes in total;
the manifest cap is 32,768 bytes. The opened object must be a regular file.
Nonblocking, no-follow opens prevent a substituted pipe or symlink from
bypassing the check. The two source units and their manifest must have distinct
opened file identities. Directory inspection stops after any fourth entry.
Exact directory membership, manifest fields and source hash binding remain
required.

## Admitted Python surface

The existing exact import rules remain: `main.py` can import only `make_tray`
from `tray`; `tray.py` can import only `Fraction` from `fractions` and `pack` from
`struct`, without aliases or relative imports. Infrastructure names and private
attribute access remain unavailable.

The following are the finite operations provided by this implementation:

| Surface | Admission |
| --- | --- |
| Numeric operations | Finite integer, float and rational `+`, `-`, `*`, `/`, `//`, `%`, unary `+` and `-`; the original Python result is retained after checks. |
| Sequences | Bounded list, tuple, string and byte concatenation; sequence repetition is rejected. |
| Logic and comparison | Boolean operations and `not`; single equality, ordering, membership and identity comparisons on bounded values. |
| Construction and conversion | Guarded `float`, `int`, `str`, `dict`, `list`, `tuple`, `len`, `range`, `enumerate` and `zip`. Enumeration and zip produce bounded materialized values. |
| Reduction and ordering | Guarded `sum`, `min`, `max`, `all`, `any`, `abs` and `sorted`; sorting uses checked comparisons and supports bounded source key functions and boolean `reverse`. |
| Rational conversion | `Fraction` with one or two bounded numeric inputs. String parsing is not admitted. |
| Binary encoding | `pack(">d", value)` with exactly one finite numeric value. Other formats are rejected. |
| Public attributes and methods | Rational `numerator`/`denominator`; byte `hex()`; list `append()`/`copy()`; dictionary `get()`/`copy()`/`items()`/`keys()`/`values()`. Method keyword arguments are rejected. |
| Iteration | Source `for` loops and comprehensions and guarded builtin consumers check each element; generator expressions are consumed through the same guard. |
| Item assignment | One ordinary list/dictionary item target is checked before and after mutation, preserving right-hand-side, object and key evaluation order. Slice writes, deletion and bulk unpacking targets are rejected. |

The following syntax is now explicitly rejected before execution, in addition
to the previously excluded dynamic imports, classes, asynchronous constructs,
yield, global/nonlocal declarations, context managers and exception handlers:

- Exponentiation, shifts and bitwise operators.
- Augmented assignment, formatted string expressions, sets and set
  comprehensions.
- Chained comparisons, attribute writes and decorators.
- Slice mutation, deletion, starred unpacking and subscript targets nested in
  multiple assignment, annotated assignment, loop targets or unpacking targets.
  Ordinary tuple unpacking into names and bounded dictionary expansion remain
  admitted, including the existing dictionary insertion-order control.

Arbitrary public methods are rejected; they are not an alternate path to
unbounded allocation. Unsupported builtin argument forms also fail. These
restrictions are a versioned C199 implementation decision, rather than a claim
that all otherwise valid Python syntax was required by C198. The frozen authored
fixtures use the admitted surface. No fixture source, canonical geometry
equation or independent reader expectation is changed by this repair.

## Evidence scope

Preparation controls cover bounded reductions, large requested allocations and
operators, restricted rational/packing/method calls, alias expansion, hidden
helper recursion, bounded file reads, hardlink aliases and the caller deadline.
The existing source suite covers all five frozen source pairs, all catalog
rotations and sign twins, parameter boundary rejection and the unchanged source
diagnostic classes. These are CPU source controls. They provide no evidence of
native export, receiving, lifecycle qualification or artifact promotion.
