# C221/0.1.0: frozen authority-binding checker

## Purpose and boundary

This experimental checker verifies that the eight inputs selected by the
[C220 plan](../second-target-c220/PLAN.md) retain their exact bytes and that the
18 planned parts consistently identify the same source occurrences and GLB
geometry records. It is a standard-library Python program. It does not import
OntoKin runtime modules, evaluate `.ok` source, regenerate an export, start Godot
or another native application, import a scene, or write a native scene.

Passing means **CPU authority binding passed**. It does not establish numerical
geometry, normal, material or pose fidelity, native provenance, useful rendering,
native persistence, or a second-target receiving promise. The original strict
normal failure remains unchanged. No target start is authorized by this report.

The contract is deliberately finite. It admits the original C210 after-edit
assembly and its pinned C214/C218 comparison evidence. It is not a general glTF
validator or a configurable replacement-manifest validator.

## Invocation and result

From the repository root:

```bash
python3 tools/second_target_c221/check_bindings.py --package-root /absolute/extracted-handoff
```

The supplied directory must contain the eight unchanged relative paths in
[C220 INPUT-BINDINGS.json](../second-target-c220/evidence/INPUT-BINDINGS.json).
A successor handoff can be used when it preserves those paths and bytes.
The checker reads the two authority documents from its own repository tree;
it does not select replacement authority from the supplied package.

The command emits one JSON document to standard output. Exit status `0` reports
`PASS_CPU_AUTHORITY_BINDING`; status `1` reports `FAIL_CLOSED` with a reason code.
Invalid command-line syntax uses the standard argument-parser status `2`.
The checker does not create or overwrite output files. A caller may redirect
standard output to a separate evidence file.

The report schema is `ontokin.c221.authority-binding-check/0.1`. A passing report
includes the authority-document pins, all eight file pins, accepted program
revision, observed structural inventory and explicit non-acceptance limits.
There is no `--allow-changed`, replacement-manifest, hash override, native probe,
source execution or target-launch option. `check_package(package_root)` is the
only supported admission API and raises `CheckError` on a refused input.

## Authority and safe file reads

The checker hardcodes the exact SHA-256, byte length and mode of the C220
`INPUT-BINDINGS.json` and `PART-MAP.json` documents at published base
`a266424b5cb0c3a7e020ab72d0ef8e7cd8886976`. The immutable document hashes are:

| Document | Bytes | SHA-256 |
| --- | ---: | --- |
| INPUT-BINDINGS.json | 3,512 | `6ce256ab7cfd9690665b7577e7bb9e3aca952c9b73e5e017b30dcded1d053625` |
| PART-MAP.json | 52,508 | `f8911b5d846114fe525ab753b78a16f665bd7a43775ecfce2e656d17eb1419ed` |

Both documents and all eight input files must have mode `0644`. The checker
first verifies the authority documents, then reads each input against the
verified document's exact byte length, hash and mode. A modified file accompanied
by a newly generated manifest is refused. The accepted program revision is also
a checker constant:
`sha256:c77d102a4b201d3c3cce6cbdc73c38eedf0bb1dfca7c9843a92d697cc0c7e082`.

Reads require POSIX directory-relative opening and no-follow support. The root
and each ancestor/component are opened as actual directories; symlinks are
refused. Relative input paths cannot contain absolute paths, empty components,
dot components, traversal, backslashes or NULs. Files must be regular files;
nonblocking open prevents a substituted FIFO from hanging before type checking.
Each read is bounded by its pinned size plus one byte, with a finite 4 MiB
per-file ceiling. Descriptor metadata is compared before and after reading.
The parser checks the exact bytes already read, rather than reopening a path
after checking its hash.

These checks protect this invocation's inspected bytes. They are not a hostile
host attestation or a guarantee that another process cannot modify a file after
the checker exits. A future observer must bind the bytes it actually consumes
under its own reviewed execution protocol. The current program does not verify
its own executable provenance; its reviewed Git revision and file hashes must be
preserved in the external evidence record.

## Independent structural checks

JSON parsing rejects duplicate keys, non-finite values, malformed UTF-8,
truncation and unsupported shapes. Boolean values cannot substitute for integer
indices. The checker implements the following joins without importing the
exporter, receiver or their acceptance helpers:

1. Encode both exact source strings as UTF-8 and independently compute each
   source revision. Reconstruct the canonical `ontokin.bundle/0.1` manifest and
   compute the program hash with its specified `ontokin.bundle/0.1` NUL domain
   prefix. Match the frozen revision and every retained manifest/source registry.
2. Parse the GLB 2.0 header and exact JSON/BIN chunk sequence. Check declared
   length, chunk bounds, embedded buffer length and padding. External buffers,
   sparse/interleaved accessors and unsupported component formats are refused.
3. Join all 18 planned rows with semantic-sidecar objects and GLB nodes by exact
   source path, element ID and node index. Require unique complete identity sets,
   definitions, owners, keyed occurrence steps and full source provenance.
   The global GLB occurrence registry must agree with per-node provenance.
4. Verify each provenance span's source ID, filename and revision, nonempty byte
   range, source bounds and UTF-8 boundaries. Repeated occurrences remain
   repeated: this fixture has 52 span occurrences covering 16 distinct ranges.
   Exact span contents are bound by the original source bytes and frozen map;
   the checker does not reparse or reevaluate the language.
5. Join node-to-mesh-to-primitive references and the selected material indices.
   Independently derive POSITION, NORMAL and index accessor metadata and hash
   their exact BIN bytes. Match the sidecar's accessor indices, views, component
   types, dimensions, counts and data hashes. Require complete triangle triples
   and in-range vertex indices. This accounts for 54 instance accessor uses,
   7,800 instance triangles and 23,400 instance corners.
6. Match the C214 payload's canonical hash, source/input bindings and all 18
   instance identities. Match the reference artifact/source bindings and its
   part identities. Verify the preserved source-oracle revision and C218
   observation payload link. All retained comparison files remain byte-pinned;
   their historical numerical acceptance is not rerun or relabeled. The full
   C218 reopen-details/observation and retained-oracle contents are not
   structurally revalidated; only the named revision/payload anchors are
   inspected after their byte locks pass. Other frozen-map fields, including
   the unobserved native-mapping flag and source-normal entry count, retain
   their meaning through the immutable map pin rather than a new observation.

Native/display names are not identity. The checker does not use GLB `name`,
semantic `name`, `godotNativeNode`, or `blenderComparisonObject` to join parts.
Changing any byte of the real admitted artifact still fails its immutable hash,
including a descriptive-name edit. Internal structural controls can change
descriptive names to demonstrate that semantic identity is independently joined;
such a control is not admission of modified source artifacts.

## Controls and remaining gates

The internal `validate_structure(bindings, part_map, inputs)` function is a test
seam for negative controls after decoding, using a dictionary of package paths
to bytes. It does **not** establish immutable file locks and must not be used as
an admission API. Private helper controls can isolate provenance joins from
outer artifact hashes. Public CLI/API controls must continue to reject modified
files, forged replacement authority, unsafe paths and modes.

Meaningful controls cover exact-byte admission, locked authority changes,
duplicates, missing/swapped identities, stale revisions, source-span changes,
malformed/truncated JSON and GLB, accessor bounds and hashes, path traversal,
symlinks, nonregular files and descriptive-name independence. Test results and
the independently reviewed source revision belong in the C221 evidence record.

Still pending are the numerical geometry/material/pose checker, Godot observer,
process reservation and resource-enforcement protocol, approved runtime settings,
build-lineage resolution or an explicit retained limitation, and a verified
rendering route. Any later execution requires a separately reviewed decision.
This checker consumes neither of C220's proposed future target starts.
