# C187 · Two-carriage linear gauge starters

Two fresh coding agents built the same seven-part gauge from a common design, one in Blender/Python and the other in OntoKin. Both passed on their first formal submission. Each shoe moves 300 mm with its carriage in two seconds. The base and both stops stay fixed. The checker measured the gap from each shoe’s front face to its own stop across the full animation. [Design dimensions and tolerances](assembly.json) · [Measurements and hashes](results.json)

| Submitted GLB | Initial gap, both lanes | Left minimum | Right minimum | Time of minima |
| --- | ---: | ---: | ---: | ---: |
| Blender/Python | 315.0000 mm | 14.999993 mm | 14.999993 mm | 2.000 s |
| OntoKin | 315.0000 mm | 15.000008 mm | 15.000008 mm | 2.000 s |

The checker decoded geometry, colors, names and world-space motion from each GLB. It checked all 21 pairs of parts for overlap throughout the clip. Four accepted controls, 26 deliberately defective controls and three swept-overlap cases exercised the checker. Two builds in fresh directories per route reproduced the submitted GLBs byte for byte. Both exports opened in the same viewer at 0, 1 and 2 seconds. [Six-pose comparison](comparison.png) · [Frozen checker, controls, independent reviews, playback and rebuilds](verification.zip)

Blender gives both shoes a common size in the build script and parents each shoe to its moving carriage. Reopening the submitted `.blend` and exporting it again reproduced the delivered GLB. OntoKin instantiates a common `Shoe` class for the two shoes and gives each shoe and carriage its own 0.15 m/s motion. Its source uses spherical body proxies with collision responses disabled. The exported cuboids follow the same paths. A mechanical attachment or collision response therefore needs separate evidence. Recompiling the `.ok` program independently reproduced the sealed native GLB. The OntoKin build copies seven node IDs into mesh names after native export. All other JSON values and the embedded binary chunk match the native GLB. [Native sources, build instructions, author reports and exports](deliveries.zip)

Both agents worked in separate directories in a shared environment, with 30 minutes from tool readiness and up to four formal submissions. Their reports describe the corrections they made before submitting. Provider token totals, active model time and cost were unavailable. Khronos glTF Validator 2.0.0-dev.3.10 reported zero errors, warnings, infos and hints on both submitted GLBs and the raw native OntoKin GLB. These observations qualify two starting assemblies for the localized repair. [Dispatch conditions](dispatch.json)

## Replay the independent checks

Extract both archives into the same empty directory. With CPython 3.12.14 and NumPy 2.3.5 available, run the following commands from this record’s directory. The replay checks the frozen fixtures, both delivery seals, the four clean rebuilds, the native-to-final field changes and the six playback receipts. The full handoff provisions this interpreter with `check-indexer.sh`.

```sh
mkdir replay
unzip -q deliveries.zip -d replay
unzip -q verification.zip -d replay
python3 -B replay/gauge/replay.py > replay/results.json
cmp results.json replay/results.json
```

## Next repair

Extend only the left shoe’s rear face from X = 80 mm to X = 50 mm. Keep its forward face at 180 mm and preserve the other six parts. The right shoe remains 100 mm long and both 15 mm end gaps must survive. C188 will measure the first localized repair on this fixture. [Participant brief](next/participant.md) · [Numeric design](next/assembly.json) · [Coordinator checks](NEXT-TASK.md)
