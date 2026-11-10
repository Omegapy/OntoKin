# Receiving receipt interpretation

The C193 driver copied and executed the exact pinned C191 receiving scripts.
Their original labels and bytes are preserved. In particular, the Blender
receipt's static task label says C191 and its static attempt label says
`corrected-low-light`. Those inherited labels identify the existing render
configuration; they do not report an earlier C193 rendering attempt or reused
images. This C193 execution is identified by its fresh UTC times, full command,
actual input GLB hashes, imported bounds and the eighteen resulting PNGs.

The startup command requested four threads. The unchanged renderer explicitly
sets eight scene render threads, as the actual receipt reports. Eight is the
correct rendering setting. No relative performance or timing-neutrality claim
is made. Jobs used the shared environment; resource isolation is not established.
Native qualification and saved-scene resimulation are separate jobs;
all native samples passed their exact comparisons. The complete legacy driver
started after receiving rendering finished.

All twenty-eight paths pass Khronos validation with zero errors and warnings.
Twelve final-output reports contain the informational `UNUSED_OBJECT` sampler
finding. All information-level messages are retained. The disabled case's raw
and final GLB bytes are identical, so the twenty-eight paths contain eleven
distinct GLB hashes. Three.js evaluates all eighty-four named poses. Six actual
final files are imported into Blender; their eighteen rendered poses were
visually reviewed. These are CPU-rendered import checks, not browser, GPU or
live destination-physics evidence.

The archived execution summary intentionally says visual review was pending at
the end of rendering. The subsequent visual-review receipt and combined result
record the completed review without rewriting that earlier execution receipt.
