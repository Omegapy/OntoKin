"""Collect static source identities and authoring records for the P11 proposal."""
import hashlib
import json
from pathlib import Path
import sys

workspace = Path(sys.argv[1]).resolve()
repo = workspace / "OntoKin"
candidate = workspace / "session_evidence/loader_design/candidate002"


def digest(path):
    raw = path.read_bytes()
    return {"size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def put(name, value):
    with (candidate / name).open("x", encoding="ascii") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n")


local = [
 ("L01", "prototypes/static_tray_v01/current_host_inspection_v01.py", "Read targeted parser, plan, path/alias, author-runtime, resolution, validation/recheck and launch boundaries; no import", ["read_elf_metadata", "_plan_shape", "_check_author_runtime", "_check_resolution", "_required_paths", "_input_snapshot", "_validate", "_recheck", "_launch_check"]),
 ("L02", "prototypes/static_tray_v01/current_host_readback_v01.py", "Read strict HOST consumer predicates and source/schemas", ["_verify_host", "_alias", "_absolute", "_schema"]),
 ("L03", "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md", "Read complete adopted prose", ["4. Selected runtime and host qualification", "6. Versioned manifest", "7. Fixed scientific"]),
 ("L04", "docs/engineering/localized-repair-c271/current-host-p05/ADOPTION.json", "Read complete adoption", ["accepted_design_only"]),
 ("L05", "docs/engineering/localized-repair-c271/host-inspection-p07/HOST-INSPECTION-DESIGN.md", "Read complete adopted design", ["3. Proposed executable inspection-plan contract", "4. Static closure before execution", "6. P06-compatible output"]),
 ("L06", "docs/engineering/localized-repair-c271/host-inspection-p07/QUALIFICATION-PLAN.md", "Read complete qualification plan", ["H0", "H1", "R03"]),
 ("L07", "docs/engineering/localized-repair-c271/host-inspection-p07/ADOPTION.json", "Read complete adoption", ["accepted_design_only"]),
 ("L08", "docs/engineering/localized-repair-c271/host-preparation-p09/evidence/H0-STATIC-BLOCKER-001.json", "Read complete retained record; no host reread", ["selected_python", "unmet_h0_work"]),
 ("L09", "docs/engineering/localized-repair-c271/host-preparation-p09/evidence/H0-PREPARATION-REPORT.md", "Read complete retained report", ["Exact input and source", "Completed and remaining work"]),
 ("L10", "../incoming/p10/recovery/session_p10/elf_review/frozen002/SELECTED-PYTHON-OBSERVATION.json", "Read complete independent raw observation; not a production-output oracle", ["strings", "dynamic_entries", "image"]),
 ("L11", "../incoming/p10/recovery/session_p10/elf_review/candidate001/SELECTED-PYTHON-RESULT.json", "Read retained production-result classification only; not used to author new expectations", ["actual", "matches_frozen_intended_behavior"]),
 ("L12", "docs/engineering/localized-repair-c271/elf-string-table-p10/DESIGN.md", "Read complete P10 finite mapping rule", ["Partition the half-open virtual range", "guards remain"]),
 ("L13", "docs/engineering/localized-repair-c271/elf-string-table-p10/RESULTS.md", "Read complete P10 reported outcomes and boundary", ["175 methods", "H0 remains unaccepted"]),
 ("L14", "docs/engineering/localized-repair-c271/host-inspection-p07/COMPATIBILITY-REPORT.md", "Read complete source/consumer compatibility report", ["Exact compatibility choices", "Unresolved items"]),
 ("L15", "tests/test_current_host_inspection_v01.py", "Targeted static test-fixture/control source inspection; not imported or run", ["synthetic_elf", "test_HI_P01", "test_SUP_01", "read_elf_metadata refusal controls"]),
 ("L16", "tests/test_current_host_elf_mapping_v01.py", "Targeted static mapping-control adapter inspection; not imported or run", ["read_elf_metadata", "frozen cases"]),
]
bindings = []
for sid, rel, reading, anchors in local:
    path = repo / rel
    bindings.append({"id": sid, "path": str(path.relative_to(workspace)) if ".." not in path.relative_to(workspace).parts else str(path.resolve().relative_to(workspace)),
                     **digest(path), "reading": reading, "anchors": anchors,
                     "revision": "e0119f376441fee0fc3956852ac63110ab141011" if not rel.startswith("../") else "retained P10 recovery input; source identity in its own record"})

web = [
 {"id":"W01", "url":"https://sources.debian.org/src/glibc/2.36-8/sysdeps/unix/sysv/linux/dl-origin.c/", "version":"Debian glibc source package 2.36-8", "anchor":"_dl_get_origin; original source lines 25-78", "support":"Direct Linux main origin from /proc/self/exe; environment fallback exists but is excluded by this design", "ref_id":"turn100718315view0", "reference_kind":"version-fixed published primary source code"},
 {"id":"W02", "url":"https://sources.debian.org/src/glibc/2.36-8/elf/dl-load.c/", "version":"Debian glibc source package 2.36-8", "anchor":"is_dst; _dl_dst_substitute; fillin_rpath; _dl_map_object", "support":"Token recognition and separate RPATH/RUNPATH lookup behavior; the project's nonselecting condition is its own conservative restriction", "ref_id":"turn511160069view2", "reference_kind":"version-fixed published primary source code"},
 {"id":"W03", "url":"https://man7.org/linux/man-pages/man8/ld.so.8.html", "version":"Linux man-pages 6.19 as rendered at retrieval", "anchor":"DESCRIPTION; Dynamic string tokens; secure-execution mode", "support":"Search stage ordering, RPATH inheritance, direct RUNPATH scope, hardware alternatives, token meanings and secure mode", "ref_id":"turn451094222view1", "reference_kind":"upstream manual rendering; URL itself is not content-addressed"},
 {"id":"W04", "url":"https://sourceware.org/pipermail/libc-alpha/2025-March/165169.html", "version":"2025-03-11 patch v3 by Adhemerval Zanella", "anchor":"opening rationale; _dl_canonicalize proposal", "support":"Direct-versus-explicit invocation origin distinction and why ldd aliases need separate review; does not prove patch adoption", "ref_id":"turn100718315view1", "reference_kind":"dated immutable upstream development-mail record"},
 {"id":"W05", "url":"https://sourceware.org/glibc/manual/2.39/html_node/Dynamic-Linker-Invocation.html", "version":"GNU C Library manual 2.39", "anchor":"37.1 Dynamic Linker Invocation", "support":"Ordinary kernel-selected interpreter versus explicit dynamic-linker invocation", "ref_id":"turn451094222view0", "reference_kind":"version-fixed upstream manual"},
 {"id":"W06", "url":"https://man7.org/linux/man-pages/man5/proc_pid_exe.5.html", "version":"Linux man-pages 6.19, source page date 2026-02-08", "anchor":"DESCRIPTION", "support":"Kernel executable pathname and deleted suffix; access/availability limits", "ref_id":"turn100718315view2", "reference_kind":"upstream manual rendering; URL itself is not content-addressed"},
 {"id":"W07", "url":"https://man7.org/linux/man-pages/man3/getauxval.3.html", "version":"Linux man-pages rendering retrieved in P11", "anchor":"DESCRIPTION; AT_SECURE; AT_EXECFN", "support":"Auxiliary vector type/value meaning and secure execution; source of pointer values is not a proposed pathname authority", "ref_id":"turn100718315view3", "reference_kind":"upstream manual rendering; URL itself is not content-addressed"},
 {"id":"W08", "url":"https://sources.debian.org/src/glibc/2.36-9%2Bdeb12u10/bits/auxv.h", "version":"Debian glibc source package 2.36-9+deb12u10", "anchor":"AT_NULL=0; AT_SECURE=23", "support":"Numeric auxiliary ABI selectors", "ref_id":"turn308703809view0", "reference_kind":"version-fixed published primary source code"},
 {"id":"W09", "url":"https://sources.debian.org/src/glibc/2.36-8/elf/elf.h/", "version":"Debian glibc source package 2.36-8", "anchor":"Elf64_auxv_t", "support":"64-bit type/value auxiliary pair layout", "ref_id":"turn806137930view1", "reference_kind":"version-fixed published primary source code"}
]
put("SOURCES.json", {"schema":"ontokin.c271.p11-source-support/1", "local":bindings, "primary_web":web,
    "gaps":["Version-fixed source URLs identify published source; raw source downloads/hashes were not obtained through the web renderer.",
             "No selected operational loader source/build relationship or complete compiled hardware/TLS suffix inventory has been established.",
             "Retained P09/P10 records do not provide complete selected Python extension/transitive closure or expanded-directory entries.",
             "No host observation, target image execution or production parser invocation was performed in P11."],
    "citation_policy":"Local IDs bind exact bytes; web IDs point to primary code/manuals and distinguish immutable version references from mutable renderings. Patch discussion is not deployment evidence."})

protected = [
 "prototypes/static_tray_v01/current_host_inspection_v01.py", "prototypes/static_tray_v01/current_host_readback_v01.py", "prototypes/static_tray_v01/current_host_readback_v01.mjs",
 "tests/test_current_host_inspection_v01.py", "tests/test_current_host_elf_mapping_v01.py", "tests/test_current_host_readback_provider.py", "tests/test_current_host_readback_driver.py", "tests/test_static_tray_readback_v01.py",
 "prototypes/static_tray_v01/readback.mjs", "prototypes/static_tray_v01/format_check.py", "prototypes/static_tray_v01/supervisor.py", "tools/check_local.py", "tools/prepare_current_host_readback.py",
 "tools/force-agent-verification-requirements.txt", "tools/native-reader-verification-linux-cp312.lock",
 "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md", "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.json", "docs/engineering/localized-repair-c271/current-host-p05/ADOPTION.json",
 "docs/engineering/localized-repair-c271/current-host-p06/SCHEMA.json", "docs/engineering/localized-repair-c271/host-inspection-p07/HOST-INSPECTION-DESIGN.md", "docs/engineering/localized-repair-c271/host-inspection-p07/QUALIFICATION-PLAN.md", "docs/engineering/localized-repair-c271/host-inspection-p07/ADOPTION.json"
]
put("PROTECTED-SOURCES.json", {"schema":"ontokin.c271.p11-protected-source-identities/1", "source_commit_supplied_by_director":"e0119f376441fee0fc3956852ac63110ab141011",
    "files":[{"path":p, **digest(repo/p)} for p in protected], "claim":"Static current-byte inventory; Director independently owns Git source equality and all-repository protected-file comparison", "product_files_written_by_author":[]})

surface = [
 {"path":"prototypes/static_tray_v01/current_host_inspection_v01.py", "symbols":["new exact plan/profile/variant constants", "_plan_shape"], "change":"Add closed schema/profile pair dispatch; old pair and fixed command stdout_predicate stay exact", "checks":"L01-L07; N01-N07; N32; no old-schema field admission"},
 {"path":"prototypes/static_tray_v01/current_host_inspection_v01.py", "symbols":["private shared byte-reader seam", "private plan-selected raw metadata reader", "read_elf_metadata"], "change":"Permit raw exact subject token only through authenticated new plan route; public signature and default stay unchanged; all raw result keys remain", "checks":"All 175 existing methods; L01-L07; P01/P05; N33-N50; no production parser call in P11"},
 {"path":"prototypes/static_tray_v01/current_host_inspection_v01.py", "symbols":["new private bounded kernel-origin/auxv reader", "new private guarded-origin rule"], "change":"Bound current process executable, nonsecure state, direct role, canonical origin and one guarded sibling expansion", "checks":"P01/P06/P07; N08-N32; N51/N52/N69/N73; F01-F03"},
 {"path":"prototypes/static_tray_v01/current_host_inspection_v01.py", "symbols":["_check_author_runtime", "_check_resolution"], "change":"Use same plan-specific admission at both existing parser sites; compare raw metadata; only derived path is checked against search inventory; verify full union and nonselection", "checks":"P02-P04; N53-N68; exact image and current process bindings; no synthetic operational pin substitution"},
 {"path":"prototypes/static_tray_v01/current_host_inspection_v01.py", "symbols":["_validate", "_recheck", "_required_paths", "_input_snapshot", "_launch_check"], "change":"Complete proof before Git/commands/STATIC_READY; repeat on all full rechecks; include every added path/absence/ref descriptor; final small kernel witness under existing clock", "checks":"D01-D03 and F01-F03; inherited process/source/path/clock controls; current failure wrapper retained"},
 {"path":"tests/test_current_host_loader_path_v01.py", "symbols":["new independently reviewed adapter/tests only"], "change":"Consume immutable P11 corpus and explicit synthetic seams; add no false operational positive", "checks":"Exact fixture and EXPECTATIONS digests; require callback injection actually triggered; preserve old files and discovery inventory"}
]
preserve = [
 {"id":"K01", "obligation":"Public standalone token refusal, literal RPATH/RUNPATH outputs and exact old plan/profile", "evidence":"L01-L07; old tests unchanged", "future_check":"Run complete 135 existing inspection methods plus 40 P10 mapping controls; compare no new failures/errors/skips; do not rewrite expected refusals"},
 {"id":"K02", "obligation":"P10 interval mapping, ELF bounds/flags/uniqueness/ASCII/read/identity/fd/callback guards", "evidence":"L01/L12/L15/L16", "future_check":"All existing mapping positive/refusal/fault cases with their exact corpus identities and default parser route"},
 {"id":"K03", "obligation":"P06 Python/JavaScript closed HOST, inspection, process/cleanup, manifest and provider behavior", "evidence":"L02/L05/L14; PROTECTED-SOURCES", "future_check":"Static schema/source comparison; inherited focused provider/driver compatibility as applicable; no fabricated HOST/inspection"},
 {"id":"K04", "obligation":"Exact Node/archive/24 dependency bytes, seven package pins, original seven method/helper/scientific bodies", "evidence":"L03-L07; protected provider/probe/tests/pins", "future_check":"Exact byte/body identity; original seven and real runtime outcomes remain later H3, not these controls"},
 {"id":"K05", "obligation":"Clean environment, ldd script/loader/config/cache/preload/alias/guard closure; exact commands and stdout_predicate", "evidence":"L01/L05/L06", "future_check":"Inherited inspection/mock/failure controls plus explicit unchanged command shape assertion; no new direct executable path"},
 {"id":"K06", "obligation":"Source 100000 operations/30000 ms and all existing static/command/cleanup/evidence budgets; failure/unknown preservation", "evidence":"L01/L03/L05/L06", "future_check":"Exact constants/source checks; injected bounded callback tests; no timeout extension or retries"},
 {"id":"K07", "obligation":"Complete routine/R03, integration/R04 and saved parent closure/R05 remain unmet", "evidence":"P11 PHASE and adopted qualification gates", "future_check":"No focused corpus, metadata or design result relabelled as those later executed gates"}
]
put("FUTURE-SURFACE.json", {"schema":"ontokin.c271.p11-future-surface/1", "implementation_authorized_in_p11":False,
    "proposed_production_edit_paths":["prototypes/static_tray_v01/current_host_inspection_v01.py"],
    "proposed_new_test_paths":["tests/test_current_host_loader_path_v01.py"], "surface":surface, "preservation_matrix":preserve,
    "existing_test_contract_pin_consumer_changes":False,
    "no_execution_in_p11":["production parser", "production imports", "runtime preparation/installation", "Node/ldd", "current product tests", "H0/H1", "original seven", "full routine", "native/model/hosted", "integration"]})

put("AUTHORING-ERRORS.json", {"schema":"ontokin.c271.p11-author-attempts/1", "attempts":[
 {"id":"read-parents", "outcome":"three missing parent AGENTS.md reads", "paths":["/workspace/AGENTS.md", "/workspace/scratch/AGENTS.md", str(workspace/"AGENTS.md")], "disposition":"No parent files exist; full supplied user instructions and repository AGENTS read; no writes"},
 {"id":"search-output-truncations", "outcome":"Initial broad recursive rg encountered large archival/base64 JSON; grouped document reads and one baseline report also truncated", "disposition":"Stopped broad output; reread applicable full instructions/adopted prose in bounded chunks and used targeted source ranges. Baseline full report was not required for new oracle and is not claimed fully read."},
 {"id":"primary-source-fallbacks", "outcome":"GitHub and raw GitHub glibc opens returned DisabledError; sourceware gitweb blob URLs inaccessible; two guessed auxiliary-header URLs unavailable", "disposition":"No same failing fetch replay; retrieved version-fixed published glibc source via Debian Sources and actual versioned auxiliary header URL; no full raw-source hash claimed"},
 {"id":"build001", "command":"python3 -I -S -B session_evidence/loader_design/build_controls.py session_evidence/loader_design/candidate001", "outcome":"exit 0; 93 cases constructed", "constructor_retained":"../build_controls_attempt001.py", "stdout":"../build001.stdout.txt", "stderr":"../build001.stderr.txt"},
 {"id":"static001", "command":"python3 -I -S -B session_evidence/loader_design/validate_artifacts.py session_evidence/loader_design/candidate001", "outcome":"exit 1; one authoring consistency failure", "failure":"P07_expansion_4096_bytes appended hardware suffix paths beyond the same 4096-byte bound", "evidence":"../static001.stdout.json", "disposition":"Candidate001 preserved byte-for-byte. Candidate002 declares that boundary primitive's suffix model base-only and synthetic; no operational or production behavior changes."},
 {"id":"build002", "command":"python3 -I -S -B session_evidence/loader_design/build_controls.py session_evidence/loader_design/candidate002", "outcome":"exit 0; 93 cases constructed", "stdout":"../build002.stdout.txt", "stderr":"../build002.stderr.txt"},
 {"id":"static002", "command":"python3 -I -S -B session_evidence/loader_design/validate_artifacts.py session_evidence/loader_design/candidate002", "outcome":"exit 0; 1084 fixture integrity/layout checks", "evidence":"../static002.stdout.json", "scope":"No product execution or acceptance-rule execution"}
 ], "failed_product_attempts_in_p11":[], "unknown_operations":[], "active_processes":[], "publication_performed":False})

instructions = ["AGENTS.md", "ROLE.md", "docs/workflow/PROTOCOL.md", "docs/workflow/HANDOFF.md", "docs/workflow/templates/WORKER.md"]
put("READ-SET.json", {"schema":"ontokin.c271.p11-worker-read-set/1", "worker":"/root/loader_design",
    "governing_instructions":[{"path":p, **digest(repo/p), "read":"full"} for p in instructions],
    "phase_read":{"path":"docs/engineering/localized-repair-c271/loader-path-p11/PHASE.json", "read":"full before early-save confirmation; Director owns subsequent canonical updates"},
    "source_support":"SOURCES.json", "global_startup_repeated":False, "children_spawned":0,
    "exclusive_writes":"session_evidence/loader_design/", "integration_or_publication_authority":False,
    "early_save_gate":{"confirmed_by":"/root", "library_file_id":"libfile_fde3_f-492c198488408191985f3c5b0b58e1a0_2ab2a24d43748191957f9bcc356b59de", "zip_size_bytes":899708, "zip_sha256":"f8047061fd25c770c92baf260cce31351dc4a5dcb5bbbb7006e4188b9848ae94"}})
print(json.dumps({"records_created":6, "local_sources":len(bindings), "primary_sources":len(web), "protected_files":len(protected)}, sort_keys=True))
