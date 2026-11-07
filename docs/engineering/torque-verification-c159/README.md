# C159 | A08 simulator scan eligibility

A stock simulator tick can observe how the source check retrieves and releases its dictionary helpers. Three proposed shortcuts changed the exception or the charged work on CPython 3.12.14. C159 closes these candidates. The shipped simulator and public preflight continue to use the reference implementation. The [C158 baseline](../torque-verification-c158/README.md) and [C159 measurements](measurements.json) identify the producer, source and artifact.

## What changes at the scan

Each probe runs an exact simulator and a normally constructed inherited subclass. Both produced the same differences. The tests compare the escaping exception **by object identity** and read the ledger before and after one tick. Changes to the expression run only in disposable copies of the package.

| Change tested | Reference tick | Experimental tick |
|---|---|---|
| Look up `chain` one extra time immediately before scanning keys. A colliding dictionary key returns the original binding, but raises on the fourth lookup. | Three lookups, completes, charges 1. | Four lookups, propagates the marker, charges 0. |
| Resolve the key scan’s helpers once and reuse them for the value scan. The second lookup changes `chain`. | Calls the replacement on dictionary values, propagates the marker, charges 0. | Reaches the replacement during a later sequence scan, completes, charges 1. |
| Resolve helpers afresh in each scan, storing them in local variables at their original evaluation sites. A temporary callable installs a new comparison function when released. | Releases the key callable before selecting the value comparator, propagates the marker, charges 0. | Holds the callable until after selecting the comparator, completes, charges 1. |

The last implementation matched the reference on the simpler lookup tests. The finalizer case isolates why equal lookup counts and order alone cannot establish a safe fallback. The 46 comparison rows include clean controls, the original poll raising, module and builtin shadows, and colliding keys. Each script asserts event order and charged work. [Extra lookup](check_scan_lookup.py) · [Key and value phases](check_scan_phases.py) · [Callable lifetime](check_callable_lifetime.py)

A separate stock poll installed local CPython monitoring before the guard. With original helpers in place, the key and value calls each provided a point where the observer could raise its exact marker before a debit. The isolated C158 segment offered neither Python call. Local monitoring remained active with zero global event mask and no trace or profile function. The three application-level counterexamples above work independently of interpreter monitoring. [Observer control](check_observer.py)

## Native implementation decision

The C158 C helper compares the retained lengths and ordered key and value identities of exact dictionaries while holding the CPython GIL. Admitting its data does not establish that substituting the call preserves the surrounding Python lookups, descriptor calls, temporary lifetimes or exception order. The current package supports Python 3.11+ and declares no runtime dependencies. Its authority checks identify specific Python functions and slots, and its numerical basis lists specific source files.

Reconsider native acceleration as a separately identified backend only after specifying the supported interpreter/ABI and observer boundaries, an inert dispatch mechanism, and when the exact Python fallback runs. Define how installation verifies the loaded executable against its build and C source and how the producer and reader identify the resulting numerical implementation. Preserve the complete Python path on unsupported hosts. The tested implementations have no qualifying dispatch condition for the existing default. No product binary or successor numerical identity was published.

## Fresh A08 and verification results

| Entry point on Linux x86-64 | Producer result | Read or validation result |
|---|---|---|
| Original Agent, 30-second grant | Timed out at 30.001 s with 250,882 operations in recording export/readback. | Setup failed before any of the 13 tests entered. |
| Configured Agent, 80-second grant | Published in 34.341 s with 452,627 operations. | All 13 read tests passed. The configured artifact was 2,447,148 bytes, digest prefix `b6e235d3`. |
| Direct exporter, original source | Produced the historical 2,447,148 bytes in 5.726 s of ledger time, digest prefix `6911a492`. | An independent reader checked 1,504 poses and 1,496 interval certificates. Chromium rendered front, oblique and back views and sampled eight carriers. Khronos validation found zero errors and warnings. |

Thirty callback and source-guard tests and three Agent cancellation/rollback tests passed. Four public and five simulator probes reproduced the C158 results. The two fresh Agent trials and the four direct callback experiments each used a new process. The four direct experiments used the **same** 80-second fixture and native clock. Omitting the optional callback gave 6.553 and 6.316 s. Supplying a callback that increments a counter gave 32.171 and 29.012 s. It ran 449,751 times per export. All four direct runs charged 448,334 operations and returned identical configured bytes. This measures the combined cost of supplying the callback and enforcing its checks. The producer receipts and individual test logs are in the handoff ZIP. [Digests, budgets and timings](measurements.json)

The previous full driver passed 33 of 34 roles. Its A08 setup timed out after 3,971 preceding methods. That full-driver result belongs to C157. The original Agent gate, full one-byte transfer and external playback sign-off remain open.

## Next experiment

Test the generated simulator predicate that checks 151 absent class descriptors and 84 present entries. On the retained descriptor catalogue, spelling each absence as `name in owner` reduced the isolated predicate median from 16.67 to 9.09 µs across nine shuffled rounds. Every row was still checked. Local call monitoring distinguishes this expression from a call to the original membership helper, so the first gate is a dispatch and fallback test. Then measure the *whole* Agent request with a separately fingerprinted candidate if eligibility holds. [Isolated timing script](predicates.py) · [Timing windows and profile attribution](results.json) · [Fallback and observer control](fallback.py)

Run the four scanner probes with the supplied CPython 3.12.14 environment. From the repository root, with `py` set to its Python executable, use the following commands. The observer additionally requires a C compiler and the corresponding CPython headers.

```sh
study=docs/engineering/torque-verification-c159
for name in check_scan_lookup check_scan_phases check_callable_lifetime; do
    "$py" -B "$study/$name.py" "$PWD"
done
"$py" -B "$study/check_observer.py" "$PWD" docs/engineering/torque-verification-c158/bench/dictscan.c
```
