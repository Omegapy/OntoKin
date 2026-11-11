# Retained integrated CPU attempts

The original aggregate remains **failed**: 79 reported methods comprised 78
passes and one receiving-module import error. Its log and result have not been
rewritten. The separate receiving import repair passed 11 methods in 1.879 s.
The later integrated aggregate passed 92 methods in 53.833 s. The focused
manifest staging controls passed 28 methods in 1.762 s. These are separate
executions and their durations and counts must not be combined.

`receipts/` exposes the original command, result and log bytes. The original
receiving receipt contained a command synopsis. Its unchanged bytes are in
`receiving-repair.original.json` and in the archive at their original path.
The adjacent `receiving-repair.json` explicitly labels the coordinator-provided
exact argv as a post-run correction. The manifest staging `execution.json` is
also a post-run transcription. Neither separate run retained its full inherited
shell environment. The final aggregate has its own captured explicit environment.
Missing original input captures have not been recreated.

`captured-attempts.tar.gz` contains the original complete captured directories,
including their source/resource inputs and unmodified original receipts, plus
the focused cap log. `MANIFEST.json` records each member's byte hash, size, type,
mode and link relationships. The archive preserves symbolic links without
following them and stores hard links as hard links. Header and content checks
were performed by reading the archive; no test, native job or checker was run.

The archive records original modes, including 0444 where observed. An arbitrary
extractor, umask, filesystem or Git checkout may apply different permissions.
After restoration, verify bytes, modes and link relationships explicitly. Some
test symlinks intentionally represent rejected inputs and may be dangling.
Do not execute captured source merely to inspect this evidence.
