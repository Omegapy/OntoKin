"""W1 (C271-P36) writer of START-INVENTORY.json from the entries established by reading.

Run only as: python3 -I -S -B build_inventory_json.py OUTFILE
It starts nothing and reads nothing; every value below was established by reading the files named in
START-INVENTORY.md. Paths use the labels <worktree>, <workspace>, <output>, <local>, <tmp>, <framework>.
"""
import json
import sys

W = "<worktree>/.venv/bin/python"
STEP_ENV = ("inherited from the driver, minus every GIT_* name, plus GIT_CONFIG_NOSYSTEM=1, GIT_CONFIG_GLOBAL=/dev/null, "
            "GIT_TERMINAL_PROMPT=0, GIT_ATTR_NOSYSTEM=1, GIT_OPTIONAL_LOCKS=0, GIT_NO_REPLACE_OBJECTS=1, GIT_NO_LAZY_FETCH=1, "
            "GIT_CEILING_DIRECTORIES=<output>, PYTHONDONTWRITEBYTECODE=1; both selection variables removed")
UNIT_ENV = STEP_ENV + ("; R1 only: the derived selection pair, PYTHONNOUSERSITE=1, and the UNIT_REMOVED_ENVIRONMENT names "
                       "(PYTHONPATH ... PYTHONEXECUTABLE, every DYLD_*) removed")
INHERIT = "inherited from the unit process (so PYTHONDONTWRITEBYTECODE=1, GIT_CONFIG_GLOBAL=/dev/null, GIT_OPTIONAL_LOCKS=0)"

E = []


def add(**row):
    for key in ("id", "file", "line", "steps", "tests", "program", "program_kind", "argv_pattern", "cwd", "environment",
                "bytecode_guard", "mocked", "conditions", "run_kinds", "verdict_notes"):
        row.setdefault(key, None)
    E.append(row)


# ---------------------------------------------------------------- driver
add(id="DRV-01", file="tools/check_local.py", line=729, steps=["driver"], tests=[],
    program="uname (PATH name; /usr/bin/uname under PATH=/usr/bin:/bin)", program_kind="os-tool-by-path-name",
    argv_pattern=["uname", "-p"], cwd="driver cwd (<worktree>)", environment="driver environment, unchanged (no env argument)",
    bytecode_guard="not Python", mocked=False,
    conditions="platform.platform() -> uname().processor -> _Processor.from_subprocess (<framework>/lib/python3.12/platform.py:819-835); cached per process",
    run_kinds=["R1", "R2"], verdict_notes="D-19. One start per run. Not a bounded start; recorded.")
add(id="DRV-02", file="tools/check_local.py", line=729, steps=["driver"], tests=[],
    program="file (PATH name; /usr/bin/file under PATH=/usr/bin:/bin)", program_kind="os-tool-by-path-name",
    argv_pattern=["file", "-b", "<interpreter file: sys.executable with its final-component links followed (normpath only), i.e. .../Python.framework/Versions/3.12/bin/python3.12, possibly through the <prefix>/opt link>"],
    cwd="driver cwd", environment="driver environment plus LC_ALL=C (platform.py:668)", bytecode_guard="not Python", mocked=False,
    conditions="platform.platform() generic branch -> architecture(sys.executable) -> _syscmd_file (platform.py:648-676); the platform() result is cached",
    run_kinds=["R1", "R2"], verdict_notes="D-19. One start per run; reads the interpreter file only.")
add(id="DRV-03", file="tools/check_local.py", line=272, steps=["driver"], tests=[],
    program="R1: the Git implementation bound from the selection's HOST (absolute developer-tools path, re-hashed before every start); R2: 'git' resolved once on PATH (/usr/bin/git dispatcher under PATH=/usr/bin:/bin, which runs the developer tools' Git)",
    program_kind="git", argv_pattern=["<git>", "-c", "core.fsmonitor=false", "-C", "<root>", "<args>"],
    cwd="driver cwd", environment="check_local.git_environment(<root>): driver environment minus GIT_*, plus the eight GIT_* settings of DRV-06",
    bytecode_guard="not Python", mocked=False,
    conditions=("git_metadata(<worktree>) before (5 reads) and after (5); prepare_workspace_git (init, fetch --depth=1, update-ref, read-tree, rev-parse x2 = 6); "
                "git_metadata(<workspace>) (5); R1 only: provider _verify_source through git_read for validate_selection on <worktree> (5) and "
                "derive_workspace_binding (5 on <worktree>, 5 on <workspace>, plus git_metadata(<workspace>) 5)"),
    run_kinds=["R1", "R2"], verdict_notes="Read-only commands with GIT_OPTIONAL_LOCKS=0 (no index refresh in <worktree>). R1: 41 starts, R2: 21 (with DRV-04: 49 and 29).")
add(id="DRV-04", file="tools/storage_identity.py", line=53, steps=["driver"], tests=[],
    program="same Git as DRV-03 (driver passes git_executable)", program_kind="git",
    argv_pattern=["<git>", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", "-c", "core.attributesFile=/dev/null", "-C", "<dir>", "<args>"],
    cwd="driver cwd", environment="storage_identity.git_environment(<dir>) (same GIT_* settings)", bytecode_guard="not Python", mocked=False,
    conditions=("StorageContext(<workspace>): rev-parse --show-toplevel, rev-parse --verify HEAD^{commit}, rev-parse --show-object-format, ls-tree -r -z (4); "
                "_attributes: init --quiet --template= in a new <tmp> directory, cat-file -s, cat-file blob, check-attr -z --stdin filter (4). "
                "No LFS-selected path at d3b622d6, so configure_offline_filters (shutil.which('git-lfs'), [git-lfs, version], git config x7) is not reached"),
    run_kinds=["R1", "R2"], verdict_notes="8 starts per run. A commit adding a file under docs/engineering/lfs-archives/ would add a PATH lookup and start of git-lfs.")
add(id="DRV-05", file="(Git internals of the DRV-03 fetch)", line=None, steps=["driver"], tests=[],
    program="/bin/sh and the developer tools' Git helpers (upload-pack, index-pack or unpack-objects, rev-list, maintenance run --auto)",
    program_kind="git-internal", argv_pattern=["/bin/sh", "-c", "git-upload-pack '<worktree>'", "..."], cwd="<workspace>",
    environment="Git's own child environment (exec path prepended to PATH)", bytecode_guard="not Python", mocked=False,
    conditions="git fetch from a local path; established from Git's documented behaviour, not from this repository's code",
    run_kinds=["R1", "R2"], verdict_notes="Count not determinable by reading this repository. All within the allowed program set.")
add(id="DRV-06", file="tools/check_local.py", line=666, steps=["unit-tests", "source", "agent", "construction", "surface", "impulse", "documents"], tests=[],
    program=W + " (driver sys.executable; the framework interpreter through the worktree .venv)", program_kind="framework-python",
    argv_pattern=[W, "-B", "<step arguments: -m unittest discover -s tests -v | -m ontokin conformance --output R | tools/run_agent_conformance.py --output R | -m tools.verify_construction_ci --external-evidence docs/engineering/construction-validation/external-gate.json --output R | tools/run_surface_conformance.py --allow-pending --output R | tools/run_impulse_conformance.py --allow-pending --output R | docs/maintenance/reorganization-2026-10-17/verify_reorganization.py>"],
    cwd="<workspace>", environment=UNIT_ENV + " (unit step); " + STEP_ENV + " (other steps)",
    bytecode_guard="-B and PYTHONDONTWRITEBYTECODE=1", mocked=False, conditions="start_new_session=True; one start per step",
    run_kinds=["R1", "R2"], verdict_notes="7 starts per run.")
add(id="DRV-07", file="tools/check_local.py", line=440, steps=["driver"], tests=[],
    program="none: shutil.which('node') lookup only", program_kind="path-lookup-only", argv_pattern=None, cwd=None, environment=None,
    bytecode_guard=None, mocked=False, conditions="the core plan never uses the result (only --full steps do)", run_kinds=["R1", "R2"],
    verdict_notes="No start. Under PATH=/usr/bin:/bin it finds nothing.")
add(id="DRV-08", file="tools/check_local.py", line=518, steps=["driver"], tests=[],
    program="none: os.killpg of a step's group", program_kind="signal-only", mocked=False,
    conditions="only when a step exceeds --timeout or is interrupted", run_kinds=["R1", "R2"],
    verdict_notes="O-01: a Darwin EPERM escapes stop_process; outside the start set.")

# ---------------------------------------------------------------- other steps
add(id="STP-01", file="tools/run_agent_conformance.py", line=79, steps=["agent"], tests=["test_agent.AgentContractTests.test_A01 ... test_A10 (in process)"],
    program="uname and file (PATH names), as DRV-01 and DRV-02", program_kind="os-tool-by-path-name",
    argv_pattern=[["uname", "-p"], ["file", "-b", "<interpreter file, as DRV-02>"]], cwd="<workspace>", environment="agent step environment (+LC_ALL=C for file)",
    bytecode_guard="not Python", mocked=False, conditions="first platform.platform() in the agent step process", run_kinds=["R1", "R2"],
    verdict_notes="2 starts per run. The ten A-cases start no child (prepared_worker and the retry test are not among them).")
add(id="STP-02", file="ontokin/construction_conformance.py", line=681, steps=["construction"], tests=["the 128 required tests, in process"],
    program="uname and file (PATH names)", program_kind="os-tool-by-path-name",
    argv_pattern=[["uname", "-p"], ["file", "-b", "<interpreter file, as DRV-02>"]], cwd="<workspace>", environment="construction step environment",
    bytecode_guard="not Python", mocked=False, conditions="run_conformance builds its environment record", run_kinds=["R1", "R2"],
    verdict_notes="2 starts per run; the step also runs the children of U-08 (3) and U-09 (2) in process.")
add(id="STP-03", file="ontokin/conformance.py", line=240, steps=["source"], tests=[], program="none", program_kind="no-start",
    conditions="platform.python_version/python_implementation/system only; no subprocess in ontokin.conformance", run_kinds=["R1", "R2"],
    verdict_notes="source step: 0 further starts.")
add(id="STP-04", file="docs/maintenance/reorganization-2026-10-17/verify_reorganization.py", line=None, steps=["documents"], tests=[],
    program="none", program_kind="no-start", conditions="standard-library reads only", run_kinds=["R1", "R2"], verdict_notes="documents step: 0 further starts.")
add(id="STP-05", file="ontokin/surface_conformance.py", line=1123, steps=["surface"], tests=["the 61 required tests (test_surface_agent, _agent_protocol, _catalog, _export, _export_cli, _manifest, _regressions, _source), in process"],
    program="none found", program_kind="no-start", conditions="external evidence absent, so _verify_ci (git ls-tree) is not reached; none of the 61 tests has a start site",
    run_kinds=["R1", "R2"], verdict_notes="surface step: 0 further starts by reading.")
add(id="STP-06", file="ontokin/impulse_conformance.py", line=1643, steps=["impulse"], tests=["test_impulse_cli (2 starts, U-07)", "test_impulse_conformance.ImpulseWorkflowEvidenceTests (setUpClass: U-15)", "test_impulse_conformance.ImpulseRegressionEvidenceTests.test_ci_uses_actual_git_blobs_and_requires_all_supported_job_roles (U-14)"],
    program="framework Python children and Git, as U-07, U-14 and U-15", program_kind="framework-python; git", cwd="<workspace> or <tmp>",
    environment="impulse step environment, inherited", bytecode_guard="PYTHONDONTWRITEBYTECODE=1 inherited", mocked=False,
    conditions="the 124 required tests run in the step process", run_kinds=["R1", "R2"], verdict_notes="impulse step: 2 Python + about 7 Git starts.")

# ---------------------------------------------------------------- unit stage: the metadata leaf
add(id="U-00", file="ontokin/construction_conformance.py", line=681, steps=["unit-tests"],
    tests=["first unpatched platform.platform() in the unit process: test_construction_conformance (module 16, run_conformance); later unpatched calls are cached: test_current_host_readback_controls_v02 MC22 (tools/check_local.py:729), test_current_host_rtld_paths_v01.RTLDPathControls.setUpClass (465), test_local_checks (tools/check_local.py:729)"],
    program="uname and file (PATH names; /usr/bin/uname and /usr/bin/file under PATH=/usr/bin:/bin)", program_kind="os-tool-by-path-name",
    argv_pattern=[["uname", "-p"], ["file", "-b", "<interpreter file, as DRV-02>"]], cwd="<workspace>", environment="unit process environment (+LC_ALL=C for file)",
    bytecode_guard="not Python", mocked=False,
    conditions="platform caches uname().processor and the platform() result per process; P29's inherited rtld run patches the leaf (INHERITED-METADATA-STUB); driver tests that patch it start nothing here",
    run_kinds=["R1", "R2"], verdict_notes="Exactly 1 uname and 1 file start in the unit process.")
# ---------------------------------------------------------------- unit stage: Python children with inherited environment
add(id="U-01", file="tests/test_agent.py", line=280, steps=["unit-tests"],
    tests=["AgentContractTests.test_running_cancellation_wins_before_a_prepared_candidate_commits", "AgentContractTests.test_dead_worker_is_fenced_and_live_worker_is_never_stolen", "AgentContractTests.test_retry_is_durable_across_an_independent_python_process (line 528)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-c", "<code>", "<store>", "(<file>)"], cwd="<workspace>",
    environment=INHERIT, bytecode_guard="PYTHONDONTWRITEBYTECODE=1 (not -I/-E)", mocked=False, conditions="lines 280 and 528; killed in finally", run_kinds=["R1", "R2"], verdict_notes="3 starts.")
add(id="U-02", file="tests/test_agent_cli.py", line=35, steps=["unit-tests"], tests=["AgentCLITests (lines 35, 65, 117, 164)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-m", "ontokin", "agent", "--store", "<tmp>", "..."], cwd="<workspace>",
    environment=INHERIT, bytecode_guard="PYTHONDONTWRITEBYTECODE=1", mocked=False, run_kinds=["R1", "R2"], verdict_notes="one start per call")
add(id="U-03", file="tests/test_cli.py", line=24, steps=["unit-tests"], tests=["CLITests.test_module_entrypoint_and_capabilities"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-m", "ontokin", "capabilities"], cwd="<workspace> (inherited)",
    environment=INHERIT, bytecode_guard="PYTHONDONTWRITEBYTECODE=1", mocked=False, run_kinds=["R1", "R2"], verdict_notes="1 start.")
add(id="U-04", file="tests/test_budget_agent_lifecycle.py", line=616, steps=["unit-tests"], tests=["BudgetAgentLifecycleTests.test_EB29_cli_selects_only_explicit_budget_protocol"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-m", "ontokin", "agent", "--store", "<tmp>", "--wait", "--protocol", "<protocol>"], cwd="<workspace>",
    environment=INHERIT, bytecode_guard="PYTHONDONTWRITEBYTECODE=1", mocked=False, run_kinds=["R1", "R2"], verdict_notes="1 start.")
add(id="U-05", file="tests/test_extrusion_agent.py", line=405, steps=["unit-tests"],
    tests=["test_extrusion_agent.py:405,414", "test_framed_loft_agent.py:620,632", "test_holes_agent.py:466,478", "test_pockets_agent.py:719,729", "test_ring_loft_agent.py:545,557"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-m", "ontokin", "export|agent", "..."], cwd="<workspace>",
    environment=INHERIT, bytecode_guard="PYTHONDONTWRITEBYTECODE=1", mocked=False, run_kinds=["R1", "R2"], verdict_notes="10 starts.")
add(id="U-06", file="tests/test_force_agent_cli.py", line=18, steps=["unit-tests"], tests=["ForceAgentCLITests (invoke)", "ReachAgentCLITests (tests/test_reach_agent_cli.py:17)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-m", "ontokin", "agent", "--store", "<tmp>", "--wait", "..."], cwd="<workspace>",
    environment=INHERIT, bytecode_guard="PYTHONDONTWRITEBYTECODE=1", mocked=False, run_kinds=["R1", "R2"], verdict_notes="one start per invoke call")
add(id="U-07", file="tests/test_impulse_cli.py", line=62, steps=["unit-tests", "impulse"], tests=["ImpulseCLITests.test_jsonl_malformed_request_uses_selected_impulse_envelope", "ImpulseCLITests.test_corrupt_or_directory_store_reports_controlled_selected_protocol_error (line 77)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-m", "ontokin", "agent", "--store", "<tmp>", "--protocol", "<protocol>"], cwd="<workspace>",
    environment=INHERIT + " (or the impulse step environment)", bytecode_guard="PYTHONDONTWRITEBYTECODE=1", mocked=False, run_kinds=["R1", "R2"], verdict_notes="2 starts in each of the two processes.")
add(id="U-08", file="tests/test_program_protocol.py", line=78, steps=["unit-tests", "construction"], tests=["ProgramProtocolTests.test_cli_requires_version_selection_and_keeps_stores_separate (78, 86)", "ProgramProtocolTests.test_cli_invalid_json_still_returns_selected_protocol (95)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-m", "ontokin", "agent", "...", "--store", "<tmp>", "--wait"], cwd="<workspace>",
    environment=INHERIT + " (or the construction step environment)", bytecode_guard="PYTHONDONTWRITEBYTECODE=1", mocked=False, run_kinds=["R1", "R2"], verdict_notes="3 starts in each of the two processes.")
add(id="U-09", file="tests/test_program_transactions.py", line=207, steps=["unit-tests", "construction"], tests=["ProgramTransactionTests.test_proven_dead_worker_is_fenced_but_a_live_worker_is_not_stolen (prepared_process, 207)", "ProgramTransactionTests.test_persisted_queued_bundle_resumes_in_a_new_python_process (363)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-c", "<code>", "<store>"], cwd="<workspace>",
    environment=INHERIT, bytecode_guard="PYTHONDONTWRITEBYTECODE=1", mocked=False, conditions="the prepared process is killed in finally", run_kinds=["R1", "R2"], verdict_notes="2 starts in each of the two processes.")
add(id="U-10", file="tests/test_surface_agent_cli.py", line=54, steps=["unit-tests"], tests=["SurfaceAgentCLITests (lines 54, 139, 156, 190, 200, 239)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-m", "ontokin", "agent", "--store", "<tmp>", "..."], cwd="<workspace>",
    environment=INHERIT, bytecode_guard="PYTHONDONTWRITEBYTECODE=1", mocked=False, run_kinds=["R1", "R2"], verdict_notes="one start per call")
add(id="U-11", file="tests/test_static_tray_reader_v01.py", line=496, steps=["unit-tests"], tests=["StaticTrayReaderTests.test_exact_lock_and_isolated_cli (2)", "StaticTrayReaderTests.test_entry_scripts_reject_unbound_bytecode_before_helper_import (6, line 521)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-IB", "<workspace>/tools/static_tray_reader_v01/audit.py | <tmp copy>/{audit,corrupt}.py", "..."], cwd="<workspace>",
    environment=INHERIT, bytecode_guard="-B (with -I)", mocked=False, run_kinds=["R1", "R2"], verdict_notes="8 starts; module 338, after the readback module.")
add(id="U-12", file="tests/test_current_host_observation_v02.py", line=1944, steps=["unit-tests"], tests=["CommandLineTests.test_missing_plan_is_refused_with_a_structured_record (1)", "CommandLineTests.test_launch_without_no_site_is_refused (1, -I -B)", "CommandLineTests.test_inventory_commands_write_only_their_absent_outputs (3)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-I", "-S", "-B", "<workspace>/prototypes/static_tray_v01/current_host_observation_v02.py", "static|python-inventory|source-inventory", "..."],
    cwd="tempfile.gettempdir()", environment="replaced: observation.ENVIRONMENT (the declared environment)", bytecode_guard="-B (one run uses -I -B without -S)", mocked=False,
    conditions="the observer reads synthetic trees; 'observe' is never run on the command line, and the in-process observe tests use a mocked supervisor",
    run_kinds=["R1", "R2"], verdict_notes="5 starts (missing plan 1, no -S 1, inventory commands 3).")
add(id="U-13", file="tests/test_supervisor_darwin_v01.py", line=457, steps=["unit-tests"], tests=["DarwinGroupProbe.start_waiter and the DarwinSupervisorChildren cases through supervisor_darwin_v01.run_process (prototypes/static_tray_v01/supervisor_darwin_v01.py:155)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-I", "-S", "-B", "-c", "<fixed code>"], cwd="<tmp> stage",
    environment="replaced: {PATH=/usr/bin:/bin, LC_ALL=C}", bytecode_guard="-B", mocked=False,
    conditions="MC39(a)'s child forks Python descendants (os.fork in the child code) and one grandchild Popen [-I -S -B -c]; each test's guard kills every tracked group",
    run_kinds=["R1", "R2"], verdict_notes="Real Python children only; module 344.")
add(id="U-14", file="tests/test_impulse_conformance.py", line=507, steps=["unit-tests", "impulse"], tests=["ImpulseRegressionEvidenceTests.test_ci_uses_actual_git_blobs_and_requires_all_supported_job_roles", "tests/test_surface_conformance.py:220 SurfaceConformanceRegressionEvidenceTests.test_ci_commit_proof_reads_actual_git_tree_and_required_job_roles", "tests/test_force_conformance.py:209 ForceGitInputTests.test_commit_blob_binding_ignores_ambient_git_and_replacement_refs_without_index_changes", "tests/test_chat_workflow.py:616 StartingRevisionTests (and tools/chat_workflow.py:492 through create())"],
    program="git (PATH name)", program_kind="git-by-path-name", argv_pattern=["git", "init|config|add|commit|rev-parse|ls-tree", "..."], cwd="<tmp> repositories (ontokin/impulse_conformance.py:1534 and ontokin/surface_conformance.py:1024 run ls-tree with cwd=<workspace>)",
    environment="inherited, or os.environ minus GIT_* plus GIT_CONFIG_GLOBAL=/dev/null and GIT_CONFIG_NOSYSTEM=1", bytecode_guard="not Python", mocked=False, run_kinds=["R1", "R2"],
    verdict_notes="Temporary repositories; ls-tree in <workspace> is read-only.")
add(id="U-15", file="tools/build_impulse_agent_demo.py", line=463, steps=["unit-tests", "impulse"], tests=["test_impulse_conformance.ImpulseWorkflowEvidenceTests.setUpClass (build)", "test_surface_conformance.SurfaceConformanceWorkflowEvidenceTests.setUpClass (tools/build_surface_agent_demo.py:433-434, Workflow.finish)"],
    program="git (PATH name)", program_kind="git-by-path-name", argv_pattern=[["git", "rev-parse", "HEAD"], ["git", "status", "--porcelain"]], cwd="<workspace> (ROOT of the copied source)",
    environment=INHERIT, bytecode_guard="not Python", mocked=False, conditions="status runs with GIT_OPTIONAL_LOCKS=0, so the workspace index is not refreshed", run_kinds=["R1", "R2"], verdict_notes="2 starts per call.")
add(id="U-16", file="tests/test_static_tray_admission_c231_ledger_identity.py", line=575, steps=["unit-tests"], tests=["IdentityLifecycleControls.test_fork_child_releases_pins..."],
    program="none: os.fork of the unit process, no exec", program_kind="fork-no-exec", argv_pattern=None, cwd="<workspace>", environment="the unit process's",
    bytecode_guard="inherited sys.dont_write_bytecode=True", mocked=False, conditions="the child always calls os._exit; the parent kills and reaps it if needed", run_kinds=["R1", "R2"], verdict_notes="1 fork.")

# ---------------------------------------------------------------- unit stage: driver, provider and control tests
add(id="U-17", file="tests/test_local_checks.py", line=42, steps=["unit-tests"], tests=["LocalChecksTests (every execute() call runs tools/check_local.run in process)"],
    program="git (driver git_executable: PATH resolution once; /usr/bin/git), framework Python step children, the 'git commit' step of test_source_head_movement_invalidates_unchanged_file_bytes, uname/file at the first unpatched platform.platform()",
    program_kind="git; framework-python; os-tool-by-path-name", argv_pattern=[[W, "-c", "<program>"], [W, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], ["git", "-C", "<tmp>", "commit", "..."]],
    cwd="<tmp> copies", environment="check_local.git_environment(<tmp workspace>) + PYTHONDONTWRITEBYTECODE=1", bytecode_guard="PYTHONDONTWRITEBYTECODE=1; -B where planned; one deliberate exception (U-18)",
    mocked=False, conditions="platform.platform() is not patched in this module; build_plan is patched", run_kinds=["R1", "R2"], verdict_notes="Many Git and Python starts in temporary trees.")
add(id="U-18", file="tests/test_local_checks.py", line=366, steps=["unit-tests"], tests=["LocalChecksTests.test_parent_only_no_bytecode_flag_does_not_protect_child_imports"],
    program=W, program_kind="framework-python", argv_pattern=[[W, "-B", "-c", "<program>"], ["(grandchild) " + W, "-c", "import ontokin"]], cwd="<tmp>/source",
    environment="replaced: os.environ minus PYTHONDONTWRITEBYTECODE and PYTHONPYCACHEPREFIX (grandchild inherits that)", bytecode_guard="child -B; grandchild NONE (deliberate)",
    mocked=False, conditions="the grandchild writes <tmp>/source/ontokin/__pycache__/__init__.cpython-312.pyc by design; its standard-library imports at start-up are all cached (no write into <framework>)",
    run_kinds=["R1", "R2"], verdict_notes="Bytecode-writing start #4 of 4 kinds; module 105, before the readback module.")
add(id="U-19", file="tests/test_current_host_readback_driver.py", line=162, steps=["unit-tests"], tests=["CurrentHostDriverBindingTests.test_explicit_pair_reaches_real_python_child_without_ambient_override"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-B", "-c", "<program>"], cwd="<tmp>", environment="execute_step environment with a synthetic selection",
    bytecode_guard="-B", mocked=False, conditions="other tests here patch Popen, git_metadata and platform.platform", run_kinds=["R1", "R2"],
    verdict_notes="1 start. Two tests here fail by D-18 without any start.")
add(id="U-20", file="tests/test_current_host_readback_driver_v02.py", line=89, steps=["unit-tests"], tests=["CurrentHostDriverBindingTests.test_missing_explicit_selection_cannot_use_ambient_approval", "SelectionRuleTests", "UnitEnvironmentTests", "DriverGitBindingTests", "QualifyingUnitDecisionTests", "DriverStorageGitTests"],
    program="framework Python children (-B -c; -B -m unittest discover in <tmp> workspaces), /bin/sh Git stand-ins and wrappers that exec the PATH Git, git (shutil.which at setUp, line 661)",
    program_kind="framework-python; shell-stand-in; git", argv_pattern=[[W, "-B", "-c", "<program>"], [W, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], ["<tmp>/<name>/git (a #!/bin/sh script)", "-c", "core.fsmonitor=false", "-C", "<tmp>", "..."]],
    cwd="<tmp>", environment="execute_step environment; PATH temporarily prefixed with <tmp> stand-in directories (patch.dict)", bytecode_guard="-B",
    mocked=False, conditions="DriverFixture isolates check_local._GIT_STATE; platform.platform patched", run_kinds=["R1", "R2"], verdict_notes="No Node; stand-ins log and exit or exec Git.")
add(id="U-21", file="tests/test_current_host_readback_controls_v02.py", line=2158, steps=["unit-tests"], tests=["SupervisorProcessControls (MC12, MC13, MC37-MC39): darwin.run_process and unreaped_child (2199)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-I", "-S", "-B", "-c", "<fixed code>"], cwd="<tmp> stage", environment="replaced: DECLARED_ENVIRONMENT",
    bytecode_guard="-B", mocked=False, conditions="children fork descendants by design (MC12); OwnedProcesses teardown kills every group", run_kinds=["R1", "R2"], verdict_notes="Real Python children only.")
add(id="U-22", file="tests/test_current_host_readback_controls_v02.py", line=3073, steps=["unit-tests"], tests=["SourceControls (MC19)"],
    program="git (shutil.which('git') -> /usr/bin/git) for the synthetic repository; a #!/bin/sh stand-in that execs that Git, bound through check_local.bind_git for the provider's _verify_source",
    program_kind="git; shell-stand-in", argv_pattern=[["/usr/bin/git", "-C", "<tmp>/checkout", "init|add|commit|rev-parse"], ["<tmp>/bin/git-stand-in", "-c", "core.fsmonitor=false", "-C", "<tmp>/checkout", "..."]],
    cwd="unit cwd", environment="os.environ minus GIT_* plus three GIT_* settings; stand-in: check_local.git_environment", bytecode_guard="not Python", mocked=False,
    conditions="check_local._GIT_STATE patched to None for each verify", run_kinds=["R1", "R2"], verdict_notes="Git only.")
add(id="U-23", file="tests/test_current_host_readback_controls_v02.py", line=3250, steps=["unit-tests"], tests=["DriverControls (MC07, MC21, MC22, MC23)"],
    program="framework Python unit children (-I -S -B -c), git metadata reads of <tmp> roots, uname/file (MC22 does not patch platform.platform)",
    program_kind="framework-python; git; os-tool-by-path-name", argv_pattern=[W, "-I", "-S", "-B", "-c", "<unit runner>"], cwd="<tmp> workspaces",
    environment="execute_step environment; MC22 pops both selection variables", bytecode_guard="-B", mocked=False,
    conditions="MC22's child loads tests.test_static_tray_readback_v01 from <workspace>; without a selection its setUpClass fails, so no Node starts; MC21 cases patch platform.platform",
    run_kinds=["R1", "R2"], verdict_notes="No Node. MC22 starts the readback module in a nested process, ordinary.")
add(id="U-24", file="tests/test_current_host_readback_provider_v02.py", line=898, steps=["unit-tests"], tests=["SourceGitTests (MC19 provider side)"],
    program="a #!/bin/sh stand-in for the bound Git (answers from files)", program_kind="shell-stand-in", argv_pattern=["<tmp>/git", "-c", "core.fsmonitor=false", "-C", "<tmp>", "..."],
    cwd="unit cwd", environment="check_local.git_environment", bytecode_guard="not Python", mocked=False, conditions="check_local._GIT_STATE patched", run_kinds=["R1", "R2"],
    verdict_notes="Every other provider test patches supervisor_darwin_v01.run_process, the provider entry points or subprocess.Popen.")

# ---------------------------------------------------------------- unit stage: doctor and setup tools
add(id="U-25", file="tests/test_doctor_local.py", line=70, steps=["unit-tests"], tests=["every DoctorCase and SetupCase setUp (tests/test_bootstrap_local.py), RealEnvironmentTests and RealSetupTests (LocalProject: git init, add, commit)", "the fake run's pass-through of argv[0]=='git' to doctor.execute (line 131)", "tools/doctor_local.py:863 check-attr (direct subprocess.run)"],
    program="git (PATH name)", program_kind="git-by-path-name", argv_pattern=["git", "(-c user.name/user.email | --no-optional-locks -c core.fsmonitor=false)", "-C", "<tmp>/checkout", "..."],
    cwd="unit cwd", environment="LocalProject: os.environ minus GIT_* plus GIT_CONFIG_GLOBAL=/dev/null, GIT_CONFIG_NOSYSTEM=1; doctor: clean_environment() (strips GIT_*, so the user's global Git configuration is read)",
    bytecode_guard="not Python", mocked=False, run_kinds=["R1", "R2"], verdict_notes="Many Git starts in temporary repositories.")
add(id="U-26", file="tests/test_doctor_local.py", line=656, steps=["unit-tests"], tests=["RealEnvironmentTests.setUp (8 test methods)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-I", "-m", "venv", "--without-pip", "<tmp>/check out/.venv"], cwd="<workspace> (inherited)",
    environment=INHERIT + "; -I makes the interpreter ignore PYTHONDONTWRITEBYTECODE", bytecode_guard="NONE (-I without -B)", mocked=False,
    conditions="imports venv, venv.__main__, argparse and their module-level closure (58 modules, all with fresh cached bytecode); writes only into <tmp>",
    run_kinds=["R1", "R2"], verdict_notes="Bytecode-writing start #1 of 4 kinds: 8 starts; module 32, before the readback module. Then doctor.collect(run=doctor.execute, which=lambda: None) probes the temporary environment with [<tmp venv>/bin/python, -I, -B, ...] and [<tmp venv>/bin/python, -B, -c, import ontokin].")
add(id="U-27", file="tests/test_doctor_local.py", line=1066, steps=["unit-tests"], tests=["ReportTests.test_real_child_keeps_a_passed_descriptor_open"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-I", "-c", "import os, sys; os.fstat(int(sys.argv[1]))", "<fd>"], cwd="unit cwd",
    environment=INHERIT + " (ignored under -I)", bytecode_guard="NONE (-I without -B)", mocked=False,
    conditions="start-up imports only (encodings, encodings.aliases, encodings.utf_8, sitecustomize: cached; site, os frozen)", run_kinds=["R1", "R2"],
    verdict_notes="Bytecode-writing start #2 of 4 kinds: 2 starts; no file expected.")
add(id="U-28", file="tests/test_doctor_local.py", line=1079, steps=["unit-tests"], tests=["ReportTests.test_command_line_runs_without_site_packages_and_writes_only_a_new_report (3 runs)"],
    program=W + " running tools/doctor_local.py, which starts git, and, through PATH, the first 'node' (tools/doctor_local.py:737-741) and git's 'lfs' helper", program_kind="framework-python; git; NODE-BY-PATH",
    argv_pattern=[[W, "-I", "-S", "-B", "<workspace>/tools/doctor_local.py", "--root", "<tmp>/checkout", "--json|--output <tmp>/reports/doctor.json"], ["<which('node')>", "--version"], ["git", "lfs", "version"], ["<tmp>/interpreters/python3.12 (empty file; exec fails)", "-I", "-B", "-c", "<PROBE>"]],
    cwd="unit cwd", environment=INHERIT + "; doctor children get clean_environment() (PYTHONDONTWRITEBYTECODE=1, GIT_* stripped)", bytecode_guard="-B (doctor); node and git not Python",
    mocked=False, conditions="no --node is passed; which('node'), which('npm'), which('python3.12') search the inherited PATH. Under PATH=/usr/bin:/bin none is found (neither /usr/bin/node nor /bin/node exists) and 'git lfs' finds no helper",
    run_kinds=["R1", "R2"], verdict_notes="FOREIGN-NODE RISK: up to 3 starts of whatever node is first on PATH, per run kind.")
add(id="U-29", file="tests/test_doctor_local.py", line=992, steps=["unit-tests"], tests=["SectionTests.test_structure_check_result_is_reported_as_it_is (4 fake tools)"],
    program=W, program_kind="framework-python", argv_pattern=[W, "-I", "-B", "<tmp>/checkout/tools/chat_workflow.py", "--root", "<tmp>/checkout", "check", "--json"], cwd="unit cwd",
    environment="clean_environment()", bytecode_guard="-B", mocked=False, conditions="the fake run passes chat_workflow.py commands to doctor.execute", run_kinds=["R1", "R2"], verdict_notes="4 starts of a one-line print script.")
add(id="U-30", file="tests/test_bootstrap_local.py", line=1109, steps=["unit-tests"], tests=["RealSetupTests.test_real_core_environment_from_the_command_line (2 runs)"],
    program=W + " running tools/bootstrap_local.py; it starts git, the base interpreter (sys._base_executable: the framework interpreter, possibly through its <prefix> link), the new environment's interpreter, and, through PATH, 'node' and git's 'lfs' helper (three doctor.collect calls)",
    program_kind="framework-python; git; NODE-BY-PATH",
    argv_pattern=[[W, "-I", "-B", "<workspace>/tools/bootstrap_local.py", "--root", "<tmp>/check out", "--profile", "core", "(--python <framework>/bin/python3.12)"],
                  ["<base interpreter: sys._base_executable of the unit process, the framework interpreter, possibly through its <prefix> link>", "-I", "-m", "venv", "<tmp>/check out/.venv"],
                  ["<tmp>/check out/.venv/bin/python", "-m", "ensurepip", "--upgrade", "--default-pip"],
                  ["<tmp>/check out/.venv/bin/python", "-W", "ignore::DeprecationWarning", "-c", "<ensurepip pip runner>"],
                  ["<base or tmp venv python>", "-I", "-B", "-c", "<PROBE>"], ["<tmp venv python>", "-I", "-B", "-m", "pip", "check"],
                  ["<tmp venv python>", "-B", "-c", "import ontokin; ..."], ["<tmp venv python>", "-I", "-B", "<tmp>/check out/tools/check_native_reader_setup.py"],
                  ["<tmp venv python>", "-B", "-m", "ontokin", "capabilities|check ..."], ["<which('node')>", "--version"], ["git", "lfs", "version"]],
    cwd="<tmp>/check out for source-import and smoke checks, otherwise unit cwd", environment="bootstrap and doctor children: clean_environment() (PYTHONDONTWRITEBYTECODE=1); the venv process ignores it under -I; ensurepip and its pip child inherit it",
    bytecode_guard="all -B or the variable, except the venv process (-I without -B)", mocked=False,
    conditions="core profile: no package install, no lsof or ps (require_unused is not reached); writes only into <tmp>",
    run_kinds=["R1", "R2"], verdict_notes="Bytecode-writing start #3 of 4 kinds (1 venv process; all its imports cached). FOREIGN-NODE RISK: up to 3 node --version starts if a node is on PATH. Module 5.")

# ---------------------------------------------------------------- the readback cohort
add(id="RB-01", file="prototypes/static_tray_v01/supervisor_darwin_v01.py", line=155, steps=["unit-tests"],
    tests=["test_static_tray_readback_v01.ReadbackCPUControls.test_q01_actual_synthetic_meshes_load_in_both_libraries", "...test_q03_actual_synthetic_rotations_load_in_both_libraries", "...test_three_rejects_changed_synthetic_reference"],
    program="<local>/c271-macos/node-v24.22.1-darwin-arm64/bin/node (HOST runtime executable, through the provider)", program_kind="PINNED-NODE",
    argv_pattern=["<pinned node>", "--no-addons", "--max-old-space-size=256", "--experimental-loader", "<local>/c271-macos/reader-c195/tools/three_loader.mjs", "<workspace>/prototypes/static_tray_v01/current_host_readback_v02.mjs", "--expected-config-sha256", "<derived config digest>", "--job", "<cohort>/<case>/job.json"],
    cwd="<cohort>/<case> stage (under <output>)", environment="replaced: format_check.ENVIRONMENT {PATH=/usr/bin:/bin, LANG=C.UTF-8, LC_ALL=C.UTF-8, TZ=UTC, UV_THREADPOOL_SIZE=2}",
    bytecode_guard="not Python", mocked=False, conditions="R1: the derived selection pair reaches the unit process; tests/test_static_tray_readback_v01.py:142 -> current_host_readback_v01 facade -> current_host_readback_v02.guarded_run_process:1111. R2: setUpClass raises the ordinary-run reason first",
    run_kinds=["R1"], verdict_notes="Exactly 3 in R1 (Q01-positive, Q03-positive, Q01-changed-reference, in that order); 0 in R2.")
add(id="RB-02", file="prototypes/static_tray_v01/current_host_readback_v02.py", line=461, steps=["unit-tests"], tests=["test_static_tray_readback_v01.ReadbackCPUControls (setUpClass, the three methods, tearDownClass)"],
    program="the HOST-bound Git implementation (absolute developer-tools path) through check_local.git_read", program_kind="git",
    argv_pattern=["<bound git>", "-c", "core.fsmonitor=false", "-C", "<workspace>", "rev-parse --show-toplevel | rev-parse --verify HEAD^{commit} | rev-parse --verify <commit>^{tree} | status --porcelain=v1 --untracked-files=no | ls-files --others --exclude-standard -z"],
    cwd="unit cwd", environment="check_local.git_environment(<workspace>)", bytecode_guard="not Python", mocked=False,
    conditions="5 reads per _selection: setup 2, each attempt 3 (preflight, launch, postflight), finish 1", run_kinds=["R1"], verdict_notes="60 Git starts in R1; 0 in R2.")

# ---------------------------------------------------------------- mocked or forbidden
for row in (
    ("M-01", "prototypes/static_tray_v01/format_check.py", 168, "test_static_tray_readback_v01.ReadbackCoordinatorSeams", "patch.object(format_check, 'run_process', side_effect=child)"),
    ("M-02", "prototypes/static_tray_v01/transaction.py", 321, "test_static_tray_transaction_v01 (lines 321 and 373)", "patch.object(tx, 'run_process', side_effect=self.fake_process)"),
    ("M-03", "prototypes/static_tray_v01/current_host_inspection_v01.py", 3496, "test_current_host_inspection_v01, _required_images_v01, _rtld_paths_v01, _libc_* (the 0.1.0 Linux inspection, ldd)", "subprocess and os start functions patched to raise; helpers patched"),
    ("M-04", "prototypes/static_tray_v01/supervisor_darwin_v01.py", 155, "test_current_host_readback_controls_v02 ProviderWorld (MC21, MC29, MC30, MC31 ...), test_current_host_readback_provider_v02, test_current_host_readback_provider", "darwin.run_process mocked (delegate) or the provider refuses before it; supervisor.run_process patched to raise"),
    ("M-05", "prototypes/static_tray_v01/current_host_observation_v02.py", 2533, "test_current_host_observation_v02 (observe in process)", "mocked supervisor writes synthetic logs"),
    ("M-06", "tools/doctor_local.py", 108, "DoctorCase and SetupCase tests (fake run)", "LocalProject.run answers venv, pip, node --version, lsof, ps and probes; only git and chat_workflow.py commands reach doctor.execute"),
    ("M-07", "tools/check_local.py", 666, "test_current_host_readback_driver*, test_current_host_readback_controls_v02 MC21 (Popen patched)", "patch.object(checks.subprocess, 'Popen')"),
    ("M-08", "prototypes/static_tray_v01/supervisor.py", 185, "none for real on macOS", "the Linux prctl lookup raises before Popen; patched to raise in the MI controls"),
):
    add(id=row[0], file=row[1], line=row[2], steps=["unit-tests"], tests=[row[3]], program="none (substituted)", program_kind="mocked",
        mocked=True, conditions=row[4], run_kinds=["R1", "R2"], verdict_notes="No real start.")
add(id="X-01", file="(not reached by any of the seven steps)", line=None, steps=[], tests=[],
    program="git, node (args.node), /usr/bin/ldd, sys.executable children", program_kind="unreached",
    conditions=("format_check.build_manifest (node --version, /usr/bin/ldd; CLI 'seal-readback' only), ontokin/force_conformance.record_external (CLI only), "
                "tools/verify_reach_destinations.run, tools/verify_torque_native_dense*.main, tools/run_*_acceptance and audit_* git helpers whose tests import pure functions only, "
                "the 8 tools/second_target_*/tests/run_controls.py (not under tests/), tools/storage_tests/ (not discovered), prototypes/guided_contact_*, prototypes/semantic_receiving_c211/run.py, "
                "prototypes/static_tray_v01/lifecycle*.py, lock.build_lock, docs/language-design scripts"),
    mocked=False, run_kinds=[], verdict_notes="Listed for completeness; no test or step calls them.")

VERDICTS = {
    "1_every_start_enumerated": {"verdict": "YES", "limit": "Git-internal descendants (DRV-05) and exact per-test Git counts are not enumerated; counts in R2 are upper bounds because failing tests may stop early; dynamic routes cannot be excluded by reading"},
    "2a_foreign_node": {"verdict": "YES (PATH-dependent)", "detail": "U-28 and U-30 start the first node on the inherited PATH (tools/doctor_local.py:737-741), up to 6 starts per run kind; NO under PATH=/usr/bin:/bin"},
    "2b_ldd_codesign_otool": {"verdict": "NO", "detail": "no reachable start names them; /usr/bin/ldd absent; the ldd sites are unreached or forbidden (X-01, M-03)"},
    "2c_other_programs": {"verdict": "NO under PATH=/usr/bin:/bin; YES (PATH-dependent) otherwise", "detail": "bare names git, uname, file, node, python3.12 and git's lfs helper follow PATH; under /usr/bin:/bin they resolve to /usr/bin/git (developer tools' Git), /usr/bin/uname, /usr/bin/file, and nothing"},
    "3a_python_trees": {"verdict": "NO (expected)", "detail": "4 kinds of bytecode-writing starts (U-26 x8, U-27 x2, U-30 venv x1, U-18 grandchild x1) import only standard-library modules whose opt-level-0 bytecode exists and is fresh, and nothing from the .venv (no .pth, no third-party import)", "residual": "static closure; a dynamic import cannot be excluded"},
    "3b_pinned_runtime_and_reader_tree": {"verdict": "NO"},
    "3c_worktree": {"verdict": "NO", "condition": "the driver itself is started with -B (it imports tools/ and, in R1, prototypes/static_tray_v01 modules from <worktree>)"},
    "4_expected_node_starts": {"verdict": "CONFIRMED", "R1": 3, "R2": 0, "condition": "PATH holds no node (else +up to 6 foreign node --version starts per run)"},
    "5_order": {"verdict": "ESTABLISHED", "readback_module_position": 337, "modules": 389, "risky_before": ["test_bootstrap_local (5)", "test_doctor_local (32)", "test_local_checks (105)", "MC22 nested readback child in test_current_host_readback_controls_v02 (24)"]},
    "6_other_risks": {"verdict": "SEE REPORT", "items": ["PATH must exclude other node, git-lfs, python3.12, uname, file and git directories", "driver without -B would write __pycache__ into <worktree>/prototypes/static_tray_v01 and make validate_selection refuse (SOURCE-BYTECODE)", "provider refuses any __pycache__, .pyc, .DS_Store or added file in the four workspace source trees; no test writes there by reading; main's baseline workspaces have none", "check_local._GIT_STATE is left as an unbound PATH resolution by earlier tests, which bind_git accepts", "MC16 needs <output> and TMPDIR on different volumes (I-05)", "doctor Git children read the user's global Git configuration"]},
}
NODE = {"R1": {"pinned_runtime_through_provider": 3, "other_node": "0 under PATH=/usr/bin:/bin; up to 6 otherwise (U-28 x3, U-30 x3)"},
        "R2": {"pinned_runtime_through_provider": 0, "other_node": "0 under PATH=/usr/bin:/bin; up to 6 otherwise"}}

real = [e for e in E if not e["mocked"] and e["program_kind"] not in ("no-start", "path-lookup-only", "signal-only", "unreached")]
out = {"schema": "ontokin.c271.p36-w1-start-inventory/1", "worker": "W1", "phase": "C271-P36", "gate": "MR",
       "candidate": {"branch": "work/c271-missing-import-digest-control", "commit": "d3b622d61745259c3477bc94be0fb4da05c23c56"},
       "labels": {"<worktree>": "the C271 worktree", "<workspace>": "the driver's isolated copy under its output directory",
                  "<output>": "the driver's --output-dir", "<local>": "the local data root beside the clone",
                  "<tmp>": "the temporary directory", "<framework>": "the framework interpreter's version directory under <prefix>",
                  "<prefix>": "the package manager's installation prefix"},
       "verdicts": VERDICTS, "expected_node_starts": NODE,
       "counts": {"entries": len(E), "real_start_entries": len(real), "mocked_entries": sum(1 for e in E if e["mocked"]),
                  "no_start_or_lookup_entries": sum(1 for e in E if e["program_kind"] in ("no-start", "path-lookup-only", "signal-only")),
                  "unreached_group_entries": sum(1 for e in E if e["program_kind"] == "unreached")},
       "entries": E}
with open(sys.argv[1], "x", encoding="utf-8") as stream:
    json.dump(out, stream, indent=1, ensure_ascii=True)
    stream.write("\n")
print(json.dumps(out["counts"]))
