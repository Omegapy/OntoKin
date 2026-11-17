# C258 retained evidence

The live scientific source is `../follows.py` and its authored tests are
`../test_follows.py`. Their approved input commit is
`2bca9f7d2cba8996043bbfeae0c2855def5d7076`. Copies inside this directory are
historical evidence for identified executions, not alternate current readers.

## Exact-byte retention

[EVIDENCE-LOCATIONS.json](EVIDENCE-LOCATIONS.json) maps each logical dataset and
original audit path to an actual repository path, byte size and SHA-256. The
mapped file is the preserved payload. Some exact duplicates share one file;
unchanged original sources/artifacts map to their existing C210 proof paths.
Every required entry in the prior independent review, final supplement and
structural manifest has a verified location. No entry depends only on a
temporary path or an active symlink.

The initial and corrected independent review manifests retain their original
bytes. In particular, the older manifest called its reviewed reader a
repository equivalent. That equivalence no longer applies to the current
reader hash. The location map explicitly resolves the old `aea52fc1...` bytes
to a retained author snapshot instead. The original symlink failure retains
an exact recipe and its filesystem lifecycle; a cyclic symlink is not embedded
in the archive.

Historical contract Markdown is stored as exact `.md.txt` bytes when its
original repository-relative links would be misleading at the archive
location. [AUTHOR-RETENTION.json](AUTHOR-RETENTION.json) records those names,
hashes and the actual execution state of each authored attempt.

## Reproduction

Restore the full repository through the handoff's documented source restore
path. Use an isolated hosted worktree at the execution commit named in a
receipt, then run its recorded command. The current component's two CLI
commands and authored suite are documented in its [README](../README.md).
The reader requires the exact C257 dependency at its repository-relative path.
Copied readers inside evidence are not standalone relocated programs.

To reconstruct an original review directory, select its `dataset` entries
from the location map and copy each `retainedRepositoryPath` to that entry's
`originalPath` under a fresh audit directory, checking bytes and SHA-256 first.
Do not alter the archived receipts to substitute current paths or commits.
The independent scripts and fixture builders are retained for replay; their
recorded commands identify the actual source checkout and output directory.

The root agent owns publication, live-main verification, branch lifecycle and
saved delivery evidence. These component receipts do not claim those later
operations succeeded.
