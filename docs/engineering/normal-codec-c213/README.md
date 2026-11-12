# C213 CPU normal-codec characterization

C213 characterizes the selected Blender 4.3.2 normal encoder and decoder on the CPU. A shading normal is a direction used to calculate a surface's appearance. Blender's selected codec stores two angular short integers relative to a local normal frame. The experiment supplies that frame explicitly and measures the resulting loss.

**The finite characterization is complete; the original receiving gate remains failed.** Independently declared cases show that the codec's direction shortcuts can lose substantially more than short-integer rounding alone. No replacement tolerance is adopted, and held receiver [PR #155](https://github.com/Omegapy/OntoKin/pull/155) is unchanged. No Blender process ran.

Published through [PR #159](https://github.com/Omegapy/OntoKin/pull/159); the [integration receipt](evidence/publication/INTEGRATION.json) binds the exact merged source and actual-main checks.

Start with [results and limits](RESULTS.md). The [implementation](IMPLEMENTATION.md) explains the precise input domain, scalar float32 build, source extraction, reproduction commands and attribution. [Source bindings](SOURCE-BINDINGS.json) identify pinned upstream commit `32f5fdce0a0a571a39198edf8d7b5d719bf59f2c`; they do not attest the source lineage of the C211 executable.

The [independent corpus](evidence/independent-controls/PREDECLARATION.json) was sealed before execution. Its final 212-case run passes 934 assertions after one separately documented [oracle correction](evidence/independent-controls/ORACLE-CORRECTION.json). The original failed assertion and its observations remain unchanged. Separate source review checks the selected function bodies and float support against upstream. These checks qualify this experiment, not a full product release.

The [next bounded task](NEXT-TASK.md) is an experimental CPU-only source-normal payload and loss-report contract. It must preserve exact authoritative directions and distinguish them from approximate native shading directions. C211's strict promise and failed evidence stay separate. Any subsequent receiving attempt requires its own reviewed contract and execution plan.

## Reproduce the finite experiment

From the repository root, with Python 3.11+ and a C++17 compiler:

```bash
python3 -IB docs/engineering/normal-codec-c213/run_probe.py \
  --cases docs/engineering/normal-codec-c213/evidence/independent-controls/cases.json \
  --output /tmp/c213-observed.json --build-dir /tmp/c213-cpu-build
python3 -IB docs/engineering/normal-codec-c213/evidence/independent-controls/check_results.py \
  /tmp/c213-observed.json --output /tmp/c213-checked.json \
  --oracle-correction docs/engineering/normal-codec-c213/evidence/independent-controls/ORACLE-CORRECTION.json
```

Keep the sealed inputs and expected values unchanged. The explicit correction accepts the upstream decoder's full signed-short domain; it does not change the original receiving tolerance. Compiler and mathematical-library differences remain visible in the generated report.
