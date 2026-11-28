"""Build CONTROLS-FROZEN.json for C271-P37 stage S4 (author W2). Run as python3 -I -S -B <worktree> <evidence dir>.

It reads the control module statically (ast; never imported), cross-checks every test method against the frozen
table below, hashes the governing sources and the implementation read at freeze, and writes the record into the
phase directory. Paths in the record are repository-relative or labelled; no machine path is written.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path

worktree, evidence = Path(sys.argv[1]), Path(sys.argv[2])
MODULE = "tests/test_current_host_readback_derived_controls_v02.py"
PHASE_DIR = "docs/engineering/localized-repair-c271/derived-workspace-p37"
OUTPUT = PHASE_DIR + "/CONTROLS-FROZEN.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def described(paths):
    return {rel: {"sha256": sha(worktree / rel), "size_bytes": (worktree / rel).stat().st_size} for rel in paths}


# -- common texts -------------------------------------------------------------

BASE = ("a synthetic Git checkout in the resolved temporary directory holding the provider's 0.2.0 source set "
        "(every current_host_readback_v02.SOURCE_FILES path and a file in each SOURCE_TREES tree, synthetic bytes) and, "
        "elsewhere in the copied set, README.md, a .gitignore with no patterns, docs/notes.md, "
        ".agents/skills/alpha/SKILL.md, the generated example examples/visual/demo-data.js and a synthetic "
        "ADOPTION-AMENDMENT-001.json; every file's modification time 600 s in the past; committed with real Git "
        "(init --template=, add --all --force, commit; GIT_CONFIG_GLOBAL=/dev/null, GIT_CONFIG_NOSYSTEM=1, a placeholder "
        "identity); premise: the checkout tracks exactly its tree and is clean")
RECORDS = ("the 0.2.0 source inventory document, computed by the control from the fixture's own files, outside the "
           "checkout; the copied record = tools.check_local.inventory(<original checkout>), which the derivation keeps as "
           "source_before")
WORKSPACE = ("the workspace = tools.check_local.prepare_workspace(<original>, <fresh output>, False): the driver's own copy "
             "of SOURCE_DIRS and ROOT_FILES, its workspace Git (init, fetch, update-ref, read-tree), storage step and index "
             "refresh, every Git start through the logging wrapper, bound with tools.check_local.bind_git before the first "
             "driver Git start; premise: tools.check_local.inventory(<workspace>) equals the copied record")
ISOLATION = ("XDG_CONFIG_HOME names an empty directory (the account's global ignore and attributes files stay out); "
             "tools.check_local._GIT_STATE isolated per control")
WRAPPER = ("a /bin/sh wrapper that logs \"$*\" and execs the Git that shutil.which('git') finds under the test's PATH; "
           "bound by tools.check_local.bind_git")
STANDIN = ("a /bin/sh stand-in for the bound Git, bound through the provider's _bind_git, that answers exactly the source "
           "check's five reads (after -c core.fsmonitor=false -C <root>) from files, exits 97 or 98 on anything else, and "
           "logs each start; the root holds the 0.2.0 source set and the other copied files of the base tree, without Git; "
           "the record = tools.check_local.inventory(<root>); commit a1a1...a1, tree b2b2...b2")
ENTRY = ("prototypes.static_tray_v01.current_host_readback_v02._verify_source(source, git={path, sha256}, derived=True, "
         "own_root=False, copied=<record>), with source = {root: <workspace>, commit, tree, inventory: <the original's "
         "0.2.0 source inventory descriptor>}")
ENTRY_ORIGINAL = ENTRY.replace("derived=True", "derived=False").replace("<workspace>", "<original checkout>")
READS = ["-c core.fsmonitor=false -C <root> rev-parse --show-toplevel",
         "-c core.fsmonitor=false -C <root> rev-parse --verify HEAD^{commit}",
         "-c core.fsmonitor=false -C <root> rev-parse --verify <commit>^{tree}",
         "-c core.fsmonitor=false -C <root> status --porcelain=v1 --untracked-files=no",
         "-c core.fsmonitor=false -C <root> ls-files --others --exclude-standard -z"]


def starts(count, *, program="the bound wrapper", harness="real Git started by the fixture outside the recorded window"):
    return {"node": 0, "other": 0, "code_under_test": {
        "git_starts": count, "program": program if count else "none",
        "argv_after_the_program": READS[:count]},
        "recorded_window": "every subprocess start is recorded; an os-level spawn fails the control; no Node, ldd, "
                           "codesign or otool", "harness": harness}


def real(boundary="none"):
    return {"kind": "real", "boundary": boundary}


SIMULATED_GIT = {"kind": "simulated", "boundary": "the Git boundary: the stand-in answers the five reads with the exact lines"}
MOCKED = {"kind": "mocked", "boundary": ("the provider's _host_git (returns the wrapper's binding), _verify_host (a synthetic "
                                         "HOST with labels, a Python digest and the Git binding), _cross_bindings, "
                                         "_verify_dependencies and _verify_methods; the provider's ROOT is the fixture's "
                                         "original checkout, as when the provider runs from it; the provider then labels "
                                         "its records 'mocked'")}
DERIVATION_INPUTS = ("a config/0.2.0 outside the checkout (mode 0600) with real descriptors of the fixture's CONTRACT.md and "
                     "ADOPTION-AMENDMENT-001.json, source = the original checkout, an existing evidence root outside it, "
                     "parent null, and placeholder host, dependencies, runtime and methods members that the substituted "
                     "functions never read; the driver's output directory beneath the evidence root")

P05 = "P05 CONTRACT.md section 3"
C1 = "0.2.0 CONTRACT.md section 1 (keeps P05's isolated-workspace derivation)"
MC19 = "0.2.0 CONTRACT.md section 9, MC19"
MC21 = "0.2.0 CONTRACT.md section 8 (qualifying run) and section 9, MC21"
D12 = "DECISION-001 section 1.2"


def refused(code, reason, detail=None):
    row = {"outcome": "refused", "code": code, "reason": reason}
    if detail:
        row["detail"] = detail
    return row


def accepted(detail="returns the 0.2.0 source inventory document unchanged"):
    return {"outcome": "accepted", "detail": detail}


C = []


def control(cid, method, title, group, label, inputs, entry, expected, start, sources):
    C.append({"id": cid, "method": method, "title": title, "group": group, "label": label, "inputs": inputs,
              "entry_point": entry, "expected": expected, "starts": start, "sources": sources})


A = "DerivedRouteAcceptanceControls."
R = "DerivedRouteRefusalControls."
O = "OriginalRouteControls."
G = "GeneratedExampleControls."
X = "ExactStatusLineControls."
W = "WorkspaceIndexControls."
FULL = ("the full fixture: the base tree plus .claude/.gitignore, the link .claude/skills/alpha -> ../../.agents/skills/alpha, "
        "the twelve other uncopied paths of control c03 and the copied generated product examples/visual/a.glb; premises: "
        "without a change the workspace's status is exactly the fourteen ' D' lines of the uncopied paths (c03, c40 and "
        "c62 assert it), and after a change it holds the change's line (each refusal control asserts it)")

# -- 1. accepted on the derived route ------------------------------------------
control("P37-C01", A + "test_c01_a_regular_file_outside_the_source_directories_is_accepted",
        "a regular file outside SOURCE_DIRS, as .claude/.gitignore is", "derived route: accepted", real(),
        [BASE + "; the only uncopied path: .claude/.gitignore", RECORDS, WORKSPACE, ISOLATION, WRAPPER,
         "premises: copied_source_path('.claude/.gitignore') is false; the record lists no uncopied path; the copy left it "
         "out; workspace status exactly [' D .claude/.gitignore']; no untracked name"],
        ENTRY, accepted(), starts(5), [P05, C1, MC19, D12 + " rule B", "FZ-01"])
control("P37-C02", A + "test_c02_a_symbolic_link_outside_the_source_directories_is_accepted",
        "a symbolic link outside SOURCE_DIRS, as .claude/skills/* are", "derived route: accepted", real(),
        [BASE + "; the only uncopied path: the link .claude/skills/alpha -> ../../.agents/skills/alpha", RECORDS, WORKSPACE,
         ISOLATION, WRAPPER, "premises as c01; workspace status exactly [' D .claude/skills/alpha']"],
        ENTRY, accepted(), starts(5), [P05, C1, MC19, D12 + " rule B", "FZ-01"])
control("P37-C03", A + "test_c03_every_other_kind_of_tracked_path_that_the_copy_leaves_out_is_accepted",
        "every other kind of tracked path that the copy leaves out, by the decision's definition of the copied set",
        "derived route: accepted", real(),
        [BASE + "; uncopied: .claude/.gitignore, the link .claude/skills/alpha, an executable .claude/hooks/check.sh (100755), "
         "a root file outside ROOT_FILES (Makefile), nested directories (outside/nested/deep/notes.txt), ignored directory "
         "components inside SOURCE_DIRS (tools/build/generated.py, docs/_build/page.html, "
         "tools/node_modules/package/index.js), a link inside an ignored directory (tools/node_modules/.bin/tool -> "
         "../package/index.js), ignored file names (docs/.env, TRDs/.env.local), a link with an ignored name "
         "(docs/.env.example -> ../README.md), bytecode (fixtures/__pycache__/cached.cpython-312.pyc, tools/stale.pyo); "
         "and the copied generated product examples/visual/a.glb", RECORDS, WORKSPACE, ISOLATION, WRAPPER,
         "premises: copied_source_path is false for each; the copy left each out; status exactly their fourteen ' D' lines"],
        ENTRY, accepted(), starts(5), [P05, C1, MC19, D12 + " rule B", "DECISION-001 sections 3 and 6"])
control("P37-C04", A + "test_c04_the_real_trees_seven_uncopied_entries_are_accepted",
        "FZ-01's shape: the real tree's seven uncopied entries", "derived route: accepted", real(),
        [BASE + "; uncopied: .claude/.gitignore and the six links .claude/skills/<name> -> ../../.agents/skills/<name> for "
         "communication, ontokin-delivery, ontokin-learning, ontokin-session, to-implementation-plan and to-trd, with "
         ".agents/skills/<name>/SKILL.md copied", RECORDS, WORKSPACE, ISOLATION, WRAPPER,
         "premise: status exactly the seven lines of S2's measurement (MEASURE-001), in that order"],
        ENTRY, accepted(), starts(5), [P05, C1, MC19, D12 + " rule B", "FZ-01", "<local>/c271-p37/measure/MEASURE-001.json"])
control("P37-C05", A + "test_c05_the_derivation_and_the_unit_selection_accept_the_seven_entries",
        "the derivation entry and the unit process's selection check accept the seven entries", "derived route: accepted",
        MOCKED, ["c04's fixture", DERIVATION_INPUTS, WORKSPACE + " (output beneath the evidence root)", ISOLATION, WRAPPER],
        ("tools.check_local.bind_readback_workspace(selection, root, workspace, output, source_before=<record>, "
         "workspace_inventory=inventory(<workspace>)), which reaches the 0.2.0 derive_workspace_binding through the "
         "0.1.0 facade; then current_host_readback_v02._selection(<derived config>, <digest>, <workspace>) with the "
         "provider's ROOT = the workspace, as the unit process checks it"),
        accepted("returns config_path (<output>/readback-binding/selection.json, whose SHA-256 is config_sha256), "
                 "config_sha256, parent_config_sha256 (the original's), workspace_binding_path and workspace_binding_sha256; "
                 "source-before.json holds the record; the derived config's source root is the workspace and its parent's "
                 "source_root the original; the unit selection returns the derived config"),
        {"node": 0, "other": 0, "code_under_test": {
            "git_starts": "15 for the derivation, then 5 for the unit selection", "program": "the bound wrapper",
            "argv_after_the_program": ["the five reads at <original> (original selection)",
                                       "the five reads at <workspace> (git_metadata of the workspace)",
                                       "the five reads at <workspace> (derived selection)",
                                       "unit selection: the five reads at <workspace>"]},
         "harness": "real Git started by the fixture outside the recorded window"},
        [P05, C1, MC19, "DECISION-001 sections 1.1 and 3", "FZ-01"])
control("P37-C06", A + "test_c06_the_derivation_still_refuses_an_untracked_input_and_a_staged_change",
        "the derivation's own source check still refuses an untracked input and a staged change", "derived route: refused",
        MOCKED, ["c05's inputs, a fresh world per subtest; after the copy, outside the copied set, so that the inventories "
                 "stay equal: (a) an untracked .claude/new_control_input.txt; (b) git rm --cached .claude/.gitignore in "
                 "the workspace"],
        "tools.check_local.bind_readback_workspace, as c05",
        {"(a) untracked input": refused("CH-SOURCE", "Untracked source input: .claude/new_control_input.txt"),
         "(b) staged deletion": refused("CH-SOURCE", "Dirty source: D  .claude/.gitignore"),
         "detail": "current_host_readback_v02.CurrentHostBindingError propagates out of bind_readback_workspace"},
        {"node": 0, "other": 0, "code_under_test": {"git_starts": "(a) 15; (b) 14", "program": "the bound wrapper",
                                                    "argv_after_the_program": ["as c05, ending after the derived check's "
                                                                               "fifth read (a) or fourth read (b)"]}},
        [P05, MC19, "DECISION-001 sections 1.2 and 1.3"])
control("P37-C07", A + "test_c07_a_qualifying_run_passes_its_preparation_with_the_derived_binding",
        "a qualifying run passes its preparation with the derived binding (the path R1 refused at)", "derived route: accepted",
        {"kind": "mocked", "boundary": MOCKED["boundary"] + "; the plan has no step; platform.platform is a stand-in leaf"},
        ["c04's fixture", DERIVATION_INPUTS + "; the run's output is a fresh absent directory beneath the evidence root",
         ISOLATION, "check_local._GIT_STATE None at the start, so the run binds the wrapper from the selection (S9)"],
        "tools.check_local.run(<original>, <output>, False, 60, readback_config=<config>, readback_config_sha256=<digest>)",
        accepted("exit 0, status passed; readback_selection status workspace_bound with run_kind qualifying, a derived "
                 "member of five keys and no preparation_or_execution_error; git_binding = the wrapper, bound, source "
                 "selection; workspace_git.tracked_worktree_status = the seven lines; steps []; source_unchanged true"),
        {"node": 0, "other": 0, "code_under_test": {
            "git_starts": "Git only (46 observed at freeze; the count is not frozen)", "program": "the bound wrapper",
            "argv_after_the_program": ["exactly one update-index -q --refresh in <output>/workspace",
                                       "the derived check's five reads at <output>/workspace, consecutively"]}},
        [P05, C1, MC21, MC19, "DECISION-001 sections 1.1 and 4.4", "FZ-01"])

# -- 2. refused on the derived route -------------------------------------------
REFUSAL_INPUTS = [FULL, BASE, RECORDS, WORKSPACE, ISOLATION, WRAPPER]


def refusal(cid, name, title, change, expected, count, sources, label=None):
    control(cid, R + name, title, "derived route: refused", label or real(),
            REFUSAL_INPUTS + ["change in the workspace after the preparation: " + change], ENTRY, expected, starts(count),
            sources)


refusal("P37-C10", "test_c10_a_modified_copied_file_is_refused", "a modified copied file",
        "docs/notes.md (copied, outside the 0.2.0 source set) gets other bytes",
        refused("CH-SOURCE", "Dirty source:  M docs/notes.md"), 4, [P05, MC19, D12])
refusal("P37-C11", "test_c11_a_deleted_copied_file_is_refused", "a deleted copied file",
        "one subtest each: docs/notes.md, README.md, .agents/skills/alpha/SKILL.md deleted",
        refused("CH-SOURCE", "Dirty source:  D <path>", "<path> is the deleted file"), 4,
        [P05, MC19, D12 + " condition 4"])
refusal("P37-C12", "test_c12_a_same_size_change_with_the_old_modification_time_is_refused_after_the_refresh",
        "a same-size change with the old modification time, after the refresh (FZ-02)",
        "1.2 s after the preparation, docs/notes.md gets other bytes of the same size; its access and modification times "
        "are set back (premise: size and mtime equal the copy's)",
        refused("CH-SOURCE", "Dirty source:  M docs/notes.md"), 4, [P05, MC19, "DECISION-001 sections 4.4 and 6"])
refusal("P37-C13", "test_c13_a_retyped_copied_file_is_refused", "a retyped copied file",
        "docs/notes.md replaced by a link to ../README.md",
        refused("CH-SOURCE", "Dirty source:  T docs/notes.md"), 4, [P05, MC19, D12])
refusal("P37-C14", "test_c14_a_staged_change_is_refused", "a staged change",
        "one subtest each, staged with real Git in the workspace: git rm --cached .claude/.gitignore; git rm --cached "
        "docs/notes.md; docs/notes.md changed and added; changed, added and changed again; a new tools/staged_input.py "
        "added; a new outside/staged_input.txt added",
        refused("CH-SOURCE", "Dirty source: <line>", "the lines: 'D  .claude/.gitignore', 'D  docs/notes.md', "
                "'M  docs/notes.md', 'MM docs/notes.md', 'A  tools/staged_input.py', 'A  outside/staged_input.txt'"), 4,
        [P05, MC19, D12 + " condition 1"])
refusal("P37-C15", "test_c15_a_rename_line_is_refused", "a rename line",
        "one subtest each, with real Git: git mv docs/notes.md docs/renamed.md; .claude/.gitignore restored with the "
        "commit's bytes, then git mv to .claude/moved.txt; git mv examples/visual/a.glb examples/visual/b.glb",
        refused("CH-SOURCE", "Dirty source: <line>", "the lines: 'R  docs/notes.md -> docs/renamed.md', "
                "'R  .claude/.gitignore -> .claude/moved.txt', 'R  examples/visual/a.glb -> examples/visual/b.glb' (rule A "
                "still requires no ' -> ')"), 4, [P05, MC19, D12 + " rules A and B condition 2"])
refusal("P37-C16", "test_c16_an_uncopied_path_whose_name_git_quotes_is_refused", "a quoted name",
        "none; the fixture also tracks, outside the copied set, .claude/quote\"mark.txt (one subtest) or .claude/na\\u00efve.txt "
        "(the other)",
        refused("CH-SOURCE", "Dirty source: <line>", "the lines Git prints: ' D \".claude/quote\\\"mark.txt\"' and "
                "' D \".claude/na\\303\\257ve.txt\"'"), 4, [P05, D12 + " condition 2", "DECISION-001 section 6"])
refusal("P37-C17", "test_c17_an_uncopied_path_that_is_present_but_changed_is_refused",
        "an uncopied path that is present but changed",
        "one subtest each: .claude/.gitignore with other bytes; a regular file at the link's path; the link with another "
        "target; .claude/hooks/check.sh with the commit's bytes and mode 0644; Makefile with other bytes; "
        "tools/build/generated.py with other bytes; an intent-to-add entry outside/intent_to_add.txt",
        refused("CH-SOURCE", "Dirty source: <line>", "the lines: ' M .claude/.gitignore', ' T .claude/skills/alpha', "
                "' M .claude/skills/alpha', ' M .claude/hooks/check.sh', ' M Makefile', ' M tools/build/generated.py', "
                "' A outside/intent_to_add.txt'"), 4, [P05 + " (extra executable inputs)", MC19, D12 + " condition 1"])
refusal("P37-C18", "test_c18_an_uncopied_path_replaced_by_a_directory_holding_a_file_is_refused",
        "an uncopied path replaced by a directory holding a file",
        "Makefile becomes a directory holding inner.txt (premise: ' D Makefile' in the status)",
        refused("CH-SOURCE", "Untracked source input: Makefile/inner.txt",
                "the deletion line is admitted; the untracked file in its place refuses"), 5,
        [P05 + " (extra executable inputs)", "DECISION-001 section 1.3"])
refusal("P37-C19", "test_c19_an_untracked_input_inside_the_copied_set_is_refused",
        "an untracked input inside the copied set",
        "one subtest each, an untracked file: tools/new_control_input.py, docs/new_control_input.md, "
        ".agents/new_control_input.md, .lfsconfig (a ROOT_FILES name); premise: copied_source_path is true",
        refused("CH-SOURCE", "Untracked source input: <name>"), 5, [P05, MC19, "DECISION-001 section 1.3"])
refusal("P37-C20", "test_c20_an_untracked_input_outside_the_copied_set_is_refused",
        "an untracked input outside the copied set (the decision keeps it)",
        "one subtest each, an untracked file: .claude/new_control_input.txt, outside/new_control_input.txt, "
        "Makefile.local, tools/build/new_control_input.py; premise: copied_source_path is false",
        refused("CH-SOURCE", "Untracked source input: <name>"), 5,
        [P05 + " (extra executable inputs)", "DECISION-001 section 1.3"])
refusal("P37-C21", "test_c21_the_source_sets_binding_still_refuses_before_any_git_read",
        "the source set's binding: missing source, an added source-tree file, a changed provider or probe",
        "one subtest each, a fresh workspace: pyproject.toml (a source role) deleted; ontokin/control_fixture.txt deleted; "
        "an added tests/new_control_input.py; the provider changed; the probe changed",
        {"a missing source role": refused("CH-SOURCE", "Bound path or ancestor is missing: <workspace>/pyproject.toml",
                                          "the observer's path check, which the source set's walk applies first"),
         "a missing or an added source-tree file": refused("CH-SOURCE", "Complete CPU source inventory differs"),
         "a changed provider or probe": refused("CH-SOURCE", "Locked file identity differs: <workspace>/<file>"),
         "basis of the reasons": "the unchanged binding's reasons at the declaration commit"}, 0,
        [P05 + " (missing source, changes after the inventory was frozen)", MC19])
control("P37-C22", R + "test_c22_another_checkout_an_unbound_git_and_another_commit_or_tree_are_refused",
        "MC19's other cases on the derived route", "derived route: refused", real(), REFUSAL_INPUTS + [
            "one subtest each, with the record given: own_root=True (the workspace is not the provider's checkout); "
            "git=None; source.commit 000...0; source.tree 000...0"],
        ENTRY + "; own_root and git as each subtest says",
        {"another checkout": refused("CH-SOURCE", "Provider belongs to another source checkout"),
         "no Git binding": refused("CH-SOURCE", "Source reads require the selection's bound Git executable"),
         "another commit or tree": refused("CH-SOURCE", "Source commit/tree differs or is unavailable")},
        {"node": 0, "other": 0, "code_under_test": {"git_starts": "0, 0, 2 and 3", "program": "the bound wrapper",
                                                    "argv_after_the_program": ["the first reads of the source check, in order"]}},
        [MC19, "S9"])
control("P37-C23", R + "test_c23_a_symbolic_link_inside_the_copied_set_is_refused_by_the_driver",
        "a symbolic link inside the copied set", "derived route: refused", real(),
        ["the full fixture plus a tracked link tools/linked.py -> ../README.md (copied_source_path true), committed and "
         "clean; source_git = git_metadata(<original>) taken before the window", ISOLATION, WRAPPER],
        "tools.check_local.inventory(<original>); tools.check_local.prepare_workspace(<original>, <output>, False, source_git=...)",
        {"inventory": refused("ValueError", "Source file is a symbolic link: <original>/tools/linked.py"),
         "copy": refused("ValueError", "Cannot copy a source symbolic link: <original>/tools/linked.py"),
         "side_effects": "no workspace .git; no derived workspace reaches the provider"},
        {"node": 0, "other": 0, "code_under_test": {"git_starts": 0, "program": "none", "argv_after_the_program": []}},
        [P05, "DECISION-001 section 3"])
refusal("P37-C24", "test_c24_a_source_tree_file_that_the_copy_leaves_out_is_refused_as_missing_source",
        "a tracked file of a 0.2.0 source tree that the copy leaves out (finding F-01)",
        "none; the fixture also tracks, inside a source tree but with an ignored() component, ontokin/.env (one subtest) or "
        "prototypes/static_tray_v01/build/helper.py (the other); premises: it is in the source inventory, copied_source_path "
        "is false, the original route accepts the clean checkout (five reads), the copy leaves it out and its ' D' line "
        "is in the workspace's status",
        refused("CH-SOURCE", "Complete CPU source inventory differs",
                "rule B alone would admit its deletion line; the source set's binding refuses first"), 0,
        [P05 + " (missing source)", MC19, "DECISION-001 section 2 ('Not missing source')"])

# -- original route -------------------------------------------------------------
control("P37-C30", O + "test_c30_an_uncopied_file_deleted_in_the_original_checkout_is_refused",
        "the original route: an uncopied file deleted", "original route: refused", real(),
        ["c04's fixture, .claude/.gitignore deleted in the original checkout", RECORDS, ISOLATION, WRAPPER],
        ENTRY_ORIGINAL + "; one subtest with the record, one with copied=None",
        refused("CH-SOURCE", "Dirty source:  D .claude/.gitignore"), starts(4),
        [P05, MC19, "DECISION-001 section 1.4"])
control("P37-C31", O + "test_c31_an_uncopied_link_deleted_in_the_original_checkout_is_refused",
        "the original route: an uncopied link deleted", "original route: refused", real(),
        ["c04's fixture, the link .claude/skills/communication deleted in the original checkout", RECORDS, ISOLATION, WRAPPER],
        ENTRY_ORIGINAL + "; with the record and with copied=None",
        refused("CH-SOURCE", "Dirty source:  D .claude/skills/communication"), starts(4),
        [P05, MC19, "DECISION-001 section 1.4"])
control("P37-C32", O + "test_c32_an_original_checkout_without_any_uncopied_path_is_refused",
        "the original route: every uncopied path deleted, as a workspace lacks them", "original route: refused", real(),
        ["the full fixture with all fourteen uncopied paths deleted in the original checkout", RECORDS, ISOLATION, WRAPPER],
        ENTRY_ORIGINAL + "; with the record and with copied=None",
        refused("CH-SOURCE", "Dirty source:  D .claude/.gitignore", "the first line"), starts(4),
        [P05, MC19, "DECISION-001 section 1.4"])
control("P37-C33", O + "test_c33_the_derived_workspace_read_as_an_original_is_refused",
        "the driver's workspace checked with derived=False", "original route: refused", real(),
        ["c04's fixture and its workspace", RECORDS, WORKSPACE, ISOLATION, WRAPPER],
        ENTRY.replace("derived=True", "derived=False") + "; with the record and with copied=None",
        refused("CH-SOURCE", "Dirty source:  D .claude/.gitignore"), starts(4), [MC19, "DECISION-001 section 1.4"])
control("P37-C34", O + "test_c34_a_qualifying_run_whose_original_checkout_lacks_an_uncopied_path_fails_preparation",
        "a qualifying run whose original checkout lacks an uncopied path fails preparation", "original route: refused",
        {"kind": "mocked", "boundary": MOCKED["boundary"] + "; the plan has one step; platform.platform is a stand-in leaf"},
        ["c04's fixture", DERIVATION_INPUTS, ".claude/.gitignore deleted in the original checkout after the configuration "
         "was written", "one planned step sys.executable -I -S -B -c 'raise SystemExit(7)', which must never start", ISOLATION],
        "tools.check_local.run(<original>, <output>, False, 60, readback_config=<config>, readback_config_sha256=<digest>)",
        refused("failed preparation", "Dirty source:  D .claude/.gitignore",
                "exit 1, status failed, error = the reason; readback_selection status preparation_pending, run_kind "
                "qualifying, preparation_or_execution_error = the reason; steps [], not_executed_steps ['control-unit']; "
                "no workspace_git and no workspace"),
        {"node": 0, "other": 0, "code_under_test": {"git_starts": 4, "program": "the bound wrapper",
                                                    "argv_after_the_program": [r.replace("<root>", "<original>") for r in READS[:4]]},
         "step_starts": 0},
        [MC21, MC19, "DECISION-001 section 1.4"])
control("P37-C35", O + "test_c35_generated_example_changes_still_refuse_on_the_original_route",
        "unchanged: generated examples refuse on the original route", "original route: refused", real(),
        ["the full fixture; (a) examples/visual/demo-data.js changed in the original checkout; (b) a fresh fixture with an "
         "untracked examples/visual/scene.glb", RECORDS, ISOLATION, WRAPPER],
        ENTRY_ORIGINAL + "; (a) with the record and with copied=None; (b) copied=None",
        {"(a)": refused("CH-SOURCE", "Dirty source:  M examples/visual/demo-data.js"),
         "(b)": refused("CH-SOURCE", "Untracked source input: examples/visual/scene.glb")},
        {"node": 0, "other": 0, "code_under_test": {"git_starts": "(a) 4, (b) 5", "program": "the bound wrapper",
                                                    "argv_after_the_program": READS}},
        [P05, "DECISION-001 sections 1.4 and 5"])

# -- 3. generated examples, derived route -------------------------------------------
control("P37-C40", G + "test_c40_each_change_of_a_generated_example_is_accepted_beside_the_uncopied_paths",
        "unchanged rule A: each generated-example change is accepted beside the uncopied paths", "derived route: accepted",
        real(), REFUSAL_INPUTS + ["one subtest each, in the workspace: examples/visual/demo-data.js changed (' M'); deleted "
                                  "(' D'); changed and staged ('M  '); untracked generated products "
                                  "examples/visual/scene.glb, examples/agent/workflow.json and "
                                  "examples/construction/program.bundle.json"],
        ENTRY, accepted(), starts(5), [P05 + " (the driver's existing generated exclusion)", D12 + " rule A",
                                       "DECISION-001 section 5"])
control("P37-C41", G + "test_c41_all_generated_example_changes_together_are_accepted",
        "unchanged rule A: the changed example and the untracked products together", "derived route: accepted", real(),
        REFUSAL_INPUTS + ["examples/visual/demo-data.js changed and the three untracked products, in one workspace"],
        ENTRY, accepted(), starts(5), [P05, D12 + " rule A"])

# -- exact lines (simulated Git boundary) -----------------------------------------
LINES = [STANDIN, ISOLATION]
EXACT_ENTRY = ENTRY.replace("<workspace>", "<stand-in root>").replace(
    "<the original's 0.2.0 source inventory descriptor>", "<the root's 0.2.0 source inventory descriptor>")
control("P37-C50", X + "test_c50_the_deletion_of_a_path_outside_the_copied_set_is_admitted",
        "' D P' admitted for P outside the copied set", "derived route: accepted", SIMULATED_GIT,
        LINES + ["one subtest each, the status ' D P' for P in: .claude/.gitignore, .claude/skills/alpha, the twelve other "
                 "uncopied paths of c03, ontokin/.env, tests/__pycache__/cached.cpython-312.pyc, LICENSE/inner.txt, "
                 "'.claude/two words.txt' unquoted, Docs/other.md; and the seven lines of the real tree together; premise: "
                 "copied_source_path(P) is false"],
        EXACT_ENTRY, accepted(), starts(5, program="the stand-in", harness="none"), [P05, D12 + " rule B", "DECISION-001 section 6"])
control("P37-C51", X + "test_c51_every_other_status_form_of_an_uncopied_path_is_refused",
        "every other status form of an uncopied path", "derived route: refused", SIMULATED_GIT,
        LINES + ["one subtest each, the status 'XY .claude/.gitignore' for XY in 'D ', ' M', 'M ', 'MM', 'MD', ' T', 'T ', "
                 "'TM', 'A ', ' A', 'AM', 'AD', 'DD', 'AU', 'UD', 'UA', 'DU', 'AA', 'UU', '??', '!!'"],
        EXACT_ENTRY, refused("CH-SOURCE", "Dirty source: <line>"), starts(4, program="the stand-in", harness="none"),
        [P05, MC19, D12 + " condition 1"])
control("P37-C52", X + "test_c52_the_deletion_of_a_path_inside_the_copied_set_is_refused",
        "' D P' refused for P inside the copied set", "derived route: refused", SIMULATED_GIT,
        LINES + ["one subtest each, ' D P' for P in: README.md, pyproject.toml, .gitignore, .gitattributes, .lfsconfig, "
                 "docs/notes.md, tests/control_fixture.txt, tools/linked.py (a link inside), tools/sub (a submodule path "
                 "inside), .agents/skills/alpha/SKILL.md, TRDs/INDEX.md, .github/workflows/check.yml, tools/Build/x.py (a "
                 "case variant of an ignored name, which ignored() does not match), tests, "
                 "prototypes/static_tray_v01/current_host_readback_v02.py; premise: copied_source_path(P) is true"],
        EXACT_ENTRY, refused("CH-SOURCE", "Dirty source:  D <P>"), starts(4, program="the stand-in", harness="none"),
        [P05 + " (complete copied immutable-source inventory)", MC19, D12 + " condition 4", "DECISION-001 section 3"])
control("P37-C53", X + "test_c53_rename_and_copy_lines_are_refused", "rename and copy lines", "derived route: refused",
        SIMULATED_GIT,
        LINES + ["one subtest each: 'R  .claude/a -> .claude/b', 'C  .claude/a -> .claude/b', 'RM .claude/a -> .claude/b', "
                 "'CM .claude/a -> .claude/b', ' R .claude/a -> .claude/b', 'R  docs/notes.md -> .claude/b', "
                 "'R  .claude/a -> docs/b.md', ' D .claude/a -> b', 'R  examples/visual/a.glb -> examples/visual/b.glb', "
                 "' D examples/visual/a.glb -> examples/visual/b.glb'"],
        EXACT_ENTRY, refused("CH-SOURCE", "Dirty source: <line>"), starts(4, program="the stand-in", harness="none"),
        [MC19, D12 + " rules A and B condition 2"])
control("P37-C54", X + "test_c54_quoted_names_are_refused", "quoted names", "derived route: refused", SIMULATED_GIT,
        LINES + ["one subtest each: ' D \".claude/two words.txt\"', ' D \".claude/na\\303\\257ve.txt\"', "
                 "' D \".claude/quote\\\"mark.txt\"', ' M \"examples/visual/two words.glb\"', "
                 "' D \"examples/visual/two words.glb\"'"],
        EXACT_ENTRY, refused("CH-SOURCE", "Dirty source: <line>"), starts(4, program="the stand-in", harness="none"),
        [D12 + " rules A and B condition 2", "DECISION-001 section 6"])
control("P37-C55", X + "test_c55_unsafe_names_are_refused", "unsafe names", "derived route: refused", SIMULATED_GIT,
        LINES + ["one subtest each: ' D ../escape', ' D ./outside', ' D outside//notes', ' D /outside/notes', "
                 "' D outside/', ' D ' (no name), ' D .claude/../README.md' (names a copied file through '..'), "
                 "' D .claude/./x', ' D .'"],
        EXACT_ENTRY, refused("CH-SOURCE", "Dirty source: <line>"), starts(4, program="the stand-in", harness="none"),
        [D12 + " condition 3"])
control("P37-C56", X + "test_c56_a_case_variant_of_a_recorded_copied_file_is_refused",
        "a case variant of a recorded copied file", "derived route: refused, and one accepted", SIMULATED_GIT,
        LINES + ["premise: the record holds docs/notes.md, README.md, tests/control_fixture.txt and "
                 ".agents/skills/alpha/SKILL.md; one subtest each: ' D Docs/notes.md', ' D DOCS/NOTES.MD', ' D readme.md', "
                 "' D README.MD', ' D Tests/control_fixture.txt', ' D .AGENTS/skills/alpha/SKILL.md' (copied_source_path "
                 "false for each); and ' D Docs/other.md'"],
        EXACT_ENTRY, {"case variants": refused("CH-SOURCE", "Dirty source: <line>"),
                      "' D Docs/other.md'": accepted()},
        {"node": 0, "other": 0, "code_under_test": {"git_starts": "4 for each refusal, 5 for the acceptance",
                                                    "program": "the stand-in", "argv_after_the_program": READS}},
        [P05 + " (complete copied immutable-source inventory)", D12 + " condition 6", "DECISION-001 section 6"])
control("P37-C57", X + "test_c57_a_derived_check_without_a_well_formed_record_admits_no_deletion",
        "no record, or a malformed record", "derived route: refused", SIMULATED_GIT,
        LINES + ["status ' D .claude/.gitignore'; copied=None; then one subtest each with copied = [], {}, {'files': None}, "
                 "{'files': 'README.md'}, {'files': [{'path': 1}]}, {'files': [['README.md']]}, {'files': [{}]}, 'text', "
                 "{'files': [{'path': 'README.md'}, 3]}"],
        EXACT_ENTRY.replace("copied=<record>", "copied=<as each case says>"),
        {"copied=None": refused("CH-SOURCE", "Dirty source:  D .claude/.gitignore"),
         "malformed": refused("CH-WORKSPACE", "The copied-source inventory record is malformed", "before any Git start")},
        {"node": 0, "other": 0, "code_under_test": {"git_starts": "4 without a record; 0 with a malformed record",
                                                    "program": "the stand-in", "argv_after_the_program": READS[:4]}},
        [D12 + " condition 5 and the malformed record"])
control("P37-C58", X + "test_c58_the_original_route_refuses_every_line_with_or_without_a_record",
        "the original route refuses every line", "original route: refused", SIMULATED_GIT,
        LINES + ["derived=False; one subtest each, with the record and with copied=None: ' D .claude/.gitignore', "
                 "' D .claude/skills/alpha', ' D Makefile', ' D tools/build/generated.py', "
                 "' M examples/visual/demo-data.js', ' D examples/visual/demo-data.js'"],
        EXACT_ENTRY.replace("derived=True", "derived=False"), refused("CH-SOURCE", "Dirty source: <line>"),
        starts(4, program="the stand-in", harness="none"), [MC19, "DECISION-001 section 1.4"])
control("P37-C59", X + "test_c59_generated_examples_and_untracked_names_keep_their_rules",
        "unchanged: generated examples and untracked names", "derived and original routes", SIMULATED_GIT,
        LINES + ["(a) copied=None and the status ' M examples/visual/demo-data.js', 'M  examples/visual/demo-data.js', "
                 "' D examples/agent/workflow.json', 'MM examples/construction/main.ok', ' D examples/visual/scene.glb'; "
                 "(b) the untracked names tools/new_control_input.py, docs/new_control_input.md, "
                 ".claude/new_control_input.txt, outside/new_control_input.txt, Makefile.local, .lfsconfig; "
                 "(c) the untracked generated products examples/visual/fresh.glb, examples/agent/fresh.export.json, on both "
                 "routes"],
        EXACT_ENTRY.replace("copied=<record>", "copied=<as each case says>"),
        {"(a)": accepted(), "(b)": refused("CH-SOURCE", "Untracked source input: <name>"),
         "(c) derived": accepted(), "(c) original": refused("CH-SOURCE", "Untracked source input: <name>")},
        {"node": 0, "other": 0, "code_under_test": {"git_starts": 5, "program": "the stand-in", "argv_after_the_program": READS}},
        [P05 + " (generated exclusion)", "DECISION-001 sections 1.2 (rule A), 1.3 and 5"])

# -- 4. FZ-02 ---------------------------------------------------------------------------
BASELINE = "the comparison baseline substitutes tools.check_local.refresh_workspace_index with a no-op"
control("P37-C60", W + "test_c60_the_preparation_makes_exactly_one_more_git_start_the_refresh",
        "FZ-02: the preparation makes exactly one more Git start, the refresh", "FZ-02", real(BASELINE),
        [FULL, BASE, ISOLATION, WRAPPER, "two preparations of the same original, with and without the refresh, each in a "
                                         "fresh output; every start recorded, with each run's timeout"],
        "tools.check_local.prepare_workspace(<original>, <output>, False)",
        {"outcome": "accepted (prepared)", "detail": (
            "with the paths labelled, the refreshed sequence equals the baseline sequence plus one last start, "
            "[<git>, -c, core.fsmonitor=false, -C, <output>/workspace, update-index, -q, --refresh], whose allowance is "
            "120 s; no status read of the workspace precedes it; the baseline makes no refresh")},
        {"node": 0, "other": 0, "code_under_test": {"git_starts": "the baseline's starts plus one", "program": "the bound wrapper",
                                                    "argv_after_the_program": ["-c core.fsmonitor=false -C <output>/workspace "
                                                                               "update-index -q --refresh (the last)"]}},
        ["DECISION-001 sections 4.4 and 4.5", "interfaces/W1-CORRECTION.md section 2.1", "FZ-02"])
control("P37-C61", W + "test_c61_the_refresh_records_stat_data_for_the_copied_entries_only_and_changes_no_entry",
        "FZ-02: stat data for the copied entries only; no entry changed", "FZ-02", real(BASELINE),
        [FULL, BASE, ISOLATION, WRAPPER, "two workspaces of the same original, with and without the refresh; each "
                                         "workspace's .git/index read by the control without Git (versions 2 to 4); the "
                                         "commit's tree from ls-tree -r -z in the original (harness)"],
        "tools.check_local.prepare_workspace, then the index files",
        {"outcome": "accepted (prepared)", "detail": (
            "both indexes hold exactly the commit's paths, each with the commit's mode and object and stage 0; without the "
            "refresh every entry's stat data is zero; with it, every copied entry has a nonzero ctime and the workspace "
            "file's mtime seconds, inode and size (32-bit), and every uncopied entry keeps zero stat data")},
        {"node": 0, "other": 0, "code_under_test": {"git_starts": "as c60", "program": "the bound wrapper",
                                                    "argv_after_the_program": []}},
        ["DECISION-001 section 4.4 ('records stat data only for entries whose copied bytes hash to the commit's objects'; "
         "'changes no entry's path, mode, object or stage')", "FZ-02"])
control("P37-C62", W + "test_c62_status_lines_and_the_derived_outcome_are_the_same_with_and_without_the_refresh",
        "FZ-02: the same status lines and outcomes with and without the refresh", "FZ-02", real(BASELINE),
        [FULL, BASE, RECORDS, ISOLATION, WRAPPER, "one subtest with and one without the refresh; then docs/notes.md "
                                                  "changed in each workspace"],
        ENTRY, {"before the change": accepted(), "after the change": refused("CH-SOURCE", "Dirty source:  M docs/notes.md")},
        {"node": 0, "other": 0, "code_under_test": {"git_starts": "5, then 4", "program": "the bound wrapper",
                                                    "argv_after_the_program": READS}},
        ["DECISION-001 section 4.4", MC19])
control("P37-C63", W + "test_c63_an_ordinary_runs_summary_keeps_its_fields_and_values",
        "FZ-02: an ordinary run's summary keeps its fields and values", "FZ-02",
        real("the plan has no step (an input); platform.platform is a stand-in metadata leaf (on its first call it starts "
             "uname and file); " + BASELINE),
        ["c04's fixture: (a) clean; (b) with an uncommitted change of docs/notes.md and a staged new docs/staged.md in the "
         "original checkout", "the PATH Git is the logging wrapper, named git, first on PATH; check_local._GIT_STATE None",
         ISOLATION, "two runs each, with and without the refresh, each into a fresh absent output"],
        "tools.check_local.run(<original>, <output>, False, 60)",
        {"outcome": "accepted (exit 0, status passed)", "detail": (
            "the summary's keys are exactly the 28 of the declaration commit's run(); readback_selection "
            "{'status': 'absent', 'run_kind': 'ordinary'}; git = {available true, local_head, local_tree, "
            "tracked_worktree_status (a) '' (b) ' M docs/notes.md\\nA  docs/staged.md', untracked_source_files [], "
            "head_is_base_revision true, source_inventory_includes_untracked_files true, remote_head_verified false}; "
            "workspace_git = the same members with tracked_worktree_status (a) the seven lines (b) the seven lines and "
            "' M docs/notes.md', untracked_source_files (a) [] (b) ['docs/staged.md'], plus index_basis "
            "'source_commit_tree', copied_worktree_changes_preserved true, source_staging_preserved false, and exactly "
            "these 11 keys; workspace_storage lfs_files [] and network_transfers false; source_unchanged and "
            "git_revision_unchanged true; steps, not_executed_steps and pending_external_cases []; git_binding = the PATH "
            "wrapper, unbound, source PATH; every member other than started_at, finished_at and duration_seconds equal "
            "with and without the refresh")},
        {"node": 0, "other": 0, "code_under_test": {
            "git_starts": "the baseline's plus one", "program": "the PATH wrapper",
            "argv_after_the_program": ["-c core.fsmonitor=false -C <output>/workspace update-index -q --refresh, right after "
                                       "the storage step's ls-tree -r -z and before the workspace's first read"]}},
        ["DECISION-001 section 4.5", "CORRECTION-PLAN.md section 1 ('its summary fields and their meanings')",
         "0.2.0 CONTRACT.md section 8 (ordinary run)", "FZ-02"])
control("P37-C64", W + "test_c64_a_failed_refresh_fails_the_run_before_any_step",
        "FZ-02: a failed refresh fails the run before any step", "FZ-02",
        {"kind": "simulated", "boundary": ("the PATH Git's update-index -q --refresh start exits 128 (the wrapper); every "
                                           "other start runs the real Git; platform.platform is a stand-in leaf")},
        ["c04's fixture", "the failing wrapper named git first on PATH", "one planned step sys.executable -I -S -B -c "
                                                                          "'raise SystemExit(7)', which must never start",
         ISOLATION],
        "tools.check_local.run(<original>, <output>, False, 60)",
        refused("failed preparation", "Cannot record the isolated workspace's index stat data: <error>",
                "exit 1, status failed; the error starts with the reason's prefix and contains 'returned non-zero exit "
                "status 128'; readback_selection ordinary; steps [], not_executed_steps ['control-unit']; no workspace_git"),
        {"node": 0, "other": 0, "code_under_test": {"git_starts": "Git only (16 observed at freeze)", "program": "the PATH wrapper",
                                                    "argv_after_the_program": ["the last start: -c core.fsmonitor=false -C "
                                                                               "<output>/workspace update-index -q --refresh"]},
         "step_starts": 0},
        ["DECISION-001 section 4.4 ('On failure')", "interfaces/W1-CORRECTION.md section 2.1"])
control("P37-C65", W + "test_c65_a_copied_file_that_differs_from_the_commit_before_the_copy_stays_unrefreshed_and_refuses",
        "FZ-02: a copied file that differs from the commit before the copy stays unrefreshed", "FZ-02", real(),
        [FULL, BASE, ISOLATION, WRAPPER, "docs/notes.md changed in the original checkout before the copy; the record = "
                                         "inventory(<original>) after that change"],
        "tools.check_local.prepare_workspace, the workspace's .git/index (read without Git), then " + ENTRY,
        {"index": "docs/notes.md keeps zero stat data; README.md has stat data",
         "check": refused("CH-SOURCE", "Dirty source:  M docs/notes.md")},
        starts(4), ["DECISION-001 section 4.4", P05, MC19])

# -- cross-check against the module ----------------------------------------------------
module_path = worktree / MODULE
tree = ast.parse(module_path.read_text(encoding="utf-8"))
methods = {}
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                methods[node.name + "." + item.name] = ast.get_docstring(item) or ""
table = {row["method"]: row for row in C}
problems = []
if set(methods) != set(table):
    problems.append({"only_in_module": sorted(set(methods) - set(table)), "only_in_table": sorted(set(table) - set(methods))})
for name, doc in methods.items():
    row = table.get(name)
    if row is None:
        continue
    kind = doc.split()[1].rstrip(".") if doc.startswith("Label: ") else None
    if kind != row["label"]["kind"]:
        problems.append({"method": name, "docstring_label": kind, "frozen_label": row["label"]["kind"]})
    if row["id"].split("-")[1].lower() != name.split(".")[1].split("_")[1]:
        problems.append({"method": name, "id": row["id"]})
if problems:
    raise SystemExit("cross-check failed: " + json.dumps(problems))

runs = [json.loads(line) for line in (evidence / "runs/RUNS.jsonl").read_text(encoding="utf-8").splitlines() if line]
record = {
    "schema": "ontokin.c271.p37-controls-frozen/1",
    "task": "C271",
    "phase": "C271-P37-derived-workspace-correction",
    "stage": "S4",
    "acceptance": "A4",
    "status": "FROZEN",
    "author": ("W2, the independent control author: a subagent in a fresh context with the session's model; "
               "it wrote none of the implementation (W1's correction, or MI's), the contracts or the decision; launched by "
               "the Director c271-p37-08beec34eb0a"),
    "frozen_at_utc": sys.argv[3],
    "executed_by_author": True,
    "author_checks": [
        "the module run alone, W1's two focused modules alone, and the three together, each with the prescribed command "
        "from the worktree root (author_runs; logs and digests beside the clone)",
        "this generator's static cross-check of every test method against this table (ast only; the module is not "
        "imported here): the same methods, the docstring's label kind, and the control number"],
    "author_runs": runs,
    "author_run_notes": {
        "draft1-derived-controls": ("an earlier version of the module: 45 methods, before P37-C24 and the evidence lines "
                                    "were added; every test passed"),
        "draft2-derived-controls": ("the final bytes: no edit of the module followed it, and its log equals the final "
                                    "run's apart from the timing line"),
        "final-combined": ("an invocation error of the author, not a test result: the shell (zsh) did not split an "
                           "unquoted variable, so unittest received the three module names as one name and reported one "
                           "import error; no test ran; rerun as final-combined-2"),
        "final-combined-2": "the three modules in one process: 39 + 64 + 46 = 149 tests, OK"},
    "rules": [
        "Expectations come from P05 section 3 and the 0.2.0 contract's sections 1, 8 and 9 (MC19, MC21); the rule on "
        "status lines, which the contract leaves to the implementation, from DECISION-001 where it stays within them.",
        "An implementation defect is corrected in the implementation, never in a frozen expectation; a defect in a frozen "
        "control is recorded and refrozen by W2, and the original is kept (CORRECTION-PLAN.md section 7).",
        "Reasons quoted here are exact strings unless a placeholder in angle brackets names a part the control computes "
        "(a path in the temporary directory, the line, the name)."],
    "contract": {"id": "ontokin.current-host-readback/0.2.0", "profile": "darwin-arm64-v1",
                 "design_revision": 4, "amendments": ["P33-AMENDMENT-001"]},
    "sources": described([
        "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md",
        "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md",
        "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.json",
        PHASE_DIR + "/CORRECTION-PLAN.md", PHASE_DIR + "/PHASE.json", PHASE_DIR + "/DECISION-001.md",
        PHASE_DIR + "/interfaces/W1-CORRECTION.md",
        "docs/engineering/localized-repair-c271/macos-routine-p36/reviews/freeze-review-001/FREEZE-REVIEW-001.md",
        "docs/engineering/localized-repair-c271/macos-implementation-p33/CONTROLS-FROZEN.json"]),
    "measurement": {"path": "<local>/c271-p37/measure/MEASURE-001.json",
                    "sha256": sha(Path(sys.argv[4]))},
    "checkout": {
        "branch": "work/c271-missing-import-digest-control",
        "head": "2f728998456c829f3cdc13bbf72d6dd805fefa36",
        "state": "W1's correction uncommitted in the working tree; this record and the module are also uncommitted; the "
                 "author made no Git command in the worktree and compared W1's files with the declaration commit's copy "
                 "at <local>/c271-p37/measure/prep-001/workspace by reading files",
        "implementation_read_at_freeze": described([
            "tools/check_local.py", "prototypes/static_tray_v01/current_host_readback_v02.py",
            "prototypes/static_tray_v01/current_host_readback_v01.py",
            "prototypes/static_tray_v01/current_host_observation_v02.py", "tools/storage_identity.py"]),
        "w1_tests_read_not_frozen": described(["tests/test_local_checks.py", "tests/test_current_host_readback_provider_v02.py"]),
    },
    "test_module": {
        "path": MODULE, "sha256": sha(module_path), "size_bytes": module_path.stat().st_size,
        "test_methods": len(methods), "standard_library_only": True,
        "default_discovery_ids": sorted("test_current_host_readback_derived_controls_v02." + name for name in methods),
        "default_inventory_note": "the 46 IDs add to the default inventory; the next MR attempt's MC28 must approve them",
        "run_time_note": "about 65 s alone on this host, mostly fixture and wrapper Git starts"},
    "execution": {
        "by": "the Director at S5",
        "cwd": "<worktree>",
        "command": ("/usr/bin/env -i HOME=<home> LOGNAME=<logname> USER=<user> PATH=/usr/bin:/bin TMPDIR=<resolved tmp>/ "
                    ".venv/bin/python -B -m unittest tests.test_current_host_readback_derived_controls_v02 -v"),
        "notes": ["the temporary directory must be resolved; each control asserts it",
                  "Git must be on PATH (shutil.which); without it every control errors, none skips",
                  "CONTROL-EVIDENCE lines on stderr record each check's observed status lines, untracked names, outcome "
                  "and Git start count, with the temporary directory written as <tmp>"]},
    "conventions": {
        "labels": {
            "real": ("the code under test runs with no boundary substituted; fixtures are synthetic; Git runs through the "
                     "logging wrapper, which execs the real Git; a substituted plan or platform metadata leaf is an input, "
                     "named in the boundary"),
            "simulated": "one named boundary produces the case's condition",
            "mocked": "named components are replaced by stand-ins, and the 0.2.0 provider labels its records 'mocked'"},
        "starts": ("node and other count Node and other bounded starts, as the contract's columns do; code_under_test names "
                   "the Git starts the code under test makes inside the recorded window; the fixtures' own Git starts run "
                   "outside it"),
        "fixture_isolation": ISOLATION,
        "privacy": "no machine path, user or personal name in the module or this record; temporary paths are computed"},
    "fixtures": {
        "base": BASE, "records": RECORDS, "workspace": WORKSPACE, "full": FULL,
        "uncopied_by_kind": {
            ".claude/.gitignore": "a regular file in a top-level directory outside SOURCE_DIRS",
            ".claude/skills/alpha": "a symbolic link there, to a copied directory",
            ".claude/hooks/check.sh": "an executable file (100755) outside SOURCE_DIRS",
            "Makefile": "a root file outside ROOT_FILES",
            "outside/nested/deep/notes.txt": "nested directories outside SOURCE_DIRS",
            "tools/build/generated.py": "an ignored directory component (build) inside a SOURCE_DIR",
            "docs/_build/page.html": "an ignored directory component (_build)",
            "tools/node_modules/package/index.js": "an ignored directory component (node_modules)",
            "tools/node_modules/.bin/tool": "a symbolic link inside an ignored directory",
            "docs/.env": "an ignored file name (.env)",
            "TRDs/.env.local": "an ignored file name (.env.*)",
            "docs/.env.example": "a symbolic link with an ignored name",
            "fixtures/__pycache__/cached.cpython-312.pyc": "bytecode under __pycache__",
            "tools/stale.pyo": "an ignored suffix (.pyo)"}},
    "controls": C,
    "coverage": {
        "1. accepted on the derived route with real Git and the driver's preparation": {
            "a regular file outside SOURCE_DIRS": ["P37-C01", "P37-C04"], "a symbolic link there": ["P37-C02", "P37-C04"],
            "every other kind the copy leaves out": ["P37-C03"],
            "through the derivation and a qualifying run's preparation": ["P37-C05", "P37-C07"]},
        "2. refused on the derived route": {
            "a copied file modified or deleted": ["P37-C10", "P37-C11", "P37-C12", "P37-C13", "P37-C62", "P37-C65"],
            "a staged change": ["P37-C14", "P37-C06", "P37-C51"], "a rename or copy line": ["P37-C15", "P37-C53"],
            "a quoted name": ["P37-C16", "P37-C54"],
            "an uncopied path present but changed": ["P37-C17", "P37-C18", "P37-C51"],
            "an untracked input inside the copied set": ["P37-C19", "P37-C59"],
            "anything else the contract refuses and the decision keeps": [
                "P37-C20", "P37-C06", "P37-C21", "P37-C22", "P37-C23", "P37-C24", "P37-C52", "P37-C55", "P37-C56",
                "P37-C57"]},
        "2. refused on the original route": ["P37-C30", "P37-C31", "P37-C32", "P37-C33", "P37-C34", "P37-C35", "P37-C58"],
        "3. unchanged generated-example exclusion": ["P37-C40", "P37-C41", "P37-C59"],
        "4. FZ-02": ["P37-C60", "P37-C61", "P37-C62", "P37-C63", "P37-C64", "P37-C65", "P37-C12"]},
    "mutation_cross_check": {
        "basis": ("W1's ten mutation classes (MUTATIONS.json beside the clone); the author may not change W1's files, so "
                  "this is a reading of which frozen controls each mutation would fail, not an executed mutation run"),
        "MP1 no case-folded record guard": ["P37-C56"],
        "MP2 any XY form admitted for an uncopied path": ["P37-C51", "P37-C14", "P37-C17", "P37-C06"],
        "MP3 the driver's copied set not consulted": ["P37-C11", "P37-C52"],
        "MP4 a deletion admitted without the record": ["P37-C57"],
        "MP5 the selection drops the parent proof's record": ["P37-C05", "P37-C07"],
        "MP6 no check of empty, current or parent components": ["P37-C55"],
        "MP7 quoted names admitted": ["P37-C16", "P37-C54"],
        "MD1 no index refresh": ["P37-C60", "P37-C61", "P37-C63"],
        "MD2 refresh without -q": ["P37-C60", "every real-Git control (the preparation fails)"],
        "MD3 copied set without the ignored() exclusion": ["P37-C03", "P37-C50", "P37-C20"]},
    "findings": [
        {"id": "F-01", "kind": "decision text, nonmandatory", "controls": ["P37-C24"],
         "basis": "DECISION-001 section 2, 'Not missing source'",
         "text": ("The decision says that the whole 0.2.0 source set lies inside the copied set, so that its absence "
                  "'refuses twice: through that binding, and through rule B's condition 4'. The 0.2.0 source set is every "
                  "regular file under SOURCE_TREES (the observer's source_paths), and a tracked file there whose path has "
                  "an ignored() component, such as ontokin/.env or prototypes/static_tray_v01/build/helper.py, lies in "
                  "the source set but outside the copied set. The copy leaves it out, and rule B alone would admit its "
                  "deletion line; only the binding refuses it ('Complete CPU source inventory differs'). The outcome is "
                  "fail-closed and the decision's conclusion (no amendment) stands; P37-C24 freezes that refusal. At the "
                  "declaration commit no tracked path has an ignored() component (W1's index reading). Recommendation: "
                  "correct the sentence in a later record; no code change.")}],
    "observations": [
        {"id": "O-01", "text": ("The plan lists the driver's ordinary behaviour as unchanged, and its item 4 admits a "
                                "correction of FZ-02 with its own controls. The decision names the one added Git start as "
                                "the exception; P37-C60 and P37-C63 freeze it. The next MR attempt's start inventory must "
                                "count it.")},
        {"id": "O-02", "text": ("The controls keep the account's global Git files out (XDG_CONFIG_HOME). In a real run, "
                                "where such files exist, Git's default global ignore file applies to the provider's "
                                "ls-files --others --exclude-standard (Q-10 of MR's freeze review), and Git's default "
                                "global attributes file applies to the driver's and provider's Git reads, which set no "
                                "core.attributesFile (only the storage step's starts set it to /dev/null). Unchanged by "
                                "W1; for the next MR freeze.")},
        {"id": "O-03", "text": ("This host's Git (2.50.1, the developer tools' build) quotes a name with a space in porcelain v1, so "
                                "such an uncopied path refuses here; the decision notes that some versions do not. The "
                                "real-Git quoted controls use a double quote and a non-ASCII letter, which Git quotes under "
                                "the default core.quotePath; the space case is frozen at the exact-line level in both "
                                "forms (P37-C50 unquoted, P37-C54 quoted).")}],
    "not_frozen": [
        {"item": "a qualifying run with a real HOST, dependencies and methods",
         "reason": "the next MR attempt; P37-C05 to P37-C07 and P37-C34 substitute those boundaries"},
        {"item": "case variants at the file system's level",
         "reason": ("their outcome differs between case-sensitive and case-insensitive volumes, and a control must not "
                    "skip (W1's Q2); P37-C56 freezes the rule at the exact-line level")},
        {"item": "the refresh with Git LFS clean filters", "reason": "no LFS file in the tree and no client on the host"},
        {"item": "FZ-02's margin at the real tree's scale",
         "reason": "MEASURE-001 is its record; P37-C60 to P37-C65 freeze the mechanism, not the timing"},
        {"item": "the 0.1.0 provider (Linux route)", "reason": "a recorded follow-up outside local mode (P30-EXECUTOR-001)"}],
    "counts": {"controls": len(C), "test_methods": len(methods),
               "by_label": {kind: sum(1 for row in C if row["label"]["kind"] == kind) for kind in ("real", "simulated", "mocked")},
               "by_group": {group: sum(1 for row in C if row["group"] == group) for group in sorted({row["group"] for row in C})}},
}
out = worktree / OUTPUT
text = json.dumps(record, indent=1, ensure_ascii=True) + "\n"
for marker in ("/Users/", "/Volumes/", "/private/var", "/var/folders"):
    if marker in text:
        raise SystemExit("machine path in the record: " + marker)
out.write_text(text, encoding="utf-8")
print(json.dumps({"path": OUTPUT, "sha256": sha(out), "size_bytes": out.stat().st_size, "controls": len(C),
                  "module_sha256": sha(module_path), "methods": len(methods), "counts": record["counts"]["by_label"]}))
