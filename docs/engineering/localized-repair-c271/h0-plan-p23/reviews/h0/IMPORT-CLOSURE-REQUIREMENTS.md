# Unfinished author-import requirement reference

This source-only investigation began before the ldd candidate-path blocker. It is retained for continuation; it is not a collector, an approved observation plan or an operational runtime inventory. No import-closure collector ran in P23.

## Direct standard-library roots

The frozen inspector and its actual H0 helper-import graph declare **34** distinct direct modules:

`__future__, argparse, ast, collections.abc, contextlib, copy, ctypes, dataclasses, datetime, errno, fnmatch, fractions, hashlib, importlib, importlib.metadata, json, math, os, pathlib, platform, re, selectors, shlex, shutil, signal, stat, struct, subprocess, sys, tarfile, tempfile, time, types, uuid`.

The earlier 33-name advisory omitted `__future__`. Although it is a compiler directive, its statement still emits a runtime import. A one-line inert snippet was compiled and disassembled without execution to confirm that fact. No project source was compiled or executed.

The JSON record retains exact source hashes and all import statements with their function scopes. The inspector's `_load_helpers` is the selected local import route. Other provider, native/checker, reader and force-agent dynamic imports are outside that static H0 route. An initial data-extractor omission of `importlib.metadata` was caught by set comparison and corrected before final artifact creation; this was not a product failure.

## Finite native-image roots

A future separately reviewed observation should record the selected Python and only native extension modules actually loaded by these finite stdlib imports, with their actual mapped native dependencies. Retain file-backed, cached-bytecode, builtin and frozen distinctions. Exact extension paths cannot be inferred from import names alone; they were not observed here.

`ctypes` is a real top-level dependency and has native bootstrap behavior. Any future collector must declare it explicitly. Importing `subprocess` is required source input; launching through it is a separate action and is outside a raw import observation.

This import-derived set still excludes other necessary H0 roots: pinned Node, PATH-selected Git, ldd's actual interpreter and possible external commands, present literal RTLD candidates and their transitive dependencies. It is not a complete ELF closure. Normal argparse construction and lazy stdlib imports also need source review before the runtime manifest can be called complete.

No arbitrary environment or installed-wheel sweep follows from this source reference. P23 technical work is stopped at the concrete candidate-path blocker; preserve this unfinished prerequisite for a later authorized phase after the required path model is resolved.
