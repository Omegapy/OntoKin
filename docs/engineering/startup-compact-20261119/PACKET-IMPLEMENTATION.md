# Optional startup packet implementation evidence

## Status and scope

Working implementer candidate; independent review and integration remain Director-owned. Only `tools/startup_context.py`, `tests/test_startup_context.py` and this evidence file belong to this assignment. No repository Git write, README edit, source mutation or remote operation was performed by the helper. Tests use disposable local Git repositories.

The implementation is standard-library-only. It selects the registry required reads, active task (else latest task) with task JSON/requirements/plan, and every registry skill from regular Git blobs at an explicit full commit SHA. It uses a visible, nonrecursive literal glossary and length-delimited UTF-8 records. Every build is decoded and compared byte-for-byte with its selected Git inputs before emission; verification derives the cohort anew and rejects changed metadata, omitted/added/reordered paths or any changed source byte. No per-file hashes are embedded in the viewed packet; hashes appear in verification reports.

Build: `python3 tools/startup_context.py --ref FULL_COMMIT_SHA [--omit-entry] [--output NEW_FILE]`. Verify: `python3 tools/startup_context.py --verify PACKET [--ref EXPECTED_FULL_SHA]`. Expand: `python3 tools/startup_context.py --expand PACKET`; expansion emits verified raw-text records with zero aliases and never extracts source files. `--output` creates a new file exclusively; stdout is the default. Live GitHub-head observation remains external. `--omit-entry` explicitly asserts the entrypoint was already read at this same REF; the tool cannot independently prove that reading. Nested AGENTS and scope specifications remain extra. Every failure instructs direct reads; no instructions are silently skipped.

Limits: 128 selected files; 2,000,000 bytes per source file; 16,000,000 source bytes total; 24,000,000 packet bytes; 96 glossary entries; at most 500 initial candidate fragments sampled over at most approximately 32,000 token starts; fragment sizes 8/12/16/24/32/48/64 regex tokens; JSON nesting at most 64. Bounded candidate search can miss compression opportunities without losing source bytes. Reserved `§` plus three-digit strings in original content are rejected; ordinary section references such as `§1` remain literal. Oversized, malformed or colliding input falls back to direct source reading.

## Validation record

```json
{
  "time_utc": "2026-11-19T15:44:52.078805+00:00",
  "python": "3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]",
  "platform": "Linux-6.18.57-x86_64-with-glibc2.41",
  "source_revision": "2c800160880a496aa3c06770b66ae9caab246adb",
  "test_command": "python3 -B -m unittest tests.test_startup_context -v",
  "test_exit_code": 0,
  "diff_check_exit_code": 0,
  "candidate_files": [
    {
      "path": "tools/startup_context.py",
      "bytes": 26030,
      "sha256": "a5eccf81f399176bf7c237982bdaa33537e54e784f6fdbe5bb933b17321acde8"
    },
    {
      "path": "tests/test_startup_context.py",
      "bytes": 16429,
      "sha256": "75c09cdb935ac05a202e223639d6962e90a920363ca45a3ffc7e8a1df0996d5f"
    }
  ],
  "packet_build_and_git_verify": {
    "verified": true,
    "source_revision": "2c800160880a496aa3c06770b66ae9caab246adb",
    "task": "C268",
    "omit_entry": true,
    "files": 14,
    "glossary_entries": 15,
    "source_bytes": 74387,
    "packet_bytes": 72625,
    "saved_bytes": 1762,
    "reduction_percent": 2.369,
    "token_count": "not measured; bytes are not model tokens",
    "limits": "Git byte equivalence only; live GitHub head, prior entry reading and extra scope reads require separate observation",
    "sources": [
      {
        "path": "AGENTS.md",
        "bytes": 8271,
        "sha256": "e60cd7d221aafe1a5a35a44a28c7541fe16749b3db603f5def34aa0d6bd9f50f"
      },
      {
        "path": "GOAL.md",
        "bytes": 12386,
        "sha256": "9256b77ed78e4a27a2b76c9f9c45f970de93b9bf98e4a8d7f1d1241b4624562c"
      },
      {
        "path": "STATUS.md",
        "bytes": 10620,
        "sha256": "44dc6e1f33711dcb071e0ff96681a50e6f1bfc581d61136f8af64db49320ccfe"
      },
      {
        "path": "ROLE.md",
        "bytes": 1744,
        "sha256": "917bf126943193de88d059771a7b6553a5dc41d02770859b544ffcf191ff9175"
      },
      {
        "path": "docs/workflow/registry.json",
        "bytes": 1172,
        "sha256": "b32db9ac5a464479f9a44f1cabed20dc1f1fd34e3810248ef0a24061c2acb536"
      },
      {
        "path": "docs/workflow/CURRENT.json",
        "bytes": 2475,
        "sha256": "e78150ac07c0a879d9c18fd449390382199b6d35636ee8b3f662f1e6caf5faa2"
      },
      {
        "path": "docs/workflow/PROTOCOL.md",
        "bytes": 12342,
        "sha256": "72ee4b363619ef62a38642420b9581389435597adbce728e8f5ee536ca803880"
      },
      {
        "path": "docs/workflow/HANDOFF.md",
        "bytes": 6952,
        "sha256": "84827c5a9ef2113c161e7356cfd9a82ad792dd0a10d7eb86ce1a4bdf5d8e089a"
      },
      {
        "path": "docs/workflow/tasks/C268/task.json",
        "bytes": 6966,
        "sha256": "f62a3ebf686f630bcd912eb56dbec1f50a83191c0db8be58944ea90ab908831c"
      },
      {
        "path": "docs/workflow/tasks/C268/REQUIREMENTS.md",
        "bytes": 3580,
        "sha256": "6244d41ce510b2fbd07d076090e8f758375374d44b7e182f7a1f627d323ecf86"
      },
      {
        "path": "docs/workflow/tasks/C268/PLAN.md",
        "bytes": 2565,
        "sha256": "64f3f6b94360612a7deab43b3a48b7e933bc11f77a42330e7478b9b40524901b"
      },
      {
        "path": ".agents/skills/ontokin-session/SKILL.md",
        "bytes": 1400,
        "sha256": "1c5ff15651da466999c0122aa3bd442b40e87a4d3a0cd67e619e9d23cdf01c1a"
      },
      {
        "path": ".agents/skills/ontokin-delivery/SKILL.md",
        "bytes": 1390,
        "sha256": "f90c4ddf62de8d3a07c4d077a72da9fe01d3e1e2a45867bfa6d86f2b54bca8ed"
      },
      {
        "path": ".agents/skills/ontokin-learning/SKILL.md",
        "bytes": 2524,
        "sha256": "c9c106168e3b3e7aecb322249c2de74b909a842d6d2d4c66d9b3cdf432498cad"
      }
    ]
  }
}
```

### Focused test output

```text
test_active_task_all_skills_and_order_are_derived_from_git (tests.test_startup_context.StartupContextTests.test_active_task_all_skills_and_order_are_derived_from_git) ... ok
test_alias_collision_fails_and_cli_prescribes_direct_reads_without_output (tests.test_startup_context.StartupContextTests.test_alias_collision_fails_and_cli_prescribes_direct_reads_without_output) ... ok
test_cli_verify_expand_and_exclusive_output (tests.test_startup_context.StartupContextTests.test_cli_verify_expand_and_exclusive_output) ... ok
test_deep_json_and_duplicate_keys_fail_as_packet_errors (tests.test_startup_context.StartupContextTests.test_deep_json_and_duplicate_keys_fail_as_packet_errors) ... ok
test_expansion_length_is_checked_before_materializing_large_values (tests.test_startup_context.StartupContextTests.test_expansion_length_is_checked_before_materializing_large_values) ... ok
test_incomplete_git_batch_is_rejected (tests.test_startup_context.StartupContextTests.test_incomplete_git_batch_is_rejected) ... ok
test_invalid_utf8_and_noncommit_or_abbreviated_revisions_fail (tests.test_startup_context.StartupContextTests.test_invalid_utf8_and_noncommit_or_abbreviated_revisions_fail) ... ok
test_latest_task_is_selected_only_without_active_task (tests.test_startup_context.StartupContextTests.test_latest_task_is_selected_only_without_active_task) ... ok
test_missing_required_git_file_is_rejected (tests.test_startup_context.StartupContextTests.test_missing_required_git_file_is_rejected) ... ok
test_missing_skill_is_rejected (tests.test_startup_context.StartupContextTests.test_missing_skill_is_rejected) ... ok
test_missing_task_plan_is_rejected (tests.test_startup_context.StartupContextTests.test_missing_task_plan_is_rejected) ... ok
test_omit_entry_records_explicit_same_ref_assertion (tests.test_startup_context.StartupContextTests.test_omit_entry_records_explicit_same_ref_assertion) ... ok
test_omitted_added_and_reordered_cohorts_are_rejected (tests.test_startup_context.StartupContextTests.test_omitted_added_and_reordered_cohorts_are_rejected) ... ok
test_packet_input_rejects_devices_fifos_and_oversized_files (tests.test_startup_context.StartupContextTests.test_packet_input_rejects_devices_fifos_and_oversized_files) ... ok
test_readme_in_required_reads_is_a_failure_not_a_silent_skip (tests.test_startup_context.StartupContextTests.test_readme_in_required_reads_is_a_failure_not_a_silent_skip) ... ok
test_roundtrip_preserves_unicode_newlines_punctuation_and_all_bytes (tests.test_startup_context.StartupContextTests.test_roundtrip_preserves_unicode_newlines_punctuation_and_all_bytes) ... ok
test_same_length_source_tamper_is_detected_against_git (tests.test_startup_context.StartupContextTests.test_same_length_source_tamper_is_detected_against_git) ... ok
test_symlink_source_is_rejected (tests.test_startup_context.StartupContextTests.test_symlink_source_is_rejected) ... ok
test_uncommitted_working_files_cannot_change_the_selected_bytes (tests.test_startup_context.StartupContextTests.test_uncommitted_working_files_cannot_change_the_selected_bytes) ... ok
test_unknown_alias_recursive_definition_duplicate_path_and_trailing_data (tests.test_startup_context.StartupContextTests.test_unknown_alias_recursive_definition_duplicate_path_and_trailing_data) ... ok
test_unsafe_paths_and_readme_variants_are_rejected (tests.test_startup_context.StartupContextTests.test_unsafe_paths_and_readme_variants_are_rejected) ... ok
test_wrong_byte_lengths_and_truncated_values_fail (tests.test_startup_context.StartupContextTests.test_wrong_byte_lengths_and_truncated_values_fail) ... ok
test_wrong_task_skills_entry_assertion_and_expected_revision_are_rejected (tests.test_startup_context.StartupContextTests.test_wrong_task_skills_entry_assertion_and_expected_revision_are_rejected) ... ok

----------------------------------------------------------------------
Ran 23 tests in 1.823s

OK
```

The tests exercise actual temporary Git input selection/current-versus-latest task/omit-entry; exact Unicode, CRLF, literal punctuation and missing final newline; unchanged results despite dirty working files; literal alias collisions and CLI fallback; unsafe/README/symlink/missing sources; malformed framing, unknown/recursive aliases, duplicate paths and trailing bytes; valid-length source tampering; cohort and metadata tampering; expected-revision binding; expansion budgets; malformed/deep JSON; incomplete Git reads; device/FIFO/oversized packet rejection; verify/expand CLI behavior; and refusal to overwrite an existing output.

### Earlier result retained

Initial focused run: 22 tests, 21 passed and one failed (2.094 seconds). `test_deep_json_and_duplicate_keys_fail_as_packet_errors` did not reject 2,000 JSON nesting levels on this interpreter (`AssertionError: PacketError not raised`). The fix adds an explicit 64-level preflight rather than relying on Python recursion behavior. A subsequent 22-test run passed in 1.633 seconds. The final run above also includes the newly added bounded input-file test. The reviewer identified the device/FIFO and growing-input risk before executing an unbounded read; it was corrected with a nonblocking open, regular-file descriptor check and `read(MAX_PACKET + 1)`.

## Measured value and disposition recommendation

Measurements use tiktoken 0.12.0 / `o200k_base` installed privately for measurement only, not imported by the helper. At pinned commit `2c800160880a496aa3c06770b66ae9caab246adb`, direct selected inputs including START total **16,622 tokens**; the already-read START contributes **620 tokens**. Effective packet cost below includes all packet headers/glossary/metadata plus those 620 START tokens. These are tokenizer measurements, not claims about every model tokenizer.

| Probe | Candidate cap | Definitions | Packet bytes | Packet tokens | Effective tokens | Net token reduction | Elapsed seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Default byte-gain implementation | 500 | 15 | 72,625 | 15,865 | 16,485 | 0.824% | 0.344 |
| In-memory wider candidate pool | 5,000 | 96 | 70,173 | 15,782 | 16,402 | 1.324% | 2.075 |
| In-memory actual-token-gain probe | 5,000 | 48 | 71,014 | 15,575 | 16,195 | 2.569% | 1.115 |

The two wider probes changed only measurement-process memory; the shipped candidate remains the 500-candidate standard-library version. The actual-token-gain probe is exploratory, not a proven optimal bound. It suggests that additional complexity offers little benefit on this cohort. **Implementer recommendation: do not integrate the optional helper solely for context savings unless the Director accepts this maintenance cost for the measured small gain.** Preserve the conservative prose compression independently. No independent-review or publication claim is made here.
