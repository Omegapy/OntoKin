# A08 binding checks and source identity at C158

The [C157 runtime](https://github.com/Omegapy/OntoKin/commit/53e7648b805c2ae29a5089709d17842252899e6c) still misses the 30-second Agent deadline on the frozen two-second torque animation. Two fresh processes on Linux x86-64 and CPython 3.12.14 timed out while exporting. No artifact was published and none of the 13 read methods began. The two separately configured 80-second controls published their expected bytes and completed every read, including the cancellation and rollback cases. [Receipts and measurements](measurements.json)

| Fresh CPU 4 trial | Producer time | Charged operations | Read methods passed |
|---|---:|---:|---:|
| Original A1 | 30.003 s | 271,006 | 0 of 13 entered |
| Original A2 | 30.001 s | 354,440 | 0 of 13 entered |
| Configured A1 | 32.940 s | 452,627 | 13 of 13 |
| Configured A2 | 32.723 s | 452,627 | 13 of 13 |

All four used fresh SQLite stores and the one-million-operation ceiling. The direct exporter produced the exact original 2,447,148 bytes in 5.913 seconds of producer time. The independent reader checked 1,504 poses and 1,496 interval certificates. The original SHA-256 begins with `6911a492`. The configured artifact has a separate source revision and its SHA-256 begins with `b6e235d3`. The machine-readable record contains both full digests. [Measurements](measurements.json)

## Why the 30 shared checks must run again

The two binding catalogues contain 289 and 165 rows. Thirty rows check the same key, expected object and mutable builtins dictionary. On an exact simulator instance, a method-name lookup between the two checks can run a dictionary key’s `__eq__`. The probe used that lookup to replace `builtins.hex`. The original guard caught the replacement in the evaluation phase. Removing only the second `hex` check let execution reach a different, later error. A supported subclass or the generic fallback also reaches the instance lookup. The executable counterexample exercises the exact-class path. [Reproduce the binding counterexample](check_binding_overlap.py)

Only 14 of 1,107 sampled producer stacks stopped on the 30 shared comparisons. C157 recorded 13 of 1,251. The repeats give similar estimates of their share of CPU time. Neither measurement supports recovering the full time shortfall by removing the overlap. [Measurements](measurements.json)

## What the source scans cost

The profiled producer spent 178 of 1,107 samples on dictionary keys and values. All 178 scan samples came from the simulator, as did all 218 in the prior C157 profile. In another run the export performed 253,946 complete source checks. Creation added 3,826. Each watch held 465 entries across 79 dictionaries. The export therefore compared 118,084,890 keys and as many values by object identity. Moving an entry across adjacent dictionaries can preserve both flattened sequences, so individual dictionary lengths also matter.

Combining the two scans in Python gave medians of 34.44 and 33.99 µs for the scan segment in one process. The isolated native experiment used a separate process and included the length checks. It reduced the median for the **whole source guard** from 28.03 to 11.20 µs on a captured watch. Its 28 controls covered mutations, restoration and malformed native inputs. The benchmark used a single captured watch. [Isolated benchmark](bench/native_probe.py) · [C source](bench/dictscan.c) · [Timings and 28 controls](bench/native-probe.json)

An unconditional native substitution would change public preflight behavior. In the stock public API, an original poll callback can replace `vars`, which then replaces `chain` after the guard begins. The key scan runs, the value scan raises the exact supplied exception and the charge stays at zero. A clean tick charges one. An eligibility decision made at guard entry would miss this case. The three hostile probes and clean control restore the original module bindings. [Reproduce the preflight boundary](check_preflight_callbacks.py)

The exact simulator also permits the original poll to replace `is_` or `chain`. The simulator rejects a direct `vars` replacement at admission. It still reads `model.program_revision` afterward, and the probe used that descriptor to change `vars`. The subsequent instance check then replaced `chain` after the source guard began. Its value scan raised the original exception, with zero operations charged. An exact simulator type and unmodified operators at guard entry are insufficient. [Reproduce the simulator counterexample](check_simulator_callbacks.py)

Run the isolated benchmark from a clean Linux checkout with CPython 3.12.14, a C compiler and matching Python headers. From the repository root, use an available logical CPU.

```sh
bench=docs/engineering/torque-verification-c158/bench
taskset -c 7 python3.12 -B "$bench/native_probe.py" "$PWD" "$bench"
```

## Next development gate

Keep public preflight on its current Python path. Determine whether the simulator itself has a point at which all lookup and call behavior needed for the dictionary scan is still known to be native. Test a callback that changes a binding after admission. Establish the fallback and original exception order before making a producer candidate. A compiled implementation would also need an explicit packaging and fingerprint design for the standard-library reference. The standalone prototype uses a compiled extension and has no eligible product path yet. A qualified candidate must show a whole-request improvement and pass the original fresh and in-suite 30-second cases. The C158 work publishes evidence only. The prior full-driver result remains 33 of 34 roles at C157. [C157 verification](../torque-verification-c157/README.md)
