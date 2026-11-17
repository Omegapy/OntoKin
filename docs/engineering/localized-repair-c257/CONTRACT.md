# C257 finite ownership observation contract

C257 observes **immediate lifecycle ownership** for the existing public C210
family. It derives owners from actual authoritative `.ok` declaration
containment and independently reads ownership metadata from actual GLB bytes.
It does not infer an owner from a transform parent, `parent_frame`, follow,
hinge or physical connection. Those relations remain separate and unqualified.

The adopted [core ownership distinction](../../language-design/OK-LANG-001-core-language-specification.md)
and [construction identity/expansion rules](../../language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md)
govern interpretation. An ordinary part belongs to the containing object.
Each keyed generated part belongs directly to the collection's owner; the
collection is not an intermediate object. The existing
[C210 transport contract](../semantic-export-c210/CONTRACT.md) records owners
separately from its baked world transforms. No language semantics change.

## Independent and bounded inputs

The source observer reads the supplied `main.ok` and `hinges.ok` bytes. Its
tokenizer retains exact UTF-8 byte spans and ignores `//` line comments as syntax.
Supported ownership forms are scene root objects, classes, ordinary parts,
and generated parts over a direct `self` keyed parameter. That parameter's
final value must be a keyed literal or a module function that directly returns
a keyed literal. Literal key membership is read from source. Numeric/keyed
values are not evaluated. Final direct owner parameter overrides precede
class defaults. Nested ownership-shape overrides, dynamic key construction,
ambiguous/missing classes, unsupported composition and cycles refuse.

Class resolution follows the actual declaring module and import alias; an
imported private class is not silently treated as public. Full occurrence keys
and reused definition keys are distinct. The adopted canonical manifest rule
binds the actual source closure and program identity before artifact comparison.
Module definitions with omitted visibility are public under the adopted
construction rule. Repeated program/source identities and both mapping class
IDs must agree; source byte offsets require integer types.
The finite parser is not a general evaluator or a complete source-validity
checker. Unobserved dimensions, expressions, actions and relationships remain
unqualified even when ownership can be extracted.

## API authority

| Entry point | Result |
| --- | --- |
| `observe_source_ownership(source_files)` | Source-derived occurrence/definition keys, immediate owner keys and source byte witnesses. |
| `observe_glb_ownership(raw)` | Untrusted owner claims and their locations in GLB node metadata, source mappings and program occurrences. |
| `compare_ownership(source_files, raw)` | Exact source/program association and agreement of every owner claim with the independently derived source graph. |
| `read_bound_endpoint(repo, endpoint)` | The same observations after exact original `before`/`after` source and GLB byte admission. |

Raw supported source or metadata mutations are inspectable without pretending
that they are historical proof. The historical endpoint API alone requires
the original byte hashes. Contradictory, absent or ambiguous ownership fields
refuse; a display path alone cannot replace full identity association.

No API imports the product parser/evaluator, C255 expected semantics, C256
identity helpers or producer sidecars. It supplies no follow/hinge observations,
complete C255 `semantic` record, source build, accepted revision, clean rebuild,
invalid-edit atomicity, native/model trial or comparative score. All such
claims remain absent or explicitly false. No output permits execution.

## Verification and closure

Independent review must resolve source declaration/key spans and concrete
metadata locations; test source-only, artifact-only and supported coordinated
ownership changes; distinguish relationship/transform decoys; reject malformed
structures and resource excesses; and preserve every original failure.

## Finite resource profile

Each supplied source is nonempty UTF-8 and at most 65,536 bytes, with at most
8,192 tokens, 32 nested bracket levels and 32 top-level definitions per module.
The closure is exactly `main.ok` plus the pinned `example.hinges@1.0.0` source
named `hinges.ok`. A module has at most one scene; only the entry has a scene.
One literal keyed input has 1–64 unique keys. Expansion admits at most 128
objects and rejects recursive class containment. Source keys/text have at most
512 Unicode scalar characters; empty strings and control characters refuse.

GLB input is at most 4 MiB. It has exactly one JSON chunk of at most 2 MiB,
followed by one BIN chunk, with aligned lengths and an exact GLB 2 header.
There are 1–128 nodes and 1–128 program occurrence entries. Identity arrays
contain at most 32 nonempty components. Duplicate JSON keys and integer
lexemes longer than 64 characters refuse. Invalid shapes, malformed bytes
and excessive parser recursion become explicit `Fault` refusals. The reader
does not evaluate geometry buffers or claim complete glTF validity.

The historical file API checks the exact expected file size before reading,
reads at most that size plus one byte, then checks the complete SHA-256. It
rejects symbolic-link files and paths escaping the supplied repository.
Source and artifact APIs accept already supplied `bytes`; they do not fetch
files, invoke another parser or execute an expression.

## Closure

After reviewed integration and required actual-main checks, verify and save
one successor handoff, then stop. Follow and hinge work is a later scope.
