# Independent P11 design-review preparation

This record precedes the author's frozen candidate. It records review criteria and
source observations, not an acceptance verdict or implementation.

## Source support

1. [Linux man-pages `ld.so(8)`](https://man7.org/linux/man-pages/man8/ld.so.8.html),
   read through the web tool on 2026-11-21. The documented dependency search distinguishes
   RPATH from RUNPATH: RPATH participates when RUNPATH is absent and can affect
   descendant searches; RUNPATH applies to direct dependencies. Environment, cache,
   defaults and hardware-capability directories also affect selection. `$ORIGIN`
   derives from the program or shared object's directory. Review consequence:
   preserving token text and substituting a directory is not proof of the selected
   dependency. A narrow absence-based proposal must justify all relevant candidate
   locations and retain the existing independent resolution rationale.
2. [glibc upstream origin discussion, March 2025](https://sourceware.org/pipermail/libc-alpha/2025-March/165143.html).
   This primary-source patch discussion identifies different historical origin
   derivation for normal execution and explicit loader invocation, particularly
   through aliases. It is not evidence that the patch is deployed on the selected
   host. Review consequence: do not treat a copied fixture's path, an invocation alias,
   an explicit-loader argument or a shared object's path as interchangeable with the
   selected executing Python's canonical origin.
3. [glibc upstream commit b14e1f9fcd3ca4dd86d0637f6e32e7bf642394da](https://sourceware.org/pipermail/glibc-cvs/2022q4/081599.html).
   This published source change uses `/proc/self/exe` for Linux executable-origin
   lookup. It supports a historical implementation fact; it does not independently
   authenticate current loader bytes or prove the current process namespace.

Direct retrieval of the proposed glibc-2.42 raw files from Sourceware and GitHub
failed through the web tool. Those attempts are not source verification. The
upstream discussion and commit were accessible. No alternate executable, loader,
`ldd`, shell or host runtime was invoked to resolve the documentation question.

## Inspected legacy boundaries

Exact source baseline: `e0119f376441fee0fc3956852ac63110ab141011`.

- `read_elf_metadata` refuses every dollar token in RPATH/RUNPATH by default. Its
  successful metadata contains raw `rpath` and `runpath` lists; both together are
  refused. It bounds ELF tables/strings, file identity and injected deadline checks.
- `_check_author_runtime` invokes that parser for the selected executing Python
  before helper imports, again after imports and during rechecks. A new rule that
  changes only resolution processing cannot resolve this earlier refusal.
- `_check_resolution` requires exact raw metadata equality, finite dependency
  inventories and existing literal search-path membership. Derived directories must
  remain distinct from raw metadata and receive the same closure/guard treatment.
- `_validate` and `_recheck` authenticate the relevant inputs and significant path
  components. Rechecks must not reuse a stale exemption or origin proof.
- Existing `_absolute` and alias guards reject unsafe normalization and unreviewed
  parent-traversal link targets. A new parent step cannot silently weaken them.
- P05/P07 contracts require a predeclared independently reviewed resolution map,
  fixed five-variable environment, bounded current source, unchanged command plans,
  P06 closed HOST/inspection schemas, and separate H0/H1/qualification/full-routine
  gates. Existing Python/JavaScript consumers and original methods stay protected.

## Candidate review criteria

The eventual exact candidate must state its version, opt-in selection and finite
image/token/context boundary. It must prove identity and origin without adopting
the caller's unverified string, retain raw metadata, and specify a single safe parent
step with complete no-symlink component checks. Any new path or absence evidence
must enter initial validation, loaded-runtime validation and before/after checks.

For a nonselecting search-path proposal, review the complete relevant dependency
name set, ordinary and hardware/TLS candidate locations, directory/symlink/special
entries, current alias identities and the outcome when a candidate exists. The
proposal must not claim unchanged selection merely from a correct expanded string.
Existing RPATH/RUNPATH semantics, independently reviewed resolution, strict defaults,
closed schemas, bounds and legacy refusal controls remain acceptance obligations.

Every future source/test/fixture/document change must be explicitly enumerated.
Controls must freeze exact bytes and independent expected outcomes before
implementation. Static fixture inspection can validate those bytes and internal
consistency; it cannot supply runtime passes or close host qualification.
