# C268 historical endpoint reader implementation

Implementation author: `/root/reader_impl`. Scope: C268 R01–R03 in the shared
Director-owned checkout. This is an implementation candidate; independent
controls, exact-candidate review, affected regression, integration and saved
delivery are separate gates.

The candidate [endpoint_reader.py](endpoint_reader.py) is 14,883 bytes with
SHA-256 `f615f14f5d4bcee3a3ecdb20466fd60b0a04df2dcd13095d993baf20b1430086`.
No predecessor source, fixture, contract, workflow state or Git index was
changed by this worker.

## Authority and input identities

The implementation applies the unchanged [C260 contract](../localized-repair-c260/CONTRACT.md),
[input bindings](../localized-repair-c260/INPUTS.json),
[control plan](../localized-repair-c260/CONTROL-PLAN.md) and
[field origins](../localized-repair-c260/FIELD-ORIGINS.md).
The [C267 review](../localized-repair-c267/REVIEW.md) identifies the comparator's
finite comparison scope and retained C266 provenance boundary.

Expected endpoint paths, byte counts and hashes are literal immutable tuples
inside the reader. They were transcribed from C260 INPUTS.json, 4,605 bytes,
SHA-256 `d9f81932098104b051667d9523744530525ac891c3898718d8b1625db1941b8d`.
The two entry-source pins and shared dependency also match the actual frozen
C253 corpus, 15,763 bytes, SHA-256
`2d65c6b5f31457f99372d3cd02bbbf79c5922c03d776cfd8cd5605fac6d156b5`.
Runtime admission does not read a mutable manifest or obtain expected values
from a caller. These historical hashes admit bytes; hinge values still come
from the supplied source and artifact through the pinned comparator.

All historical paths are below
`docs/engineering/semantic-export-c210/evidence/proof/`.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `before.main.ok` | 1,708 | `73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123` |
| `after.main.ok` | 1,708 | `443328e2a2e3f2e68245fa1e725b518187aa446ecd7ee3de4675e006cf4e666a` |
| `hinges.ok` | 1,911 | `1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a` |
| `before.glb` | 185,276 | `d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534` |
| `after.glb` | 185,236 | `05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8` |

The complete code dependency closure is also pinned literally and checked on
every public call. Paths in this table are relative to `docs/engineering/`.

| Component | Path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| C267 comparison | `localized-repair-c267/hinge_compare.py` | 12,382 | `f98b9eab7a7f0cc75afa26eab0b672356d7e3275e3d713d16df214e68e69d71d` |
| C266 input binding | `localized-repair-c266/hinge_binding.py` | 17,639 | `68849dbe3339c158eac7ec43fb1defcbd2993c37c6a0a5ee813d2da71fb03dda` |
| C265 source observation | `localized-repair-c265/source_hinges.py` | 37,570 | `04bea0f7c5f82a3e3e74610d3ee98755f44ed0905566c00eb063647e31abbf9e` |
| C261 artifact observation | `localized-repair-c261/hinge_glb.py` | 14,036 | `6167b3a56a2b1a600812340d85ee02eaa3b6399801d585a758333aabcfaa5e08` |
| C257 identity utilities | `localized-repair-c257/ownership.py` | 35,942 | `c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1` |

## Public behavior and supported paths

`read_bound_endpoint(repo, endpoint)` accepts an exact built-in string endpoint
equal to `before` or `after`. It accepts a root as a built-in `str` or the native
concrete `pathlib.Path` type (`PosixPath` on the tested host). Absolute roots and
roots relative to the process's current working directory are supported.
Byte paths, file descriptors, custom path-like objects, `PurePath` and type
subclasses are outside this API. A string root must be nonempty; `Path("")`
already represents `.` when supplied by Python.

The root must resolve through ordinary directories. Every opened root ancestor,
input ancestor and leaf is accessed with `O_NOFOLLOW`. A lexical `..` component
is refused before normalization even if it would remain inside the repository.
Double-leading-slash roots, NUL/control/surrogate characters, paths over 4,096
UTF-8 bytes and paths over 128 components are refused. No tilde or environment
expansion occurs. Fixed relative input paths never introduce an absolute child
path or parent traversal. Regular hard-linked copies are allowed if their
captured bytes match; this interface does not attest an original filesystem inode.

The platform must expose POSIX descriptor-relative `open`, nonfollowing
descriptor-relative `stat`, and `O_NOFOLLOW`, `O_DIRECTORY`, `O_NONBLOCK` and
`O_CLOEXEC`. A missing capability produces `UNSUPPORTED_PLATFORM`; there is no
weaker path-opening fallback. The executed platform is Linux x86-64 / CPython
3.12.14. Other platforms have not been qualified.

For every file, the reader opens each ancestor relative to an already-open
directory descriptor. It opens the leaf without following symlinks and checks
`fstat` for a regular file and the exact expected size before issuing a read.
`O_NONBLOCK` permits rejection of a FIFO without waiting for a writer. Each
file receives one `os.read(fd, expected_size + 1)`, followed by another `fstat`.
Short reads, extra bytes, changed size, changed modification/change timestamps
and wrong SHA-256 refuse. Descriptors close on success and refusal.

This deliberately conservative single-read policy can refuse a short regular
file read even if a later read could finish it. There is no unbounded retry.
The buffer limit is the frozen size plus one, and the three historical inputs
remain well within C260's source and GLB limits. Kernel/filesystem stalls are
not a real-time deadline guarantee. The nonblocking and regular-file checks
specifically address nonregular input behavior such as FIFO waits.

Directory descriptors prevent a later pathname substitution from redirecting
an already-open ancestor or leaf. The admitted identities describe the captured
bytes, not a guarantee that all three paths retain those contents after return.
The operation does not claim an atomic filesystem snapshot, accepted source
revision, or protection against privileged filesystem remounts.

## Dependency capture and invocation

All three historical inputs must pass admission before the comparator is called.
The wrapper then captures all five dependency files using the same safe reader.
Dependency paths derive from the reader's own engineering directory, separately
from the supplied input repository. All five complete sizes and hashes must pass
before any captured Python module is compiled or loaded.

Simply loading the unchanged C267 module would leave a file-access gap: C267
and C266 reopen their dependencies through pathname-based readers after checking
them. C265 similarly loads C257 on first use. The Director approved a local
dependency-acquisition adapter to remove those reopenings:

1. Load each exact captured module into a fresh, uniquely named private module.
2. Set private C265 `_DEPENDENCY` to the captured C257 module.
3. Replace private C266 `_dependencies` with a function returning the captured
   source, artifact and identity modules.
4. Replace private C267 `_dependencies` with a function returning the captured
   binding, source and artifact modules.
5. Call the unchanged C267 `compare_hinges` function on the captured historical
   source and artifact buffers.
6. Remove every private module's `sys.modules` entry in `finally`.

These are the only runtime adaptations. Comparison, numeric conversion, source
observation, source/program/object association, field equality and refusal bodies
are unchanged. There is no persistent dependency cache or global modification
to imported predecessor modules. The wrapper performs fresh admission on every
call, including calls after previous success.

The dependency audit found no additional repository reads along this call path.
C267 uses C266/C265/C261 and validates C257; C266 uses C265/C261/C257; C265's
single loaded dependency is C257. C261 has no file loader. The invoked C257
lexical/module/occurrence functions do not read files; its separate historical
reader and command-line entry point are never called. Python's standard library
and the executing Python process remain trusted runtime prerequisites. Loading
the pinned observer code is distinct from executing the observed `.ok` program:
no product parser, evaluator, exporter, native application or model is invoked.

## Result and refusal contract

Success retains the complete C267 result, including nested records, site
associations, object bindings, source witnesses, artifact pointers and all
unqualified/false flags. The wrapper changes the outer schema to
`ontokin.c268.bound-hinge-endpoint/0.1`, retains the original schema in
`comparisonSchema`, sets `historicalInputsBound` to `True`, and adds `endpoint`
and `historicalAdmission`. The admission mapping has `main.ok`, `hinges.ok` and
`artifact` entries, each containing `path`, `bytes` and `sha256`.

Only the exact outer C267 limit sentence that denies historical admission is
replaced. Its replacement states that admitted historical bytes do not qualify
accepted revisions, edit atomicity or clean rebuild equivalence. All other
limitations remain verbatim. The first three source/artifact/comparison APIs
and all predecessor files remain unchanged.

Every refused call raises C268 `Fault`, a `ValueError` with predecessor-compatible
`code`, `detail`, `pointer`, `origin`, `sourceHashes`, `sourceBytes`,
`artifactSha256` and `artifactBytes`. An additional `reason` distinguishes the
bounded file-access cases. Refusals carry no qualified records or partial result.

| Code | Reason and interpretation |
| --- | --- |
| `ENDPOINT` | `ENDPOINT`: endpoint type or value is unsupported. |
| `INPUT_PATH` | `ROOT_TYPE`, `PATH`, `ESCAPE`, `SYMLINK`, `NOT_DIRECTORY`, `NOT_REGULAR`: invalid or unsafe path/type. |
| `INPUT_SIZE` | `SIZE`: initial file size differs from the frozen pin; no file content read occurs. |
| `HISTORICAL_BINDING` | `SHORT_READ`, `GROWN`, `CHANGED_DURING_READ`, `HASH`: captured bytes or observed file state fail admission. |
| `IO_ERROR` | `MISSING`, `PERMISSION`, `OPEN`, `STAT`, `READ`, or outer `IO`: host access failure. |
| `INPUT_BINDING` | The same bounded reasons for any dependency path/size/hash/I/O refusal, or unexpected pinned comparison schema/limit. |
| `RESOURCE_LIMIT` | `PATH_LIMIT`: declared path length/component bound exceeded. |
| `UNSUPPORTED_PLATFORM` | `CAPABILITY`: required safe descriptor facilities are absent. |
| Inherited C267 code | `COMPARISON`: predecessor refusal code, detail, pointer and source origin propagate. |
| `MALFORMED` | `INTERNAL_INPUT`: other bounded input/conversion exceptions at the public boundary. |

Available fault identities are deliberately partial evidence. Before a content
read, an observed byte count can come from `fstat` with no hash. After a read,
byte counts and SHA-256 describe the captured buffer, including a refused short
or extra-byte buffer. They do not label that buffer a complete admitted file.
Input files not reached by the call have no identity. A comparator/dependency
failure after historical capture retains all three input identities.

## Executed implementation checks

[check_candidate.py](evidence/implementation/check_candidate.py) is
implementation-author smoke/parity evidence, not independently authored
qualification. Its [RESULTS.json](evidence/implementation/RESULTS.json) records
the exact candidate and dependency hashes, command, interpreter, platform,
observed source head and outcomes.

Command:

`PYTHONDONTWRITEBYTECODE=1 python3 docs/engineering/localized-repair-c268/evidence/implementation/check_candidate.py`

The recorded run at source head `4595bade65291f36900be3e648c733aea74d5c40`
passed 10 checks with zero failures. Four successful calls cover both historical
endpoints and absolute/relative string/Path roots. Each result has eight hinges,
sixteen endpoint sites and one shared hinge definition. After reversing only
the documented outer result additions, every nested field equals a separately
called original C267 comparator result.

During all four wrapper calls, `Path.open` was patched to raise on use. Calls
still passed, confirming the inherited pathname dependency loaders are not
reopened on this path. Instrumented `os.read` observed exactly eight reads per
call: the three inputs plus five dependencies, each requested at its frozen size
plus one. No private C268 module entry remained afterward. Five invalid-argument
cases and a missing-`O_NOFOLLOW` capability injection returned the expected
typed refusals with no qualified output. The initial manual smoke also passed
both endpoints and three invalid arguments before the final recorded run.

The Director identified a resource-bound improvement during inspection: reject
excessive character length before scanning characters or encoding UTF-8. The
final candidate includes that correction. A separate
[oversized-path probe](evidence/implementation/PATH-BOUND.json) passed: a root
with 1,000,001 characters and a leading surrogate returned `RESOURCE_LIMIT`
before character validation. The 10-case smoke was rerun successfully after
this change. The earlier passing receipt and exact reader are retained as
[RESULTS-01.json](evidence/implementation/RESULTS-01.json) and
[the prior source snapshot](evidence/implementation/endpoint_reader-before-path-bound.py.txt).

No behavioral failure occurred in these implementation checks. The implementation
smoke program is 5,748 bytes, SHA-256
`57c1db791078f49b6a85af2fc4489d6e8d9fd12911e5e5bea1a4526adae1a663`.
The result receipt is SHA-256
`5c842d1e86a6f31a76fb7e7d11eb5fb6c335a130519754351d2c3dc8faab2a81`.

Independent controls own symlink/race/FIFO/permission/read-failure/dependency
mutation and changed-input coverage under R04. The Director owns the complete
affected cohort, exact-candidate independent review, documentation/workflow
checks, publication, actual-main verification and delivery. None is claimed
complete by this implementation report. No site/world alignment, full source or
glTF validity, accepted revision, invalid-edit atomicity, rebuild equivalence,
native behavior, model-trial result or comparative benefit is qualified here.
