# C199 independent dependency and contract preflight

## Result

Byte-only preflight passed **3,455 assertions**. No Blender process, export,
receiving process, simulation, render or native qualification attempt started.
This is preparatory dependency evidence, not implementation qualification.

The inspected repository head was
`0e1ef6a64e78d8478f40cbc2d2f25238014e8825`, tree
`962dd185271ffe1a197a4046073dd16bb3009d87`.
`BYTE-PREFLIGHT.json` and `BYTE-CHECKS.json` contain the detailed result.

## Preserved contract and source bindings

- All nine normative C198 files match INPUT-FREEZE sizes and SHA-256 hashes.
- The canonical file-list digest matches; all 39 control definitions remain.
- All 104 BASELINE-INPUTS bindings match the specified historical commit,
  including file length, SHA-256, Git blob and mode.
- All 13 DEPENDENCIES source bindings match the specified historical commit.
- Current baseline differences are restricted to STATUS.md, which correctly
  records the later integrated C198 checkpoint. All other baseline files and
  all dependency source files match their historical pinned content.
- INPUT-FREEZE SHA-256 is
  `86e1476851c7e3ed14b6e9f4674375bc683e891bfc5037c2727dfc3b15557231`.

## Exact native dependency

The existing official archive was found at
`/workspace/scratch/efc86516cbb7/deps/blender-4.5.3-linux-x64.tar.xz`.
It is exactly 377,397,328 bytes, SHA-256
`975c58fcb244273838534bba771e64ad87739216b0f9b39a888531a49a72d845`.
The executable SHA-256 matches
`5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397`.
The default `/usr/bin/blender` has a different hash and is not eligible.

The existing extracted bundled Python and glTF files were independently
compared against archive contents: **3,321 files matched**. The observed
bytecode files are already contained in the official archive; no extra cache
files were found in those selected component inventories.

A fresh extraction was then made at
`/workspace/scratch/801d9d641f68/deps/blender-4.5.3-linux-x64`.
The archive was hashed again before extraction. Extraction used a new target,
one exact root, a 20,000-member and 2 GiB content ceiling, Python's data filter,
and explicit rejection of traversal, special devices and outward links.
The resulting 6,510 members include 5,579 regular files totaling
1,168,277,492 bytes. Every regular file is byte-hashed in
`CLEAN-DISTRIBUTION-INVENTORY.json`; component inventories separately identify
the bundled Python and glTF files. The new executable again matches its pin.
`CLEAN-DEPENDENCY-INSTALL.json` records installation and disk-space evidence.

The host is Linux x86-64 with CPython 3.12.14. Its executable is
`/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12`,
SHA-256 `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`.
`HOST-PREFLIGHT-LOADED-MODULES.json` covers only modules used by this preflight;
the actual implementation still needs its own transitive module closure.

## Static operator property evidence

`BLENDER-OPERATOR-PROPERTIES.json` records AST-derived declarations from the
pinned glTF add-on and inherited `bpy_extras.io_utils` helpers. No add-on code
was imported or executed.

The exporter declares **108 properties**, of which 106 have explicit literal
defaults. `filepath` and `ui_tab` have no declared default. The importer declares
**19 properties**, of which 15 have explicit literal defaults; `filepath`,
`directory`, `files` and `loglevel` omit their defaults. The raw declared-default
maps preserve this distinction.

The proposed `STATIC-TRAY-EXPORT-PROPERTY-MAP.json` and
`STATIC-TRAY-IMPORT-PROPERTY-MAP.json` cover every declared inherited property.
They include explicit static-profile overrides, UI values and a documented
per-attempt filepath template. The integrator must review and bind these exact
maps and their resolved path policy in the executable lock. They are not a
dynamically observed RNA dump. The first qualified native start must check
the expected Blender version/build and runtime RNA property coverage before
construction or import; a mismatch consumes that slot and rejects it.

## Exploratory observation retained

An early exploratory script incorrectly treated absence of readable version
and build strings in the executable as failed gates. Those unsuccessful
string searches and the original result are retained as `EXPLORATORY-*`.
They do not contradict the exact archive and executable SHA-256 matches.
The adopted byte requirements passed. Runtime version/build confirmation
remains deferred to the first permitted native slot. The initial verifier also
had an archive-path suffix construction error before any archive operation;
its repaired source uses the complete explicit archive filename.

## Remaining gate

C199 must still implement and seal the two source routes, shared worker,
independent reader/corruptor, receiver, supervisor and complete fixtures.
Their exact source, dependency, command and setting closure requires independent
approval before the twelve-slot native schedule. The first unexpected result
stops the schedule; failed starts consume slots. The current preflight cannot
authorize a retry or substitute native evidence. Later tray admission and
timed author work remain separate.
