# Independent publication-helper review

**Amended helpers passed, subject to the explicit caller obligations below.** The initial review required changes; `integration-helper-review01.json` preserves those findings and initial behavior. `integration-helper-review02.json` binds the amended helper bytes and all evidence.

The hermetic driver ran 34 cases: 17 initial-behavior reproductions and 17 amended-helper checks. All produced the independently expected outcomes. These were synthetic temporary Git repositories created only for this review. No project checkout, network service, remote ref or production runtime was touched. The driver, exact commands, native identities, complete helper results, stdout/stderr and expected/actual outcomes are retained.

## Corrected findings

| Initial gap | Amended behavior and evidence |
| --- | --- |
| Any execute bit was treated as sufficient native mode evidence | Exact filesystem 0644/0755 required; previous 0600 and 0744 false successes now refuse |
| Reviewed ref and staged index could differ | Index equals the captured target tree at start and end; an index-only unreviewed entry refuses |
| Staged index could change during enumeration | Both helpers reject the injected mid-capture index change |
| Symbolic ref names were returned or resolved again for the receipt | Parent, baseline and target are captured once as immutable IDs; receipts identify that captured tree |
| Fresh-output exists check could follow a dangling symlink | Exclusive creation preserves existing bytes and refuses dangling output symlinks |

Additional controls verify exact UTF-8/multibyte/CRLF, empty-file and executable-mode descriptions; NUL and invalid-UTF-8 binary handling; native SHA-1 and SHA-256 identities; and refusal of source deletion, changed old runtime, outside-scope additions, worktree byte mismatches, untracked source and nonordinary Git entries.

The original source was read completely before amendment. A subsequent filesystem-copy attempt raced the author's revision and refused before copying. Initial source snapshots were reconstructed from that complete observed text through the exact inverse amendment. The input receipt records this limitation; it does not claim a pre-amendment filesystem hash or mode measurement. The amended snapshots are exact measured filesystem copies and still match the current helpers.

## Caller obligations

Bind preservation verification to the same immutable target tree emitted by preparation. Upload each binary blob as its exact original bytes and verify the returned Git blob ID. Verify the returned remote tree and commit parent/tree before the expected-head ref update. Then perform complete resulting-main source/readback verification. None of those publication gates is established by a local helper's success.

The helpers use fixed subprocess argument arrays and no shell, network call or ref-update command. `write-tree` creates the intended local native tree objects; exclusive result-file creation is the other intended local mutation. They operate within the recovered trusted Git path namespace and explicitly chosen output parent directories. They are not general untrusted-archive extractors, and their object hashing assumes this repository's existing SHA-1 format.
