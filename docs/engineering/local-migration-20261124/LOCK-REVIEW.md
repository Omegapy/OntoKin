# Independent review of the macOS arm64 verification lock

## Reviewer

- Reviewer: independent reviewer subagent with a fresh context; model inherited
  from the session.
- Date: 2026-11-25. The checks ran between 06:57Z and 07:11Z.
- Role: Reviewer for task LOCAL-MIGRATION-20261124, step TASK-010, requirement
  REQ-006, before anything is installed from the lock.
- Not produced by the reviewer: the lock, the provenance record, the staged
  wheels, the tracked specification and the tools that read them.
- Method: the reviewer downloaded every wheel again from the package index into
  the reviewer's own directory and hashed the bytes there. The download script
  reads neither the lock nor the provenance record; it chose each wheel from the
  index record. Nothing from a wheel was installed, imported or executed. The
  scripts ran with CPython 3.12.13 in isolated mode, from a directory that holds
  no wheel.

## Reviewed inputs

| File | Bytes | SHA-256 as computed by the reviewer |
| --- | --- | --- |
| `tools/native-reader-verification-macos-arm64-cp312.lock` | 799 | `b1e3e86668421539c6817faefe7f126b4dbf25153fcbb2fab6325e080cf7a81c` |
| `tools/native-reader-verification-macos-arm64-cp312.provenance.json` | 6,508 | `cbcc1b27797ab4a8742ad8b0360a25164e1dadb61f8da12d54e930c317355415` |
| `tools/native-reader-verification-linux-cp312.lock` | 779 | `a7f17491000c2e139ccc5d213ca0e8a6f917e5befb4b878fef29f5ff72ae780f` |
| `tools/force-agent-verification-requirements.txt` | 270 | `6d5fefcbd7ccced7d39bf8d20e87ec1c4401fc6b252aea41677d41d9124555d1` |
| `tools/local-environment.json` | 7,982 | `c70b9d43634f9a35170e4ac633a6e352e7a986a6fb8ab10639fa60a9c776f9b4` |
| `docs/engineering/local-migration-20261124/PRESERVATION.json` | 5,047 | `ef0d64581466d4f124f46c55885a0baf514c1f960548294e2b81302b402ed4af` |

- The values for the two locks and the requirements file equal the ones the
  assignment expects.
- All of these except the preservation record were hashed at the start and again
  at 07:07Z and 07:11Z; nothing had changed. The preservation record was hashed
  once.
- The worktree head was `bb80175704d82567a2e8528edf8407695e0e63a1`. The lock and
  the provenance record were not yet committed. The tracked specification and the
  preservation record equal their committed blobs.
- Base revision: `git show` of the Linux lock and of the requirements file at
  `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774` gives the same SHA-256 values as above.
- Staged wheels: the staging directory held exactly the seven files named in the
  per-wheel table and nothing else. Each is byte-identical to the reviewer's own
  download, so its SHA-256 is the one in that table.

## Checks

| Criterion | What was done | Observed result | Result |
| --- | --- | --- | --- |
| 1. Exactly the seven adopted versions, each with the SHA-256 of the wheel bytes | Parsed the raw lock bytes and compared the entries with the seven versions named in the assignment, the six requirements pins, the Linux lock and the tracked specification. Hashed the reviewer's own downloads. | Seven entries, the seven adopted versions, nothing else. Each hash equals the SHA-256 of the reviewer's own bytes and the digest in both index records (JSON and simple). | Pass |
| 2. Provenance record is complete and true | Parsed the record with duplicate-key detection and compared every field with the reviewer's bytes and the index records. | For all seven wheels the filename, the Python, ABI and platform tags, the source URL, the byte size and the SHA-256 are true. So are the index-record URL, upload time, yanked flag, Python requirement, platform-independence flag and Linux-equality flag. Each index record and source URL answered 200 without a redirect, and the digest inside each source URL equals the BLAKE2b-256 of the reviewer's bytes. The two lock digests it quotes are right. | Pass |
| 3. Five platform-independent hashes equal the Linux lock; the Linux lock is unchanged | Compared the hashes. Compared the working bytes with `git show` at the base revision and with the preservation record. | All five are equal. The Linux lock is byte-identical to the base revision (blob `e82d499012bab9349c7bb2ee310bb2b7bc63de0d` at the base, at the head and in the working tree), and so is the requirements file (blob `26345fd6d042cb8617b35cb1856afe8e10eb88fe`). Both agree with the preservation record. | Pass |
| 4. Existing lock format, nothing extra, nothing missing | Parsed both locks byte by byte with the same strict rules. Also read the lock through the requirement parser of the host's pip 26.0, used as a library; pip was not run. | Eight ASCII lines ended by LF: one comment line, then seven lines of exactly `NAME==VERSION --hash=sha256:HEX`, with the names, spelling and order of the Linux lock. No option line, URL, marker, extra or continuation, and one hash for each package. The two locks differ only in the comment, rpds-py and Pillow lines. pip's parser reads seven pinned requirements with one SHA-256 each. | Pass |
| 5a. Filename tags | Evaluated every file of the seven releases in the index. Compared the tags with those the host interpreter supports, as listed by the packaging code inside the host's pip. | For each package exactly one wheel fits CPython 3.12 on macOS arm64, and it is the locked one. The host (CPython 3.12.13, macOS 26.6.2, arm64) supports every tag. None of the files in the seven releases is yanked. | Pass |
| 5b. WHEEL and METADATA | Read both files inside each archive. | Name, version and Tag lines match the pin and the filename. Root-Is-Purelib agrees with the tags. Requires-Python admits 3.12.13 in all seven. Requires-Dist equals the index record. The METADATA digest equals the one the simple index publishes. | Pass |
| 5c. Compiled members are arm64 Mach-O | Parsed the Mach-O headers in memory. Ran `file` and `lipo` on copies, each in its own new directory. | 27 compiled members: one extension module in rpds-py; eight extension modules and 18 bundled libraries in Pillow. All are thin 64-bit arm64, for macOS, with minimum OS 11.0. The nine extension modules end in `.cpython-312-darwin.so` and export their `PyInit` function. The five platform-independent wheels hold no compiled member. | Pass |
| 5d. Compiled members can be linked on this host (static) | Read load commands, symbol tables and code signatures. Looked Python symbols up in the export table of the host's CPython 3.12 library, read as bytes, and system symbols in Apple's own libraries. | Every library reference is a macOS system library or a member of the same wheel with a sufficient compatibility version. All 345 Python, 442 bundled and 708 system symbol references resolve; the only others are the 27 to the loader's own `dyld_stub_binder`. All 27 ad hoc code signatures match their code pages. One bundled Pillow library (libjpeg) carries an unused build-machine run path; nothing loads through a run path, so it has no effect. | Pass |
| 6. Dependency closure | Evaluated every Requires-Dist line for CPython 3.12.13 on macOS arm64 without extras, once with the reviewer's own evaluator and once with the packaging code inside the host's pip. | 51 lines, of which eight apply. All eight name one of the seven pins at an accepted version: jsonschema needs attrs, jsonschema-specifications, referencing and rpds-py; referencing needs attrs, rpds-py and typing_extensions (below Python 3.13); jsonschema-specifications needs referencing. Both evaluations agree. No wheel declares a default extra. | Pass |
| Further: undeclared imports | Parsed all 172 Python members with the CPython 3.12 grammar and listed their imports. | All parse. Outside the packages' own tests and benchmarks, an import from outside the standard library and the seven is guarded, or belongs to an optional Pillow plugin whose dependency is a declared extra and whose loader ignores a failed import. | Pass |
| Further: archive safety | Compared central directory, local headers and RECORD, and looked for hidden bytes, unsafe names and files that run at interpreter start. | RECORD lists every member with its true hash and size. No hidden bytes, duplicate name, unsafe path, link, data directory, `.pth` file, `sitecustomize` module or bytecode. No path is delivered by two wheels and no module shadows the standard library. | Pass |
| Further: the two new binary wheels against the adopted Linux wheels | Downloaded the two Linux wheels that the existing lock adopts, checked them against that lock and compared the members. | Every Python source and stub member (2 in rpds-py, 105 in Pillow) is byte-identical, and both platforms deliver the same extension modules. Apart from compiled members, only RECORD, WHEEL and the software bills of materials differ. | Pass |
| Further: publisher statements | Read the attestation record the index serves for each wheel. | Each names the same filename and SHA-256 and the expected upstream repository. Signatures were not verified. | Pass |
| Further: privacy | Searched the lock and the provenance record. | No account name, machine path or credential. | Pass |
| Further: can the checks fail | Ran the checks for criteria 1 to 4 on 18 altered copies of the lock, the provenance record or the Linux lock in the reviewer's own directory, and on an unaltered copy. Ran the closure check on a lock without rpds-py. | Every altered copy was rejected for the intended reason: a changed hash, version, size, tag, URL, filename or flag, an added option, URL, hash or package, a missing package, a changed order, CRLF line ends, a duplicate key, a Linux wheel hash in the macOS lock, and a changed Linux lock. The unaltered copy passed. The closure check reported the two unmet dependencies on rpds-py. | Pass |

Two of the reviewer's own checks first reported differences that were faults of
the checks. A literal comparison of Requires-Dist lines failed for jsonschema and
referencing because the wheels quote marker values with single quotes and the
index record with double quotes. An import scan did not recognise
`with suppress(ImportError)` or declared extras as guards. Both checks were
corrected and run again.

## Per-wheel table

| Package | Version | Filename | Bytes | SHA-256 of the reviewer's own download | Equal to lock | Equal to provenance | Equal to staged | Equal to Linux lock hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attrs | 26.1.0 | `attrs-26.1.0-py3-none-any.whl` | 67,548 | `c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309` | Yes | Yes | Yes | Yes |
| jsonschema | 4.26.0 | `jsonschema-4.26.0-py3-none-any.whl` | 90,630 | `d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce` | Yes | Yes | Yes | Yes |
| jsonschema-specifications | 2025.9.1 | `jsonschema_specifications-2025.9.1-py3-none-any.whl` | 18,437 | `98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe` | Yes | Yes | Yes | Yes |
| referencing | 0.37.0 | `referencing-0.37.0-py3-none-any.whl` | 26,766 | `381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231` | Yes | Yes | Yes | Yes |
| rpds-py | 2026.5.1 | `rpds_py-2026.5.1-cp312-cp312-macosx_11_0_arm64.whl` | 345,775 | `58b1d94308ddf0b1982f61f2eb54bf92997c9ece8a8093ef014250f4a517906c` | Yes | Yes | Yes | platform-specific |
| typing_extensions | 4.16.0 | `typing_extensions-4.16.0-py3-none-any.whl` | 45,571 | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` | Yes | Yes | Yes | Yes |
| Pillow | 13.0.0 | `pillow-13.0.0-cp312-cp312-macosx_11_0_arm64.whl` | 4,852,329 | `fc481f742ccda20e9ed760b8f978dff50f2a4e9bc253ac167fb0a05b0783ef52` | Yes | Yes | Yes | platform-specific |

The two platform-specific hashes in the Linux lock belong, in the index, to the
manylinux x86-64 wheels of the same versions.

## Findings

None.

## Disposition

Disposition: accepted for use

## Limits

- The disposition covers only the bytes whose SHA-256 values are listed above. A
  change to the lock or the provenance record needs a new review.
- No wheel was installed, imported or executed. Import behaviour, run-time
  behaviour, `pip check` and the native-reader preflight were not checked.
- The index, reached over HTTPS, is the source of every byte. For the five
  platform-independent wheels the existing Linux lock is an earlier record of the
  same hashes. For the two binary wheels no record independent of the index was
  checked, and the publisher attestations were read but not verified.
- Package code was not reviewed for vulnerabilities or behaviour. At the time of
  the check the index listed no known vulnerability for the seven versions; no
  other vulnerability source was consulted.
- Compiled members were read statically. They were not loaded or disassembled,
  and their signatures were checked only against their code pages.
- The provenance statements about how the wheels were fetched, which interpreter
  was used and that nothing was installed cannot be established from bytes. What
  was observed: the staging directory and its files were created at 06:56Z,
  before the lock and the provenance record; the host's Python 3.12 in isolated
  mode lists none of the seven packages; and neither the worktree nor the main
  checkout had a `.venv` at 07:07Z. The provenance date is the UTC date. Other
  interpreters and environments were not checked.
- Only one host was used. Other CPython 3.12 patch releases and other macOS
  versions were not checked beyond the tags and minimum-OS fields.
- Bootstrap and doctor tools and their tests appeared untracked in the worktree
  during the review. They were not reviewed.
- The Linux lock was checked for identity and for the platform of its two binary
  hashes only.
