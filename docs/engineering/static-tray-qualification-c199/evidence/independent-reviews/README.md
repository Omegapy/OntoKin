# Retained independent review snapshot

This package retains eleven completed review directories named in
`MANIFEST.json`. It includes original blocker findings and failed probes as
well as later repair reviews. Those historical records retain their original
meaning; this package does not declare that every earlier review passed.

The top-level JSON records from each review are copied without modification
under `reviews/` for direct reading. `captured-reviews.tar.gz` preserves the
complete original selected directories: probes, logs, captured source/resource
inputs, symbolic links, hard links and modes. The manifest gives exact byte
hashes, sizes, member types and link relationships. The source directories and
any earlier tracked preflight evidence were not changed.

Later exact input-lock approval and native result directories are excluded.
This fixed snapshot cannot authorize a native start or replace the eventual
approval of the exact final lock. Packaging performed no new tests, native
jobs, readback checks or lifecycle controls.

Archive headers and every file payload were inspected against the manifest
without extraction or execution. The tar records original modes, including
0444 where observed. This does not establish that an arbitrary extraction tool,
umask or filesystem enforces those permissions, nor does Git preserve read-only
mode bits in a checkout. Verify modes, bytes and link relationships explicitly
after restoration. Captured adversarial-input symlinks are preserved as links;
their targets are not copied or followed by this packaging step.
