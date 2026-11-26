#!/usr/bin/env python3
"""N34-M: render N34-M-REVIEW.md and N34-M-REVIEW.json from one source (worker W1, C271-P35).

Inputs: the raw outputs of n34m_reader.py, n34m_compare.py (runs 02 and 03) and n34m_git_scan.py,
and the reviewed documents (hashed only). The narrative below and the tables generated from the
raw outputs give both forms the same content. It starts nothing and writes exactly the two review
files, by exclusive creation. Paths carry the labels <worktree>, <local> and <prefix>.

Run:  <venv>/bin/python -I -S -B n34m_report.py --dir OUT --worktree WT --local LOCAL --prefix PREFIX
"""
import argparse
import collections
import hashlib
import json
import os
import sys

REVIEWED = (
    "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md",
    "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.json",
    "docs/engineering/localized-repair-c271/macos-implementation-p33/AMENDMENT-001.md",
    "docs/engineering/localized-repair-c271/macos-implementation-p33/AMENDMENT-001.json",
    "docs/engineering/localized-repair-c271/macos-implementation-p33/interfaces/W3-OBSERVER.md",
    "docs/engineering/localized-repair-c271/macos-implementation-p33/DIRECTOR-DECISIONS.md",
    "docs/engineering/localized-repair-c271/macos-qualification-p35/MH-PLAN.md",
    "docs/engineering/localized-repair-c271/macos-qualification-p35/PHASE.json",
    "docs/engineering/localized-repair-c271/macos-preparation-p34/reviews/RESULT-REVIEW-001.json",
    "prototypes/static_tray_v01/current_host_observation_v02.py",
)
SCRIPTS = ("n34m_reader.py", "n34m_compare.py", "n34m_git_scan.py", "n34m_report.py")
RAW = ("raw-reader-02.json", "raw-compare-02.json", "raw-compare-03.json", "raw-git-scan-02.json",
       "superseded-run-01/raw-reader-01.json", "superseded-run-01/raw-compare-01.json")
FRAMEWORK = "<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12"
VENV = "<worktree>/.venv"
NODE = "<local>/c271-macos/node-v24.22.1-darwin-arm64/bin/node"

SHORT = {"LC_SEGMENT_64": "SEG", "LC_DYLD_INFO_ONLY": "INFO", "LC_DYLD_CHAINED_FIXUPS": "FIXUPS",
         "LC_DYLD_EXPORTS_TRIE": "EXPORTS", "LC_SYMTAB": "SYMTAB", "LC_DYSYMTAB": "DYSYMTAB",
         "LC_LOAD_DYLINKER": "DYLINKER", "LC_UUID": "UUID", "LC_BUILD_VERSION": "BUILD", "LC_SOURCE_VERSION": "SRC",
         "LC_MAIN": "MAIN", "LC_LOAD_DYLIB": "DYLIB", "LC_ID_DYLIB": "ID", "LC_RPATH": "RPATH",
         "LC_FUNCTION_STARTS": "FSTARTS", "LC_DATA_IN_CODE": "DIC", "LC_CODE_SIGNATURE": "CS"}


def sha256_of(path):
    data = open(path, "rb").read()
    return hashlib.sha256(data).hexdigest(), len(data)


def compact(names):
    """LC_SEGMENT_64 x4, ... in order, runs collapsed."""
    out = []
    for name in names:
        short = SHORT.get(name, name)
        if out and out[-1][0] == short:
            out[-1][1] += 1
        else:
            out.append([short, 1])
    return " ".join(name if count == 1 else "%s×%d" % (name, count) for name, count in out)


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def code(text):
    return "`" + text + "`" if text else ""


def strip_command(row):
    out = {key: value for key, value in row.items() if key not in ("classic_loader_h", "sections")}
    if "sections" in row:
        out["sections"] = [section["segname"] + "," + section["sectname"] for section in row["sections"]]
    return out


# ---------------------------------------------------------------------------
# Narrative (one source for both forms)
# ---------------------------------------------------------------------------

VERDICT = "ACCEPT_WITH_NONMANDATORY_FINDINGS"

SUMMARY = [
    "`bin/node` meets every rule of contract section 7. All 111 Mach-O images of the interpreter installation "
    "(79 in the framework version directory, 27 in the `.venv`, 5 external dependencies) meet section 4's rules. "
    "P33-AMENDMENT-001 (design revision 4) changes neither section.",
    "The parser under review accepts all 112 files, and its parse agrees field for field with the independent "
    "reader's. Its Python inventory equals the reader's listing entry for entry and equals MP's after-snapshot "
    "(`c277bdd3…`). M0's Mach-O and Python-installation checks would pass on this host as the files stand.",
    "The closure claim holds for these files within its stated limits. Every non-system reference resolves to a "
    "bound file, and every system reference is absent from disk and present in the image table of the OS "
    "cryptex's dyld shared cache.",
    "D-16: `bin/node` links CoreFoundation by a plain `LC_LOAD_DYLIB` (command 14).",
    "Nine nonmandatory findings, N-01 to N-09. None blocks the adoption of an execution plan.",
]

ANSWERS = collections.OrderedDict()
ANSWERS["a"] = {
    "question": "Does every file meet the contract's rules (thin 64-bit arm64, file type, the closed allow-list, "
                "LC_LOAD_DYLINKER /usr/lib/dyld, dylibs only under /usr/lib/ or /System/Library/; any LC_RPATH, "
                "LC_DYLD_ENVIRONMENT, upward or re-export dylib, @-relative path or unknown command refuses), and do "
                "the Python images meet section 4 as amended?",
    "answer": "Yes, both.",
    "points": [
        "**bin/node, section 7.** It is thin, `MH_MAGIC_64`, `CPU_TYPE_ARM64`, cpusubtype `0x00000000` and "
        "`MH_EXECUTE`. Its 21 commands are of 14 kinds, all inside the 16-command allow-list: `LC_SEGMENT_64` ×5, "
        "`LC_DYLD_CHAINED_FIXUPS`, `LC_DYLD_EXPORTS_TRIE`, `LC_SYMTAB`, `LC_DYSYMTAB`, `LC_LOAD_DYLINKER`, `LC_UUID`, "
        "`LC_BUILD_VERSION`, `LC_SOURCE_VERSION`, `LC_MAIN`, `LC_LOAD_DYLIB` ×4, `LC_FUNCTION_STARTS`, "
        "`LC_DATA_IN_CODE` and `LC_CODE_SIGNATURE`. The two kinds it does not use are `LC_LOAD_WEAK_DYLIB` and "
        "`LC_DYLD_INFO_ONLY`. `LC_LOAD_DYLINKER` is `/usr/lib/dyld`. "
        "The four dylibs are CoreFoundation, Security, `/usr/lib/libc++.1.dylib` and `/usr/lib/libSystem.B.dylib`, "
        "all normalized absolute paths under `/System/Library/` or `/usr/lib/`. No `LC_RPATH`, "
        "`LC_DYLD_ENVIRONMENT`, upward, re-export, weak or lazy dylib, no `@` path and no unknown command occurs. "
        "There are no structural anomalies.",
        "**Python images, section 4** (unchanged by the amendment, whose 17 replaced clauses concern only the "
        "supervisor, MC14, MC37 to MC39, the labels and trust assumption 2). All 111 images are thin "
        "`MH_MAGIC_64` arm64 with cpusubtype 0. Their file types are `MH_EXECUTE` (2: `bin/python3.12` and "
        "`Resources/Python.app/Contents/MacOS/Python`), `MH_DYLIB` (25) and `MH_BUNDLE` (84). "
        "Every command is of a kind in Node's allow-list, or `LC_ID_DYLIB` (25 times) or `LC_RPATH` (81 times). "
        "None carries "
        "`LC_DYLD_ENVIRONMENT`, `LC_LOAD_UPWARD_DYLIB`, `LC_REEXPORT_DYLIB`, `LC_LAZY_LOAD_DYLIB` or an unknown "
        "command. Both executables name `/usr/lib/dyld`.",
        "**Python references.** There are 162, all `LC_LOAD_DYLIB` (no weak reference):",
        "- 127 system references to 11 distinct paths (13 with Node's two others);",
        "- 9 absolute non-system references: the launcher and the process image name the framework's `Python` library by its `<prefix>/Cellar/…` path, the lib-dynload modules name five external libraries through `<prefix>/opt/…` links, and libssl names libcrypto by its versioned path. Each resolves to a bound regular file;",
        "- 26 `@loader_path` references, all from Pillow's 8 extension modules and its bundled `.dylibs`. Each "
        "resolves to a bound image in the `.venv`;",
        "- 0 `@rpath`, 0 `@executable_path` and 0 other `@` forms.",
        "**`LC_RPATH`.** The 81 entries are `<prefix>/lib` (78), the sqlite library's own lib directory, libmpdec's "
        "`@loader_path/../lib` (resolved as a directory from both of its spellings), and an absent build-machine path "
        "in Pillow's libjpeg (N-06). Every entry is recorded.",
        "**Contrast.** Node's own rules would refuse every Python image: 109 by file type, and both executables "
        "because of a non-system reference, with an `LC_RPATH` in the process image. That is why section 4 has rules "
        "of its own.",
    ],
}
ANSWERS["b"] = {
    "question": "D-16: does bin/node link CoreFoundation, and how?",
    "answer": "Yes, by a plain LC_LOAD_DYLIB.",
    "points": [
        "Command {index}, at file offset {offset}, is `cmd {cmd}`: `LC_LOAD_DYLIB`, not `LC_LOAD_WEAK_DYLIB` "
        "`0x80000018` and not a lazy, upward or re-export command. Its cmdsize is {cmdsize}, its name offset "
        "{name_offset} and its timestamp {timestamp}. It names `{path}`, current version {current} and "
        "compatibility version {compatibility}. It is the first of the four dylib commands.",
        "The path does not exist on disk. It is an image of the cryptex's dyld shared cache "
        "(UUID `F2E86C53-6052-388B-BA71-5A0C9B569413`).",
        "The parser's own parse gives the same command, and `check_node_macho` returns it as the first reference. "
        "HOST's `runtime.macho` will therefore carry it.",
        "dyld must load CoreFoundation and run its initializers before `main`, and a failed load stops the start.",
        "Under D-16 and MH-PLAN section 6, MC36 stands as written. The load command does not show that "
        "`__CF_USER_TEXT_ENCODING` then appears in the probe's `process.env` (N-04).",
    ],
}
ANSWERS["c"] = {
    "question": "W3's Q3: is every cpusubtype CPU_SUBTYPE_ARM64_ALL? Is any file arm64e or fat?",
    "answer": "Every bound file is CPU_SUBTYPE_ARM64_ALL, and none is arm64e or fat.",
    "points": [
        "All 112 files have cputype `0x0100000c` and raw cpusubtype `0x00000000`: subtype value 0 and capability "
        "bits (mask `0xff000000`) 0. These are `bin/node`, the 79 framework images, the 27 `.venv` images and the "
        "5 external dylibs. None is `CPU_SUBTYPE_ARM64E` (2) or `CPU_SUBTYPE_ARM64_V8` (1), and none has "
        "`CPU_SUBTYPE_PTRAUTH_ABI`.",
        "None is fat. This Python framework build is thin arm64, not universal2. No file in either tree begins "
        "with a fat magic, a Java class magic or an `ar` archive magic.",
        "The only fat files met lie outside the parsed set:",
        "- the developer tools' Git: x86_64 subtype 3 and arm64 subtype 0;",
        "- `/usr/lib/dyld`: x86_64 subtype 3 and arm64 subtype `0x80000002`, that is arm64e with `CPU_SUBTYPE_PTRAUTH_ABI`.",
        "The parser's rule, exactly 0, accepts every bound file. In-memory cases N06 to N09 confirm that it "
        "refuses subtypes 1, 2, `0x80000000` and `0x80000002`.",
    ],
}
ANSWERS["d"] = {
    "question": "W3's open questions checked against the real files: fat files refused; @rpath stricter than dyld; "
                "MH_OBJECT refused; the Git version checked by grammar only.",
    "answer": "None of them refuses a real file, and each outcome is correct under the contract.",
    "points": [
        "**Fat files (Q1).** No bound file is fat, so the rule refuses nothing here. For Node the rule is the "
        "contract's (\"thin\"). For Python images it is an implementation rule, since section 4 does not say thin "
        "(N-05). It fails closed. The developer tools' Git is fat, but M0 binds Git by bytes and never parses it. "
        "`_macho_extent` on Git's first bytes returns `MACHO-FAT`, which confirms W3's F3. This is correct: the "
        "contract sets no Mach-O rule for Git.",
        "**`@rpath` stricter than dyld (Q4).** No bound image carries an `@rpath` reference, so the rule is never "
        "exercised. Neither are the related rules on weak references and leaf names. The real files are accepted.",
        "  - The 81 `LC_RPATH` entries take no part in load-time resolution. The parser records their state, "
        "fail closed (N-06).",
        "  - rpds's `LC_ID_DYLIB` is `@rpath/rpds.cpython-312-darwin.so`. That is an install name, not a reference, "
        "and section 4 sets no rule for it (N-01 (d)).",
        "  - The rule is correct under section 4's \"by dyld's rules with the recorded rpaths\" as a stricter subset. "
        "N-01 (b) notes the one case in which a subset rule could bind another file than dyld loads. It does not "
        "occur here.",
        "**`MH_OBJECT` (Q5).** No file in either tree is `MH_OBJECT`. `config-3.12-darwin/` holds no `python.o`, and "
        "its `libpython3.12.a` and `libpython3.12.dylib` are links to the framework's `Python`. There is no `ar` "
        "archive. Nothing is refused. The rule follows section 4's accepted types, so it is correct.",
        "**Git version by grammar (Q6).** This is not a Mach-O rule. The contract binds Git by path and SHA-256 and "
        "states no expected version, and the pinned bytes determine the version.",
        "  - The developer tools' Git embeds `2.50.1 (Apple Git-155)` and the format `git version %s` in its arm64 "
        "slice. One `--version` start should therefore print `git version 2.50.1 (Apple Git-155)\\n`, which "
        "`GIT_VERSION_LINE` admits. This is a static prediction: no Git was started.",
        "  - The grammar-only check is correct under the contract. Both of that Git's slices reference only five "
        "system libraries, all images of the cache, so E18's premise holds for that file (N-07).",
    ],
}
ANSWERS["e"] = {
    "question": "Does the parser's source decide each rule as the contract says (bounds checks, truncated or "
                "overlapping commands, cmdsize alignment, LC_REQ_DYLD bits, string offsets, any command skipped "
                "without checking)?",
    "answer": "Yes. It decides every contract rule as the contract states. It adds stricter rules (N-05), and its "
              "reference resolution has edge cases (N-01) that do not arise here. Some recorded properties are not "
              "decided (N-02).",
    "points": [
        "**Header** (`_macho_extent`, lines 733–741; `parse_macho`, 825–849):",
        "- Only `cf fa ed fe` passes. The four fat magics give `MACHO-FAT`; the 32-bit and big-endian magics give `MACHO-MAGIC`.",
        "- At least 32 bytes are present before any unpack.",
        "- cputype and cpusubtype must match exactly.",
        "- 0 < ncmds ≤ 4096, 0 < sizeofcmds ≤ 4 MiB, and 32 + sizeofcmds ≤ the file size.",
        "**Command table:**",
        "- Each command header lies inside the table; cmdsize is at least 8, a multiple of 8 (the 64-bit rule) and inside the table.",
        "- The sizes must add up to sizeofcmds exactly. Commands are read in sequence, so they cannot overlap, and a truncated, short or padded table refuses (N11 to N21).",
        "- The parsed bytes are the hash-bound bytes. `read_macho` takes them from the same read that computes the digest, and reads again with a binding comparison when the table exceeds 64 KiB.",
        "**`LC_REQ_DYLD`:** names map from full 32-bit values (lines 195–212). A known code with a missing or an extra `LC_REQ_DYLD` bit is unknown and refuses (N36, N37, N44, N47). The table equals the reader's independent table for 0x1 to 0x36.",
        "**Strings** (`_lc_string`, 748–756): the offset must lie at or after the fixed structure and inside the command; the NUL must lie inside the command; the string must be non-empty and printable ASCII (N22 to N26).",
        "**Per-command structure:** every command that either rule set can accept is size-checked and range-checked:",
        "- `LC_SEGMENT_64`: exactly 72 + 80·nsects, and the file range inside the file;",
        "- `LC_SYMTAB`: symbol and string ranges;",
        "- `LC_DYSYMTAB`: size only;",
        "- `LC_UUID`, `LC_SOURCE_VERSION` and `LC_MAIN`: exact sizes; the entry offset inside the file;",
        "- `LC_BUILD_VERSION`: exactly 24 + 8·ntools;",
        "- the linkedit-data commands and `LC_DYLD_INFO_ONLY`: exact sizes and ranges;",
        "- the dylib, dylinker and rpath commands: the string checks above.",
        "**Skipped commands:** unknown commands, and known commands outside both allow-lists, are recorded undecoded (`name` null, or the name alone). Both rule sets refuse every such command, so no command is accepted unchecked (N39 to N49, P12 to P16).",
        "**Rules against the contract:**",
        "- The parser's Node allow-list, its refused list and its Python additions and file types equal CONTRACT.json's lists exactly.",
        "- `check_node_macho` (884–901) refuses the four named commands and anything outside the 16, requires `/usr/lib/dyld`, refuses any `@` in a dylib reference, and requires a normalized absolute path under the two prefixes. All other path-carrying commands are outside the list.",
        "- `check_python_macho` (911–951) and `_closure_pass` (1209–1299) apply section 4: the three file types; the allow-list plus `LC_ID_DYLIB` and `LC_RPATH`; refusal of `LC_DYLD_ENVIRONMENT`, `LC_LOAD_UPWARD_DYLIB`, other `@` forms and unknown commands; `@`-relative `LC_RPATH` entries resolved as directories; and every non-system reference resolved to a bound image, with the link hops recorded.",
        "**Mutation cases:** 64 Node cases and 17 Python cases on the real header bytes, in memory, all with the predicted outcome (section 5). N58 to N63 show the undecided properties of N-02.",
    ],
}
ANSWERS["f"] = {
    "question": "Does the closure claim hold for these files within its stated limits, and what does it not cover?",
    "answer": "It holds for these files. Its limits are as stated, plus the items listed here.",
    "points": [
        "**Node:** the bytes are bound (SHA-256 `6f320694…`, 122,545,856 bytes, `0o755`, one link) and equal the "
        "NODE-SOURCE.json pin. All 21 load commands were read. Its four dependencies are system paths that do not "
        "exist on disk and are images of the cache.",
        "**Interpreter installation:** the inventory (digest `c277bdd3…`, 776,209 canonical bytes) binds:",
        "- 3,478 + 297 files, 305 + 45 directories and 5 + 3 links;",
        "- the 4-hop selection chain and pyvenv.cfg's `home`;",
        "- 111 images, among them the 5 external dylibs, and 6 closure link hops.",
        "All 35 non-system references resolve to bound images. The 11 distinct system paths of the Python images "
        "are absent from disk and present in the cache's image table.",
        "**System side:** the cache is the cryptex's `dyld_shared_cache_arm64e`: header magic `dyld_v1  arm64e`, "
        "osVersion 26.6.0, 3,649 images and 12 subcaches. The OS identity is macOS 26.6.2 (25G83), and the system "
        "and cryptex SystemVersion.plist files are byte-identical. The limits stated in sections 7 and 12 hold: "
        "the cache images are identified by OS identity, not by per-file hashes, and the SSV, SIP and the cryptex "
        "delivery are assumed, not verified.",
        "**Not covered by the claim, beyond its stated limits:**",
        "- the per-file identity of the cache images and of the dynamic linker `/usr/lib/dyld`. dyld is an on-disk "
        "system-volume file that is also a cache image; the claim does not name it, and HOST does not record the "
        "cache UUID (N-03);",
        "- whether a reference under `/usr/lib/` or `/System/Library/` is a cache image at all: the prefix rule "
        "does not ensure it, and seven `/System/Library` subtrees are firmlinked to the data volume (N-03);",
        "- code signatures. `LC_CODE_SIGNATURE` is range-checked only. Validity and AMFI enforcement are runtime "
        "behaviour;",
        "- run-time loads by the libraries' own logic: OpenSSL's providers, engines and configuration; "
        "CoreFoundation's and Security's plug-ins; libuv's `dlopen` for file-system events in Node; ctypes in Python; "
        "`dlopen(\"@rpath/…\")` searches through the recorded rpaths, including `<prefix>/lib` from the process "
        "image (N-06);",
        "- dyld's default fallback directories (`/usr/local/lib`, `/usr/lib`) for a dependency that disappears "
        "between the last recheck and a load. That is the time-of-use limit of any static binding; MC29 detects "
        "the change afterwards;",
        "- files that are not Mach-O and are read at run time outside the trees: zoneinfo, locale data, "
        "`~/.CFUserTextEncoding`, OpenSSL's configuration;",
        "- the base installation's global site-packages, the target of the framework's `lib/python3.12/site-packages` "
        "link. It is recorded as a link target only. It is not on `sys.path` under `-I -S`, and it is excluded in "
        "the venv by `include-system-site-packages = false`;",
        "- symbol binding at run time. Extension modules resolve Python's API by dynamic lookup in already-loaded "
        "images, and interposition is runtime behaviour;",
        "- Git's dependencies. They lie outside the parser, and this review checked them statically for the "
        "developer tools' Git only (N-07).",
    ],
}
ANSWERS["g"] = {
    "question": "Would the parser accept or refuse the real files? If it would refuse, why, and is the cause the "
                "parser, the contract or the files?",
    "answer": "It accepts them. No cause of refusal exists in the parser, the contract or the files.",
    "points": [
        "**Node.** `read_macho` with the NODE-SOURCE pin and `private=True`, then `check_node_macho`, as "
        "`check_runtime` calls them: accepted.",
        "**Images.** `check_python_macho` on each of the 111 images: accepted.",
        "**Inventory.** `python_inventory(<worktree>/.venv, <framework version directory>)`: accepted, "
        "digest `c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633`. A second computation, and run 03 "
        "after all other work, give the same digest and no `compare_inventory` difference. The digest equals MP's "
        "`python_inventory_after_sha256`.",
        "**Packages.** `verify_packages` finds exactly the seven pins, with every RECORD row verified.",
        "**Launcher.** `check_launcher` accepts this review's own `-I -S -B` process, started as "
        "`<worktree>/.venv/bin/python`: process image `Resources/Python.app/Contents/MacOS/Python`, `sys.path` "
        "inside the framework.",
        "So M0 would not fail on this host for any Mach-O or Python-installation reason, as the files stand on "
        "2026-11-26.",
        "**What would make it refuse later.** Each of these is a change of state, not a defect in the parser, the "
        "contract or the files:",
        "- a start of the framework interpreter that writes bytecode (N-09, MC32);",
        "- a retargeted `<prefix>/opt` link or a changed external library;",
        "- the creation of `/Users/runner` (N-06);",
        "- an OS update.",
    ],
}

FINDINGS = [
    {
        "id": "N-01", "severity": "nonmandatory",
        "title": "Reference resolution: edge cases in which the bound file and dyld's could differ",
        "location": "current_host_observation_v02.py `_closure_pass` (lines 1209–1299: 1227, 1247, 1260), "
                    "`_search_directory` (1177–1189), `check_python_macho` (911–951)",
        "issue": [
            "(a) For an `@loader_path` reference, the parser checks every spelling of the loader, but records only "
            "the lexicographically first resulting spelling of the target (`sorted(outcomes.items())[0]`, line 1260). "
            "A target reached through several loader spellings has its own `@loader_path` references checked from "
            "its canonical directory and that one spelling only.",
            "(b) For `@rpath`, the parser selects the first candidate that exists (line 1247). dyld skips a "
            "candidate that exists but does not load, and goes on to the next one, which the parser never bound. "
            "Examples are a file built for another platform or a newer OS, a file that is not a dylib, and a file "
            "whose signature is invalid.",
            "(c) `@executable_path` in a non-executable image is resolved against the process image's directory "
            "(line 1227). Before the launcher re-executes, dyld resolves it against the launcher's directory.",
            "(d) No rule applies to `LC_ID_DYLIB` values; rpds's is `@rpath/rpds.cpython-312-darwin.so`. dyld can "
            "treat an already-loaded image whose install name matches a requested path as that dependency.",
        ],
        "effect": "None of these arises in the real files:",
        "effect_points": [
            "no bound image has an `@rpath` or `@executable_path` reference;",
            "each of the 26 `@loader_path` references comes from an image with a single spelling;",
            "the launcher's only non-system reference is absolute;",
            "no install name equals a reference that resolves to another file, and no install name is a cache path. "
            "The reader's collision check finds only the five externals' own names, each resolving to the same file.",
        ],
        "recommendation": "Not needed for this host's plan. If a later plan binds a tree with `@rpath` references, "
                          "symlinked Mach-O files or several rpaths, the implementation should first:",
        "recommendation_points": [
            "record every spelling;",
            "refuse when an earlier existing candidate is not a loadable image of the accepted type;",
            "check every install name against every reference.",
        ],
    },
    {
        "id": "N-02", "severity": "nonmandatory",
        "title": "Structural properties recorded but not decided",
        "location": "`_command` (763–822); the `parse_macho` docstring (826–832); W3-OBSERVER section 6.1",
        "issue": "The parser does not decide these properties: section file ranges, `LC_DYSYMTAB` offsets, segment "
                 "overlap and order, duplicate segment names, `LC_BUILD_VERSION` platform and minimum OS, header "
                 "flags and code-signature validity. Yet its docstring says it refuses \"every structural "
                 "inconsistency\". Cases N58 to N63 are accepted, as the source predicts.",
        "effect": "No contract rule depends on these properties, and the bytes are pinned. The reader checks section "
                  "and indirect-symbol ranges and segment overlap, and finds no anomaly in the 112 files. Every "
                  "platform is macOS. Every minimum OS is at most 26.0: Node 13.5, Pillow 11.0, the framework and "
                  "the externals 26.0. No file sets `MH_FORCE_FLAT` or `MH_ALLOW_STACK_EXECUTION`.",
        "recommendation": "In a later implementation phase, narrow the docstring and W3-OBSERVER section 6.1 to the "
                          "checks made, or add the checks.",
    },
    {
        "id": "N-03", "severity": "nonmandatory",
        "title": "The system side of the closure claim holds here, but rests on facts that M0 does not record",
        "location": "CONTRACT.md section 7 (load commands, closure claim) and section 4 (claim); `_closure_pass` "
                    "line 1235",
        "issue": [
            "A normalized path under `/usr/lib/` or `/System/Library/` is treated as an OS library identified by "
            "the OS build, and is not resolved.",
            "On this host every such reference is absent from disk and present in the image table of the "
            "cryptex's main cache file. That covers the 13 distinct paths of the bound files, Node's four among "
            "them, and the five of the developer tools' Git. The main cache file is `dyld_shared_cache_arm64e`: "
            "SHA-256 `7a024959…`, 573,440 bytes, UUID `F2E86C53-6052-388B-BA71-5A0C9B569413`, osVersion 26.6.0, "
            "3,649 images.",
            "The prefix rule does not ensure this by itself. `/usr/share/firmlinks` maps seven `/System/Library` "
            "subtrees onto the writable data volume: Caches, Assets, PreinstalledAssets, AssetsV2, "
            "PreinstalledAssetsV2, `CoreServices/CoreTypes.bundle/Contents/Library` and Speech. An on-disk file "
            "under either prefix is not a cache image either.",
            "The dynamic linker `/usr/lib/dyld` is on disk: fat, x86_64 and arm64e, SHA-256 `373fce2b…`. It is "
            "also a cache image, and the header's dyld-in-cache fields are set. It is not hashed, and the claim "
            "names only \"system libraries\".",
        ],
        "effect": "None for these files. Every reference is a cache image, and no reference lies under a "
                  "firmlinked subtree.",
        "recommendation": "Three changes would strengthen the claim; none is needed for this plan:",
        "recommendation_points": [
            "HOST records the main cache file's digest and UUID, and each system reference's membership in its "
            "image table. These are static reads, as `n34m_reader.py` makes.",
            "M0 refuses a system reference that is not a cache image.",
            "The claim's text names dyld as identified by the OS and unbound.",
        ],
    },
    {
        "id": "N-04", "severity": "nonmandatory",
        "title": "D-16 settles MC36's premise from the link, not from the variable",
        "location": "DIRECTOR-DECISIONS.md D-16; MH-PLAN section 6; CONTRACT.md sections 7 and 9 (MC30, MC36)",
        "issue": "`bin/node`'s command 14 is a plain `LC_LOAD_DYLIB` of CoreFoundation, so under D-16 MC36 stands "
                 "as written. The link means that dyld loads CoreFoundation and runs its initializers before "
                 "`main`. It does not show that `__CF_USER_TEXT_ENCODING` is then present in the probe's "
                 "`process.env` with HOST's value, and MC36's expected refusal needs exactly that.",
        "effect": "None yet. The positive starts observe it.",
        "recommendation": "In the operational freeze, tie MC36 to a positive probe start of the same freeze that "
                          "observed the variable with HOST's value (MC30). If it was not observed, MC36 stays "
                          "`NOT_RUN` pending D-16's amendment, and its expected outcome is not weakened.",
    },
    {
        "id": "N-05", "severity": "nonmandatory",
        "title": "Implemented rules stricter than the contract's text",
        "location": "`parse_macho` 836–837; `python_inventory` 1164–1165; `check_python_macho` 933–949; "
                    "`_counted` 870–877; `_closure_pass` 1240–1266; W3-OBSERVER section 11 (Q1, Q3 to Q5)",
        "issue": "Beyond the contract's words, the parser refuses:",
        "issue_points": [
            "a fat Python image (section 4 does not say thin);",
            "any cpusubtype other than 0 (the contract says arm64);",
            "a weak reference that does not resolve;",
            "an `@rpath` reference that only another image's rpaths would resolve;",
            "a relative leaf-name reference;",
            "an executable without exactly one `LC_MAIN` and one `LC_LOAD_DYLINKER`;",
            "either of those commands in another file type;",
            "a dylib without exactly one `LC_ID_DYLIB`;",
            "a second copy of a single-instance command.",
        ],
        "effect": "Each rule fails closed. Under MH-PLAN section 8, an M0 refusal on any of them would be an "
                  "implementation cause and would stop MH. Every real file satisfies each rule:",
        "effect_points": [
            "no fat or arm64e image;",
            "no weak, `@rpath` or leaf-name reference;",
            "both executables have one `LC_MAIN` and one `LC_LOAD_DYLINKER`;",
            "all 25 dylibs have one `LC_ID_DYLIB`;",
            "no single-instance command is repeated.",
        ],
        "recommendation": "The observation plan's review cites W3-OBSERVER section 6 as the implemented rule set. A "
                          "later amendment may write the fat and subtype rules into section 4.",
    },
    {
        "id": "N-06", "severity": "nonmandatory",
        "title": "Unused LC_RPATH entries, one of them a build-machine path",
        "location": "the closure's `rpaths` (raw-compare-02.json, `python_inventory.closure.images`)",
        "issue": [
            "The 81 `LC_RPATH` entries are these:",
            "- `<prefix>/lib` in 78 framework images: the lib-dynload modules, the `Python` library and the process image;",
            "- the sqlite library's own lib directory;",
            "- libmpdec's `@loader_path/../lib`;",
            "- in Pillow's `libjpeg.62.4.0.dylib`, the absolute `/Users/runner/work/Pillow/Pillow/build/deps/darwin/lib`, which is absent here.",
            "No bound image has an `@rpath` reference, so none of these entries takes part in load-time resolution.",
        ],
        "effect": [
            "The parser records each entry's resolution, and records the libjpeg entry as absent at `/Users/runner`.",
            "Creating `/Users/runner`, for example an account of that name, would change the inventory. M0 and "
            "every recheck would then refuse. That fails closed: it never causes an unbound load.",
            "The entries remain search paths for run-time `dlopen(\"@rpath/…\")` calls from those images. dyld's "
            "search also includes the main executable's `<prefix>/lib`. Both lie outside the claim.",
        ],
        "recommendation": "Note it in the HOST review. No change is needed.",
    },
    {
        "id": "N-07", "severity": "nonmandatory",
        "title": "Git: M0 does not check E18's premise",
        "location": "`check_git_binding` (1893–1926); `GIT_VERSION_LINE` (116); CONTRACT.md section 2 (E18) and "
                    "section 7",
        "issue": [
            "Git is bound by path, SHA-256, size and mode, and is never parsed. `_macho_extent` refuses it as fat "
            "(`MACHO-FAT`, confirmed).",
            "The developer tools' Git, `/Library/Developer/CommandLineTools/usr/bin/git` (SHA-256 `be4afb2b…`, "
            "7,604,272 bytes), has an x86_64 slice and an arm64 slice, cpusubtype 3 and 0.",
            "Both slices reference only CoreServices, CoreFoundation, libz, libiconv and libSystem. All five are "
            "cache images, none is on disk, and neither slice has an `LC_RPATH`.",
        ],
        "effect": [
            "For that file, E18's \"its system libraries identified by OS build\" holds.",
            "Its arm64 slice embeds `2.50.1 (Apple Git-155)` and `git version %s`. Its predicted line, "
            "`git version 2.50.1 (Apple Git-155)\\n`, matches `GIT_VERSION_LINE`. This is a static prediction; "
            "no Git was started.",
            "The grammar-only check is consistent with the contract, which states no expected version.",
        ],
        "recommendation": "The observation plan's review confirms that the bound Git is this file, or re-reads the "
                          "load commands of any other candidate. The HOST review compares the recorded line with "
                          "the embedded text.",
    },
    {
        "id": "N-08", "severity": "nonmandatory",
        "title": "W3-OBSERVER section 5's measured figures predate MP",
        "location": "W3-OBSERVER section 5, \"Measured on this host\"",
        "issue": "Section 5 was measured \"with the venv as MI leaves it (no packages)\". It reports 84 images, "
                 "5 venv files, and \"No `@`-relative reference occurs\".",
        "effect": [
            "At this review there are 111 images. The venv holds 27 of them: Pillow's 18 bundled dylibs and 8 "
            "extension modules, and rpds's extension.",
            "There are 26 `@loader_path` references, all Pillow's, and 81 `LC_RPATH` entries.",
            "The venv holds 297 files, 45 directories and 3 links.",
            "Pillow's images are the first real files that exercise the `@loader_path` resolution path. The parser "
            "and the independent reader resolve all 26 references to the same bound files.",
        ],
        "recommendation": "The observation plan and its review use the frozen inventory's figures, not those of "
                          "section 5.",
    },
    {
        "id": "N-09", "severity": "nonmandatory",
        "title": "The -B rule names the .venv's interpreter, but this host's python3 is the same framework interpreter",
        "location": "MH-PLAN sections 3 and 5 (\"-B\"); W3-OBSERVER F4; the `python3 …` check commands in AGENTS.md",
        "issue": [
            "`python3` on this session's PATH is `<prefix>/opt/python@3.12/libexec/bin/python3`. That is a link to "
            "the framework's `bin/python3.12`, which is the bound launcher.",
            "1,390 of the framework's 1,804 standard-library sources have no cached bytecode. Of these, 106 lie "
            "outside `test`, `idlelib`, `lib2to3`, `turtledemo` and `tkinter`. Examples are `unittest/_log.py`, "
            "`unittest/async_case.py`, `doctest.py`, `multiprocessing/managers.py` and `email/mime/*.py`.",
            "Suppose the framework interpreter starts under any name, without `-B` and without "
            "`PYTHONDONTWRITEBYTECODE`, and imports one of them. It adds a `__pycache__` file to the bound tree, and "
            "M0 or a recheck refuses (MC32).",
        ],
        "effect": "This session's environment sets `PYTHONDONTWRITEBYTECODE=1`, so W1's four starts of bare "
                  "`python3` wrote nothing. The inventory digest equals MP's after-snapshot in runs 02 and 03, and "
                  "no entry of either tree changed afterwards (section 6).",
        "recommendation": "Extend section 5's rule to every start of the framework's interpreter, whatever its name, "
                          "the Director's workflow and documentation checks included. Alternatively, keep "
                          "`PYTHONDONTWRITEBYTECODE=1` set for the phase and record it.",
    },
]

CONDUCT = [
    "No Git write: the worktree's index file was last written at 16:08:36 MST, before this review began. No "
    "worktree file is newer than it, and no file was created in the worktree, bytecode included (no "
    "`__pycache__` exists under `prototypes/static_tray_v01/`).",
    "No Node, `ldd`, `codesign`, `otool` or Git `--version` start, no download, no install, and no Finder.",
    "Starts made:",
    "- `<worktree>/.venv/bin/python -I -S -B` for every script and every inline analysis;",
    "- shell utilities (`ls`, `find`, `stat`, `readlink`, `grep`, `sed`, `cat`, `env`, `date`, `mkdir`, `mv`);",
    "- five read-only Git commands in the worktree, to confirm that it was clean: `git status --short` and `git status --short --ignored`, twice each, and `git rev-parse HEAD`. The index file kept its earlier modification time;",
    "- four starts of bare `python3`, which is the framework interpreter (N-09). One printed an empty line, two read repository JSON, and one printed `sys` facts. Each ran without `-B` but under `PYTHONDONTWRITEBYTECODE=1`, so `dont_write_bytecode` was 1. Nothing was written: the inventory digest equals MP's after-snapshot in runs 02 and 03, and no entry of either tree, or of the external libraries' directories, is newer than 16:12:06 MST.",
    "Deviations from MH-PLAN section 3, which allows W1 static reads and its own scripts under `-I -S -B`: the Git "
    "reads and the bare `python3` starts. Neither wrote anything or changed a bound input.",
    "Writes: only under `<local>/c271-p35/workers/W1/`.",
    "First run superseded: `n34m_compare.py` compared the reader's labelled paths with the parser's real paths and "
    "so reported false differences. Its outputs are kept in `superseded-run-01/`, produced by earlier versions of "
    "the two scripts. Runs 02 and 03 use the corrected script, and their outputs record the scripts' digests.",
]


def bullets(lines):
    """A point that starts with '- ' or '  - ' is nested under the point before it."""
    out = []
    for line in lines:
        if line.startswith("  - "):
            out.append(line)
        elif line.startswith("- "):
            out.append("  " + line)
        else:
            out.append("- " + line)
    return "\n".join(out)


def finding_md(finding):
    lines = ["### %s (%s): %s" % (finding["id"], finding["severity"], finding["title"]), "",
             "- **Location:** " + finding["location"]]
    for key, label in (("issue", "Issue"), ("effect", "Effect on the real files"), ("recommendation", "Recommendation")):
        value = finding[key]
        points = finding.get(key + "_points", [])
        if isinstance(value, list):
            lines.append("- **%s:**" % label)
            for item in value:
                if item.startswith("- "):
                    lines.append("    " + item)
                else:
                    lines.append("  - " + item)
        else:
            lines.append("- **%s:** %s" % (label, value))
        for item in points:
            lines.append("  - " + item)
    return "\n".join(lines)


def finding_json(finding):
    out = {"id": finding["id"], "severity": finding["severity"], "title": finding["title"],
           "location": finding["location"]}
    for key in ("issue", "effect", "recommendation"):
        value = finding[key]
        parts = list(value) if isinstance(value, list) else [value]
        parts += finding.get(key + "_points", [])
        out[key if key != "recommendation" else "required_change"] = " ".join(
            part[2:] if part.startswith("- ") else part for part in parts)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser()
    for name in ("dir", "worktree", "local", "prefix"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--forbid", action="append", default=[],
                        help="a word that must not occur in either review file (case-insensitive)")
    args = parser.parse_args(argv)
    os.chdir(args.dir)
    labels = sorted(((name, prefix) for name, prefix in (("<worktree>", args.worktree), ("<local>", args.local),
                                                          ("<prefix>", args.prefix))), key=lambda row: -len(row[1]))

    def label(text):
        for name, prefix in labels:
            text = text.replace(prefix, name)
        return text

    reader = json.load(open("raw-reader-02.json", encoding="utf-8"))
    compare = json.load(open("raw-compare-02.json", encoding="utf-8"))
    recheck = json.load(open("raw-compare-03.json", encoding="utf-8"))
    git = json.load(open("raw-git-scan-02.json", encoding="utf-8"))
    python = reader["python"]
    inventory = compare["python_inventory"]
    closure = inventory["closure"]["images"]

    # Command 14 of bin/node, the CoreFoundation link (D-16), cited from the reader's record.
    cf = reader["node"]["slices"][0]["load_commands"][14]
    assert cf["name"] == "LC_LOAD_DYLIB" and cf["path"].endswith("/CoreFoundation")
    ANSWERS["b"]["points"][0] = ANSWERS["b"]["points"][0].format(
        index=cf["index"], offset=format(cf["file_offset"], ","), cmd=cf["cmd"], cmdsize=cf["cmdsize"],
        name_offset=cf["path_offset"], timestamp=cf["timestamp"], path=cf["path"], current=cf["current_version"],
        compatibility=cf["compatibility_version"])

    # ---- per-file records -------------------------------------------------
    images = dict(python["images"])
    images.update(python["external"])
    sequences = collections.Counter()
    for record in images.values():
        sequences[tuple(row["name"] for row in record["slices"][0]["load_commands"])] += 1
    sequence_ids = {}
    for number, (names, _count) in enumerate(sorted(sequences.items(), key=lambda kv: (-kv[1], kv[0])), 1):
        sequence_ids[names] = "S%02d" % number

    def image_entry(path, record):
        view = record["slices"][0]
        names = tuple(row["name"] for row in view["load_commands"])
        parser_row = compare["python_images"].get(path) or {}
        parsed = parser_row.get("check_python_macho", {})
        refs = (python["closure"]["references"].get(path) or {}).get("references", [])
        tree = record["tree"]
        root = FRAMEWORK if tree == "framework" else VENV if tree == "venv" else ""
        return {
            "path": path, "tree": tree, "relative_path": path[len(root) + 1:] if root else path,
            "sha256": record["sha256"], "size_bytes": record["size_bytes"], "mode": record["mode"],
            "nlink": record["nlink"], "container": record["container"], "header": view["header"],
            "load_commands": [strip_command(row) for row in view["load_commands"]], "sequence": sequence_ids[names],
            "install_name": next((row.get("path") for row in view["load_commands"] if row["name"] == "LC_ID_DYLIB"),
                                 None),
            "rpaths": [row.get("path") for row in view["load_commands"] if row["name"] == "LC_RPATH"],
            "references": [{"command": ref["command"], "raw": ref["raw"], "kind": ref["kind"],
                            "target": ref.get("target")} for ref in refs],
            "parser_rpath_resolution": (closure.get(path) or {}).get("rpaths", []),
            "anomalies": view["anomalies"],
            "reader_rules": record["rules"],
            "parser": {"read_macho": "accepted" if "read_macho" not in parser_row else parser_row["read_macho"],
                       "binding_matches_reader": parser_row.get("binding_matches_reader"),
                       "check_python_macho": "accepted" if parsed and not parsed.get("refused") else parsed,
                       "differences_from_reader": parser_row.get("differences_from_reader")},
        }

    entries = [image_entry(path, record) for path, record in sorted(images.items())]
    node_record = reader["node"]
    node_view = node_record["slices"][0]
    node_entry = {"path": NODE, "sha256": node_record["sha256"], "size_bytes": node_record["size_bytes"],
                  "mode": node_record["mode"], "nlink": node_record["nlink"], "container": node_record["container"],
                  "header": node_view["header"], "load_commands": [strip_command(row) for row in node_view["load_commands"]],
                  "anomalies": node_view["anomalies"], "reader_rules": node_record["rules"],
                  "parser": {"read_macho_with_pin": "accepted", "pin": compare["node"]["pin_from_node_source"],
                             "check_node_macho": compare["node"]["check_node_macho"],
                             "differences_from_reader": compare["node"]["differences_from_reader"]}}

    # ---- system references -----------------------------------------------
    system_rows = []
    for path, row in sorted(reader["system_references"].items()):
        node_ref = NODE in row["referenced_by"]
        system_rows.append({"path": path, "referenced_by_images": len(row["referenced_by"]), "by_node": node_ref,
                            "commands": row["commands"], "on_disk": row["on_disk"],
                            "in_shared_cache_image_list": row["in_shared_cache_image_list"]})

    # ---- reviewed files, scripts and raw outputs ---------------------------
    reviewed = []
    for rel in REVIEWED:
        digest, size = sha256_of(os.path.join(args.worktree, rel))
        reviewed.append({"path": "<worktree>/" + rel, "sha256": digest, "size_bytes": size})
    scripts = [{"path": "<local>/c271-p35/workers/W1/" + name, "sha256": sha256_of(name)[0],
                "size_bytes": sha256_of(name)[1]} for name in SCRIPTS]
    raws = [{"path": "<local>/c271-p35/workers/W1/" + name, "sha256": sha256_of(name)[0],
             "size_bytes": sha256_of(name)[1]} for name in RAW]

    mutation_node = [{key: case[key] for key in ("id", "case", "expected", "observed", "as_expected")}
                     for case in compare["node"]["mutation_cases"]]
    mutation_python = [{key: case[key] for key in ("id", "case", "expected", "observed", "as_expected")}
                       for case in compare["python_mutation_cases"]]
    os_identity = compare["os_identity"]["value"]
    cache = reader["dyld_shared_cache"]
    dylinker = {key: reader["dylinker"][key] for key in ("path", "sha256", "size_bytes", "mode", "container",
                                                          "slices_summary")}
    git_extra = reader["extras"][0]
    git_slices = [{"cputype": view["header"]["cputype_name"], "cpusubtype": view["header"]["cpusubtype_raw"],
                   "filetype": view["header"]["filetype_name"],
                   "load_commands": [row["name"] for row in view["load_commands"]],
                   "dylib_paths": view["dylib_paths"],
                   "in_shared_cache_image_list": view["dylib_paths_in_shared_cache_image_list"],
                   "on_disk": view["dylib_paths_on_disk"],
                   "rpaths": [row.get("path") for row in view["load_commands"] if row["name"] == "LC_RPATH"]}
                  for view in git_extra["slices"]]

    assert all(case["as_expected"] for case in mutation_node + mutation_python)
    assert recheck["python_inventory"]["digest"] == inventory["digest"]
    assert not any(entry["parser"]["differences_from_reader"] for entry in entries)
    assert not node_entry["parser"]["differences_from_reader"]

    review = {
        "schema": "ontokin.c271.p35-n34m-review/1",
        "review": "N34-M-REVIEW",
        "task": "C271",
        "phase": "C271-P35-macos-host-qualification-mh",
        "gate": "MH",
        "stage": "S2",
        "obligation": "CONTRACT.md section 7, N34-M; MH-PLAN section 2 stage S2 and section 6; PHASE.json A2",
        "reviewer": "W1, N34-M reviewer: a Claude Code subagent in a fresh context; wrote none of the parser, the "
                    "contract, the amendment, the preparation or the plans",
        "director": "c271-p35-e38e3aa82ade",
        "contract": "ontokin.current-host-readback/0.2.0",
        "design_revision": 4,
        "amendments": ["P33-AMENDMENT-001"],
        "amendment_scope": "AMENDMENT-001 replaces 17 CONTRACT.md clauses (sections 1, 2, 5, 9, 10, 12: the "
                           "supervisor, MC14, MC37 to MC39, the contract label and trust assumption 2); none "
                           "concerns Mach-O or the interpreter binding, so sections 4 and 7 apply as adopted",
        "bound_commit": {"sha": "16d4f9f4a13bb7edef709a1ac050b81469fb3063", "worktree": "<worktree>",
                         "state": "clean, only .venv/ ignored, at the start and at the end"},
        "host": {"os": os_identity, "machine": "arm64"},
        "date": "2026-11-26",
        "verdict": VERDICT,
        "mandatory_findings": [],
        "summary": SUMMARY,
        "answers": {key: {"question": value["question"], "answer": value["answer"],
                          "detail": [point.strip()[2:] if point.strip().startswith("- ") else point.strip()
                                     for point in value["points"]]}
                    for key, value in ANSWERS.items()},
        "findings": [finding_json(finding) for finding in FINDINGS],
        "files": {"node": node_entry, "python_images": entries},
        "load_command_sequences": [{"id": sequence_ids[names], "count": count, "commands": list(names)}
                                   for names, count in sorted(sequences.items(), key=lambda kv: sequence_ids[kv[0]])],
        "selection": python["selection"],
        "trees": python["trees"],
        "inventory": {"digest": inventory["digest"], "canonical_bytes": inventory["canonical_bytes"],
                      "framework_entries": inventory["framework_entries"], "venv_entries": inventory["venv_entries"],
                      "kinds": inventory["kinds"], "closure_images": inventory["closure_images"],
                      "closure_external": inventory["closure_external"], "closure_links": inventory["closure_links"],
                      "second_computation_differences": inventory["second_computation_differences"],
                      "run_03_digest": recheck["python_inventory"]["digest"],
                      "equals_mp_after_snapshot": "python_inventory_after_sha256 of "
                                                  "macos-preparation-p34/reviews/RESULT-REVIEW-001.json",
                      "cross_check_with_reader": compare["inventory_cross_check"]},
        "verify_packages": compare["verify_packages"]["value"][0],
        "check_launcher": {"accepted": not compare["check_launcher"]["refused"],
                           "process": {key: compare["launcher_state"]["value"][key]
                                       for key in ("executable", "base_executable", "prefix", "base_prefix",
                                                   "process_image", "version", "build_string", "flags", "path")}},
        "system_references": system_rows,
        "dyld_shared_cache": cache,
        "firmlinked_system_library_subtrees": ["/System/Library/Caches", "/System/Library/Assets",
                                               "/System/Library/PreinstalledAssets", "/System/Library/AssetsV2",
                                               "/System/Library/PreinstalledAssetsV2",
                                               "/System/Library/CoreServices/CoreTypes.bundle/Contents/Library",
                                               "/System/Library/Speech"],
        "dylinker": dylinker,
        "git": {"path": git_extra["path"], "sha256": git_extra["sha256"], "size_bytes": git_extra["size_bytes"],
                "container": git_extra["container"], "slices": git_slices,
                "parser_classification": {"macho_magic_kind": compare["git_magic_kind"],
                                          "_macho_extent": compare["git_parse_macho"]},
                "embedded_version": git["arm64_embedded_versions"], "format": git["arm64_formats"],
                "predicted_line": git["predicted_line"],
                "predicted_line_matches_grammar": git["predicted_line_matches_grammar"],
                "note": "static prediction; no Git start"},
        "mutation_cases": {"node": mutation_node, "python": mutation_python,
                           "python_base": compare["python_mutation_base"]},
        "reviewed_files": reviewed,
        "reviewed_parser_lines": "current_host_observation_v02.py: constants 184–232; parser 715–958; trees and links "
                                 "960–1069; Python inventory, closure, comparison and packages 1072–1455; launcher "
                                 "1457–1518; check_runtime 1850–1890; check_git_binding 1893–1926; GIT_VERSION_LINE 116",
        "reproduction": {
            "interpreter": "<worktree>/.venv/bin/python (CPython 3.12.13), -I -S -B, standard library only",
            "commands": [
                "$PY -I -S -B n34m_reader.py --node " + NODE + " --venv <worktree>/.venv --dyld-cache "
                "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e --extra "
                "/Library/Developer/CommandLineTools/usr/bin/git --label '<worktree>=…' --label '<local>=…' "
                "--label '<prefix>=…' --output raw-reader-02.json",
                "$PY -I -S -B n34m_compare.py --parser <worktree>/prototypes/static_tray_v01/"
                "current_host_observation_v02.py --reader-json raw-reader-02.json --node " + NODE + " --venv "
                "<worktree>/.venv --framework " + FRAMEWORK + " --node-source "
                "<local>/c271-macos/node-v24.22.1-darwin-arm64/NODE-SOURCE.json --git "
                "/Library/Developer/CommandLineTools/usr/bin/git --label … --output raw-compare-02.json "
                "(and again, last, --output raw-compare-03.json)",
                "$PY -I -S -B n34m_git_scan.py --git /Library/Developer/CommandLineTools/usr/bin/git --output "
                "raw-git-scan-02.json",
                "$PY -I -S -B n34m_report.py --dir <local>/c271-p35/workers/W1 --worktree … --local … --prefix … --forbid … (the package manager, the user and the volume names)",
            ],
            "scripts": scripts,
            "raw_outputs": raws,
        },
        "conduct": [line.lstrip("- ") for line in CONDUCT],
    }

    # ---- Markdown -----------------------------------------------------------
    md = []
    md.append("# N34-M: independent review of the Mach-O parser and the closure claim")
    md.append("")
    md.append("**Reviewer:** W1, the N34-M reviewer of phase `C271-P35-macos-host-qualification-mh`, gate MH, stage S2 "
              "(Director `c271-p35-e38e3aa82ade`), local mode. W1 is a Claude Code subagent in a fresh context. It "
              "wrote none of the parser, the contract, the amendment, the preparation or the plans.  ")
    md.append("**Bound commit:** `16d4f9f4a13bb7edef709a1ac050b81469fb3063`. The C271 worktree was clean, with only "
              "`.venv/` ignored, at the start and at the end.  ")
    md.append("**Contract:** `ontokin.current-host-readback/0.2.0`, design revision 4 (CONTRACT.md as amended by "
              "P33-AMENDMENT-001).  ")
    md.append("**Obligation:** contract section 7, N34-M; MH-PLAN stage S2; PHASE.json acceptance A2.  ")
    md.append("**Host:** macOS %s (%s), arm64; the system and cryptex SystemVersion.plist files are byte-identical.  "
              % (os_identity["system_version"]["product_version"], os_identity["system_version"]["product_build_version"]))
    md.append("**Date:** 2026-11-26.")
    md.append("")
    md.append("Places are named by labels:")
    md.append("")
    md.append("- `<worktree>` is the C271 worktree.")
    md.append("- `<local>` is the working directory beside the clone.")
    md.append("- `<prefix>` is the installation prefix that holds the interpreter's framework and its non-system "
              "libraries.")
    md.append("")
    md.append("Framework paths in the tables are relative to the framework version directory, `%s`; `.venv` paths "
              "are relative to `<worktree>/.venv`. The machine-readable form is "
              "[N34-M-REVIEW.json](N34-M-REVIEW.json), and the scripts and raw outputs lie beside it." % FRAMEWORK)
    md.append("")
    md.append("## Verdict")
    md.append("")
    md.append("**%s.** There is no mandatory finding." % VERDICT)
    md.append("")
    md.append(bullets(SUMMARY))
    md.append("")
    md.append("## 1. Method")
    md.append("")
    md.append("1. **Read:**")
    md.append("   - CONTRACT.md sections 3 (Node's \"thin 64-bit arm64\"), 4, 7 and 12, and the matching lists in "
              "CONTRACT.json;")
    md.append("   - AMENDMENT-001, which changes neither section 4 nor section 7;")
    md.append("   - the parser's Mach-O and Python-installation parts (%s);" % review["reviewed_parser_lines"])
    md.append("   - W3-OBSERVER sections 5, 6 and 9 to 12; MH-PLAN sections 3 and 6; D-16.")
    md.append("2. **Reader.** `n34m_reader.py` is an independent Mach-O reader that uses only the standard library and "
              "`struct`. It shares no code with the parser and does not import it.")
    md.append("   - **Each file:** SHA-256, size, mode and link count; thin or fat, with every fat slice; the header, "
              "with the cpusubtype's capability bits separated; the file type and flags; and every load command with "
              "its decoded fields. It also checks the structure: section, symbol, indirect-symbol and linkedit "
              "ranges, and segment overlap.")
    md.append("   - **Trees:** it lists both trees exhaustively without following links, and classifies every regular "
              "file by its leading magic.")
    md.append("   - **Resolution:** it resolves the `bin/python` chain hop by hop, cross-checked with `os.path.realpath`. "
              "It computes the closure to a fixed point, with two resolutions of `@rpath`: the image's own entries, "
              "and a dyld-like rpath stack.")
    md.append("   - **System references:** it checks each one against the disk and against the image table of the "
              "cryptex's main shared-cache file. It also checks install names for collisions.")
    md.append("   - **Rules:** it evaluates the contract's rules independently.")
    md.append("3. **Comparison.** `n34m_compare.py` loads the parser by file path. Importing it added only "
              "standard-library modules. The script calls only pure functions:")
    md.append("   - `read_macho` with the NODE-SOURCE pin and `private=True`, as `check_runtime` does, then "
              "`check_node_macho`;")
    md.append("   - `check_python_macho` for each image;")
    md.append("   - `python_inventory` twice, with `compare_inventory`;")
    md.append("   - `verify_packages`, and `launcher_state` with `check_launcher` for its own process;")
    md.append("   - `read_os_identity`, and `macho_magic_kind` and `_macho_extent` on Git's first bytes.")
    md.append("")
    md.append("   It compares the two parses command by command, and cross-checks every tree entry, with every file's "
              "SHA-256. It also runs 64 Node and 17 Python mutation cases in memory.")
    md.append("4. **Git.** `n34m_git_scan.py` reads the developer tools' Git statically and extracts its embedded "
              "version text.")
    md.append("5. **Runs.** Every run used `<worktree>/.venv/bin/python -I -S -B`. Run 02 is the evidence. Run 03 "
              "repeated the comparison after all other work, with the same result. The commands are in the JSON "
              "form's `reproduction`.")
    md.append("")
    md.append("## 2. The files")
    md.append("")
    md.append("### 2.1 `bin/node`")
    md.append("")
    header = node_view["header"]
    md.append(table(["Property", "Value"], [
        ["Path", code(NODE)], ["SHA-256", code(node_record["sha256"])],
        ["Size, mode, links", "%s bytes, `%s`, %d" % (format(node_record["size_bytes"], ","), node_record["mode"],
                                                        node_record["nlink"])],
        ["Container", "thin"], ["Magic", "`MH_MAGIC_64` (little-endian)"],
        ["cputype", "`%s` %s" % (header["cputype"], header["cputype_name"])],
        ["cpusubtype", "`%s`: value %d (%s), capability bits `%s`" % (header["cpusubtype_raw"], header["cpusubtype_value"],
                                                                      header["cpusubtype_name"],
                                                                      header["cpusubtype_capability_bits"])],
        ["File type", "%d `%s`" % (header["filetype"], header["filetype_name"])],
        ["Flags", "`%s`: %s" % (header["flags"], ", ".join(header["flag_names"]))],
        ["ncmds, sizeofcmds", "%d, %d" % (header["ncmds"], header["sizeofcmds"])],
        ["Pin (NODE-SOURCE.json)", "equal: SHA-256, size and mode"],
        ["Contract section 7 (reader)", node_record["rules"]["verdict"]],
        ["Parser (`read_macho` with the pin, `check_node_macho`)", "accepted; no field differs from the reader"],
    ]))
    md.append("")
    rows = []
    for row in node_view["load_commands"]:
        fields = []
        for key in ("segname", "path", "uuid"):
            if key in row:
                fields.append(code(str(row[key])))
        if "fileoff" in row:
            fields.append("file %d + %d" % (row["fileoff"], row["filesize"]))
        if "dataoff" in row:
            fields.append("data %d + %d" % (row["dataoff"], row["datasize"]))
        if "current_version" in row:
            fields.append("current %s, compatibility %s" % (row["current_version"], row["compatibility_version"]))
        if "platform_name" in row:
            fields.append("%s, minos %s, sdk %s, %s" % (row["platform_name"], row["minos"], row["sdk"],
                                                        ", ".join("%s %s" % (tool["tool_name"], tool["version"])
                                                                  for tool in row["tools"])))
        if row.get("name") == "LC_SOURCE_VERSION":
            fields.append(row["version"])
        if "entryoff" in row:
            fields.append("entryoff %d, stacksize %d" % (row["entryoff"], row["stacksize"]))
        if row.get("name") == "LC_SYMTAB":
            fields.append("%d symbols, %d string bytes" % (row["nsyms"], row["strsize"]))
        rows.append([row["index"], code(row["cmd"]), code(row["name"]), row["cmdsize"], "; ".join(fields)])
    md.append(table(["#", "cmd", "Name", "cmdsize", "Decoded fields"], rows))
    md.append("")
    md.append("### 2.2 The interpreter installation: selection and trees")
    md.append("")
    selection = python["selection"]
    cfg = selection["pyvenv_cfg"]
    md.append("- **pyvenv.cfg:** `home = %s`, `include-system-site-packages = %s`, `version = %s`, `executable = %s`."
              % (cfg["home"], cfg["include-system-site-packages"], cfg["version"], cfg["executable"]))
    md.append("- **Chain from `<worktree>/.venv/bin/python`** (%d hops; `os.path.realpath` agrees):"
              % len(selection["launcher_chain"]["hops"]))
    for hop in selection["launcher_chain"]["hops"]:
        md.append("  - `%s` → `%s`" % (hop["path"], hop["target"]))
    md.append("  - It ends at `%s`. `home`'s `python3.12` reaches the same launcher through %d hops, and "
              "`executable` through none." % (selection["launcher"], len(selection["home_launcher_chain"]["hops"])))
    trees = python["trees"]
    md.append("- **Trees:**")
    md.append("  - The framework version directory holds %s files, %d directories and %d links, and the `.venv` holds "
              "%d files, %d directories and %d links."
              % (format(trees["framework"]["files"], ","), trees["framework"]["directories"],
                 len(trees["framework"]["links"]), trees["venv"]["files"], trees["venv"]["directories"],
                 len(trees["venv"]["links"])))
    md.append("  - By leading magic, %d framework files and %d `.venv` files are Mach-O. None is fat, 32-bit, "
              "big-endian, a Java class file or an `ar` archive, and there is no special file."
              % (trees["framework"]["magic_counts"]["macho"], trees["venv"]["magic_counts"]["macho"]))
    md.append("- **Framework links:** %s." % "; ".join("`%s` → `%s`" % (row["path"][len(FRAMEWORK) + 1:], row["target"])
                                                     for row in trees["framework"]["links"]))
    md.append("- **The parser's inventory:**")
    md.append("  - It holds %s and %d entries, the same as the reader's listing, with the same kinds, link targets "
              "and file SHA-256 values."
              % (format(inventory["framework_entries"], ","), inventory["venv_entries"]))
    md.append("  - It has %d closure images, which equal the reader's images and externals, and %d closure link hops."
              % (inventory["closure_images"], len(inventory["closure_links"])))
    md.append("  - Its digest is `%s` (%s canonical bytes). The value is identical on a second computation and in "
              "run 03, and equals MP's `python_inventory_after_sha256`."
              % (inventory["digest"], format(inventory["canonical_bytes"], ",")))
    md.append("")
    md.append("### 2.3 Load-command sequences of the Python images")
    md.append("")
    md.append("Abbreviations: SEG `LC_SEGMENT_64`, INFO `LC_DYLD_INFO_ONLY`, FIXUPS `LC_DYLD_CHAINED_FIXUPS`, EXPORTS "
              "`LC_DYLD_EXPORTS_TRIE`, ID `LC_ID_DYLIB`, DYLIB `LC_LOAD_DYLIB`, BUILD `LC_BUILD_VERSION`, SRC "
              "`LC_SOURCE_VERSION`, FSTARTS `LC_FUNCTION_STARTS`, DIC `LC_DATA_IN_CODE`, CS `LC_CODE_SIGNATURE`. "
              "The complete list of every file, with decoded fields, is in the JSON form.")
    md.append("")
    md.append(table(["ID", "Images", "Commands in order"],
                    [[sequence_ids[names], count, compact(names)]
                     for names, count in sorted(sequences.items(), key=lambda kv: sequence_ids[kv[0]])]))
    md.append("")

    def image_rows(tree):
        out = []
        for entry in entries:
            if entry["tree"] != tree:
                continue
            header = entry["header"]
            nonsystem = [ref["raw"] for ref in entry["references"] if ref["kind"] != "system"]
            out.append([code(entry["relative_path"]), header["filetype_name"].replace("MH_", ""),
                        format(entry["size_bytes"], ","), code(entry["sha256"]), entry["sequence"],
                        code(entry["install_name"] or ""), "<br>".join(code(item) for item in entry["rpaths"]),
                        "<br>".join(code(item) for item in nonsystem),
                        "%s / %s" % (entry["reader_rules"]["verdict"].lower(),
                                     "accept" if entry["parser"]["check_python_macho"] == "accepted" else "REFUSE")])
        return out

    columns = ["File", "Type", "Bytes", "SHA-256", "Seq.", "LC_ID_DYLIB", "LC_RPATH", "Non-system references",
               "Reader / parser"]
    md.append("Every image below is thin, cpusubtype `0x00000000` and free of anomalies. The parser reads it with a "
              "binding equal to the reader's, and no parsed field differs. Every non-system reference resolves to a "
              "bound image, in both readings. System references are in section 2.7.")
    md.append("")
    md.append("### 2.4 Framework images (79)")
    md.append("")
    md.append(table(columns, image_rows("framework")))
    md.append("")
    md.append("### 2.5 `.venv` images (27)")
    md.append("")
    md.append(table(columns, image_rows("venv")))
    md.append("")
    md.append("### 2.6 External dependencies (5)")
    md.append("")
    md.append(table(columns, image_rows("external")))
    md.append("")
    md.append("The closure records six link hops:")
    md.append("")
    for row in inventory["closure_links"]:
        md.append("- `%s` → `%s`" % (row["path"], row["target"]))
    md.append("")
    md.append("The external libraries' own references:")
    md.append("")
    for entry in entries:
        if entry["tree"] == "external":
            md.append("- `%s`: %s" % (entry["path"].split("/")[-1],
                                     ", ".join(code(ref["raw"]) for ref in entry["references"])))
    md.append("")
    md.append("### 2.7 System references")
    md.append("")
    md.append(table(["Path", "Referencing images", "Node", "On disk", "In the cache's image table"],
                    [[code(row["path"]), row["referenced_by_images"], "yes" if row["by_node"] else "",
                      "yes" if row["on_disk"] else "no", "yes" if row["in_shared_cache_image_list"] else "NO"]
                     for row in system_rows]))
    md.append("")
    md.append("### 2.8 The dyld shared cache and the dynamic linker")
    md.append("")
    md.append(table(["Property", "Value"], [
        ["Main cache file", code(cache["path"])],
        ["SHA-256, size", "%s, %s bytes" % (code(cache["sha256"]), format(cache["size_bytes"], ","))],
        ["Header", "magic `%s`, UUID `%s`, platform %d, osVersion %s" % (cache["magic"], cache["uuid"], cache["platform"],
                                                                      cache["os_version"])],
        ["Images, subcaches", "%s images (from `%s`), %d subcaches" % (format(cache["images_count"], ","),
                                                                    cache["image_table"], cache["sub_cache_count"])],
        ["dyld in the cache", "header `dyldInCacheMH` `%s`; `/usr/lib/dyld` in the image table: %s"
         % (cache["dyld_in_cache_mh"], "yes" if cache["usr_lib_dyld_in_image_list"] else "no")],
        ["`/usr/lib/dyld` on disk", "%s, %s bytes, %s: %s" % (code(dylinker["sha256"]), format(dylinker["size_bytes"], ","),
                                                             dylinker["container"],
                                                             ", ".join("%s `%s` %s" % (row["cputype_name"],
                                                                                       row["cpusubtype_raw"],
                                                                                       row["filetype_name"])
                                                                       for row in dylinker["slices_summary"]))],
    ]))
    md.append("")
    md.append("### 2.9 The developer tools' Git (supplementary, for question (d))")
    md.append("")
    md.append("`%s`: SHA-256 `%s`, %s bytes, fat." % (git_extra["path"], git_extra["sha256"],
                                                    format(git_extra["size_bytes"], ",")))
    md.append("")
    md.append(table(["Slice", "cpusubtype", "Type", "Commands", "Dylibs (all cache images, none on disk)", "LC_RPATH"],
                    [[row["cputype"], code(row["cpusubtype"]), row["filetype"], len(row["load_commands"]),
                      "<br>".join(code(path) for path in row["dylib_paths"]), "none" if not row["rpaths"] else row["rpaths"]]
                     for row in git_slices]))
    md.append("")
    md.append("The parser classifies the file as `fat`, and `_macho_extent` refuses it (`MACHO-FAT`). Its arm64 "
              "slice embeds `%s` and `%s`, so the predicted line is `%s`; it matches `GIT_VERSION_LINE` "
              "(a static prediction; no start)."
              % (git["arm64_embedded_versions"][0], git["arm64_formats"][0], git["predicted_line"].replace("\n", "\\n")))
    md.append("")
    md.append("## 3. Answers")
    md.append("")
    for key, value in ANSWERS.items():
        md.append("### (%s) %s" % (key, value["question"]))
        md.append("")
        md.append("**%s**" % value["answer"])
        md.append("")
        md.append(bullets(value["points"]))
        md.append("")
    md.append("## 4. Findings")
    md.append("")
    md.append("All nine are nonmandatory: none blocks adopting an execution plan.")
    md.append("")
    for finding in FINDINGS:
        md.append(finding_md(finding))
        md.append("")
    md.append("## 5. Mutation cases")
    md.append("")
    md.append("Each case changes the real header bytes in memory and calls `parse_macho` and then the rule check: "
              "`check_node_macho` for the N cases, on `bin/node`, and `check_python_macho` for the P cases, on "
              "`lib/python3.12/lib-dynload/_ssl.cpython-312-darwin.so`. Every observed outcome equals the predicted "
              "one. Cases N58 to N63 show the properties that the parser does not decide (N-02).")
    md.append("")
    md.append(table(["ID", "Case", "Expected", "Observed"],
                    [[case["id"], case["case"], code(case["expected"]), code(case["observed"])]
                     for case in mutation_node + mutation_python]))
    md.append("")
    md.append("## 6. Conduct")
    md.append("")
    md.append(bullets(CONDUCT))
    md.append("")
    md.append("## 7. Files")
    md.append("")
    md.append("Reviewed, at the bound commit:")
    md.append("")
    md.append(table(["File", "SHA-256", "Bytes"], [[code(row["path"]), code(row["sha256"]), format(row["size_bytes"], ",")]
                                                   for row in reviewed]))
    md.append("")
    md.append("Produced by W1, in `<local>/c271-p35/workers/W1/`. The two review files are rendered by "
              "`n34m_report.py` from the raw outputs, so their own digests are not listed.")
    md.append("")
    md.append(table(["File", "SHA-256", "Bytes"], [[code(row["path"][len("<local>/c271-p35/workers/W1/"):]),
                                                    code(row["sha256"]), format(row["size_bytes"], ",")]
                                                   for row in scripts + raws]))
    md.append("")
    text_md = "\n".join(md)
    text_json = json.dumps(review, indent=1, sort_keys=False, ensure_ascii=False) + "\n"
    for text in (text_md, text_json):
        lowered = text.lower()
        for word in args.forbid:
            assert word.lower() not in lowered, "a forbidden word occurs"
        for name, prefix in labels:
            assert prefix not in text, name
    for name, text in (("N34-M-REVIEW.md", text_md), ("N34-M-REVIEW.json", text_json)):
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(name, len(text.encode("utf-8")), hashlib.sha256(text.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
