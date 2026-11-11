# Reader layout and metadata evidence

`EVIDENCE.zip` preserves the reader preparation sequence and its actual captured
synthetic inputs. It includes the earlier metadata failures and the repaired
results. All geometry was synthesized by the independent test generator; no
Blender, Node or lifecycle process ran for these cohorts.

| Cohort | Preserved result |
| --- | --- |
| Original layout preparation | 19 passed, then 20 passed after bounded auxiliary JSON reads. |
| Separate capture of original 20-method suite | 20 passed; 105 audit invocations, 11 corruption calls, 8 isolated Python reader CLI calls. |
| Independent metadata probes | Five provenance-bearing GLBs incorrectly passed the earlier reader. Their exact original bytes and report remain retained. |
| Metadata repair | 22 passed; 138 audit invocations, 11 corruption calls, 8 isolated Python reader CLI calls. |
| Exact five-probe repair check | All five rejected with `UNSUPPORTED` and `LAYOUT`; each retained 14 measured nodes and 2,056 measurements, with no `STRUCTURE` finding. |

The original 20-method result and the separately authorized capture replay are
different executions. The capture replay does not replace or retroactively
capture the original run. The repaired 22-method cohort has its own source
snapshot, command, runtime hash, input bindings, results and log.

Every captured API audit binds actual GLB bytes, expected inputs, optional
baseline, delivery rules and the returned report. The CLI observations also bind
the local executable directory, lock, command, process reply and result file.
The two versions of the observation harness are retained by their hashes.
The first harness omitted `-IB` from its reconstructed command field; its
recorded runtime flags show isolated/no-bytecode mode. The actual command used
`python3 -IB capture_reader.py` with its recorded arguments. The second harness
records `sys.orig_argv` directly.

The old synthetic generator marker remains in the original captured fixtures.
The repaired synthetic fixtures imitate the fixed production metadata as test
data. That field does not claim that a native exporter produced them. Static
source observations from the pinned exporter support the exact generator,
`StaticTray` scene name and forbidden buffer/accessor names. They are not a
native execution result.

`MANIFEST.json` binds the ZIP and dependencies. `FILES.json` inside the ZIP maps
logical paths to blobs or verified members of the existing review archive. It
also preserves original POSIX modes, symlink targets and any hardlink groups.
Use the verifier described in the adjacent `source-resources/README.md` to check
every byte binding without executing the retained tests or inputs.
