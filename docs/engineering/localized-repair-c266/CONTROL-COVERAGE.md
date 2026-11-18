# C266 independent control coverage

The final independent suite passes **34 test methods and 748 public API calls**
on CPython 3.12.14 in the assistant's hosted Linux x86-64 environment. All
**28 expected bindings** and **720 expected typed refusals** matched their
expected outcomes; there were zero failures, errors or skips. The
[final results](evidence/independent-controls/run-02/results.json) retain each
case, input identities, actual outcome, command and environment. The
[test log](evidence/independent-controls/run-02/unittest.txt) records the method
results. Each run also retains its exact checked code and a content-addressed
`inputs.zip` containing the supplied byte inputs.

This qualifies the C266 **source/program/object input-binding prerequisite**
only. It does not qualify `compare_hinges`, any complete hinge set, ordered
endpoint agreement or a historical endpoint. **No complete C260 H group is
closed by this suite.** The H references below identify partial obligations
from the unchanged [C260 control plan](../localized-repair-c260/CONTROL-PLAN.md),
not complete group passes.

## Independent expected values and exact inputs

[The fixture helper](binding_control_fixtures.py) imports no observer, product
parser, evaluator, exporter, producer sidecar or C257 comparator. It constructs
expected identities and complete mapping records from the adopted construction
rules and known authored source recipes. Its byte-span helpers locate those
explicit fixture fragments; they are not a general source-validity checker.

For both original C210 endpoints, the helper independently reconstructs all
18 object maps, including full keyed-entry spans, and checks equality with the
actual retained artifact mappings. Other controls construct their own compact
two-source fixtures and artifact metadata. The canonical program digest uses
the adopted domain separator and canonical manifest serialization. Expected
answers are not read from the implementation under test.

| Checked final input | Bytes | SHA-256 |
| --- | ---: | --- |
| `hinge_binding.py` | 17,639 | `68849dbe3339c158eac7ec43fb1defcbd2993c37c6a0a5ee813d2da71fb03dda` |
| `test_hinge_binding.py` | 29,777 | `582adecab5975b922ce123851f6b76b7d86e2947664d79818055c19e4ed3c26b` |
| `binding_control_fixtures.py` | 17,102 | `fc675e5da709a1f67892d929d90701833a62dd55f6fd0b9798b1c95496fca983` |
| Pinned C265 source observer | 37,570 | `04bea0f7c5f82a3e3e74610d3ee98755f44ed0905566c00eb063647e31abbf9e` |
| Pinned C261 raw reader | 14,036 | `6167b3a56a2b1a600812340d85ee02eaa3b6399801d585a758333aabcfaa5e08` |
| Pinned C257 utility | 35,942 | `c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1` |

The checked implementation SHA-256 is identical in both retained runs. Test and
fixture hashes changed only for the fixture correction described below.

## Actual method and call inventory

The method names are exact names in [test_hinge_binding.py](test_hinge_binding.py).
`Bindings` and `Refusals` count public API calls, including the separately
recorded mutations within each method. They do not count independent scientific
qualifications. Every row remains partial with respect to C260.

| Test method | Bindings | Refusals | Partial C260 relation and actual checked behavior |
| --- | ---: | ---: | --- |
| `test_original_before_and_after_all_objects` | 2 | 0 | H01, H22: exact original inputs and all 18 source/object provenance associations; no hinge comparison or historical admission |
| `test_changed_membership_and_opaque_keys` | 4 | 0 | H19, H27: inserted/deleted/reordered membership, distinct dotted/underscored/hyphenated literal keys and changed object counts |
| `test_direct_helper_and_final_override_memberships` | 4 | 0 | H19: helper/direct defaults, helper override and final owner overrides of a distinct class default |
| `test_renamed_names_separate_from_punctuation_keys` | 1 | 0 | H19, H22, H27: renamed module, class, root and member names/keys remain separate identity inputs |
| `test_unicode_offsets_are_utf8_bytes` | 4 | 0 | H22: Unicode comments shift declarations; all four membership recipes bind exact UTF-8 byte positions |
| `test_every_repeated_provenance_leaf_node_program_and_both` | 0 | 375 | H21, H22: each leaf of representative root/generated/ordinary object maps is contradicted in the node copy, program copy and both copies |
| `test_every_mapping_member_is_required_in_each_copy` | 0 | 135 | H22: each mandatory top-level/nested mapping member is removed independently from either or both copies |
| `test_unknown_mapping_members_refuse_at_every_dictionary` | 0 | 27 | H22: unknown fields at each consumed mapping dictionary refuse rather than acquire authority |
| `test_mapping_containers_require_their_actual_types` | 0 | 45 | H22, H24: mappings, identities and path-step containers have their required shapes; empty mappings are not partial success |
| `test_python_numeric_equality_does_not_admit_wrong_json_types` | 0 | 27 | H22, H24: integer spans cannot become integral floats; the generated boolean cannot become an equal integer |
| `test_full_input_entry_span_cannot_be_replaced_with_key_token` | 0 | 4 | H19, H22: each membership recipe requires the entire keyed entry, not merely its quoted key token |
| `test_nested_root_and_owner_paths_are_not_display_hints` | 0 | 3 | H21, H22: consistent forgeries of root path, owner path or generated ancestry refuse against source |
| `test_all_program_manifest_and_source_unit_claims` | 0 | 26 | H22: every canonical manifest/source-unit leaf is independently corrupted |
| `test_sparse_and_unknown_program_manifest_source_units` | 0 | 35 | H22: missing or unknown manifest/source-unit dictionary members refuse |
| `test_program_manifest_unit_order_is_canonical` | 0 | 1 | H22: reversed canonical manifest unit order refuses |
| `test_entry_and_program_revisions_and_source_ids` | 0 | 12 | H22: stale, missing or wrongly typed entry/program revisions and source IDs refuse |
| `test_every_node_scalar_claim_against_source` | 0 | 4 | H21, H22: node path, full object ID, class and program revision bind against source |
| `test_missing_object_from_both_artifact_tables` | 0 | 1 | H21: removing the same source object from both artifact tables does not authorize an incomplete set |
| `test_extra_object_in_both_artifact_tables` | 0 | 1 | H21: adding a consistently repeated unsupported object does not authorize an extra set member |
| `test_duplicate_object_id_and_path` | 0 | 2 | H21: duplicate object IDs and paths refuse |
| `test_consistent_renaming_of_claimed_path_without_source_refuses` | 0 | 1 | H21, H22: mutually agreeing artifact copies cannot independently authorize a source path rename |
| `test_node_and_mapping_order_do_not_define_identity` | 1 | 0 | H21, H22: node and dictionary insertion order may change; returned node indices follow actual reordered nodes |
| `test_stale_source_bytes_and_dependency_pin` | 0 | 3 | H22: changed entry, changed dependency with stale pin, and corrected pin with stale artifact each refuse |
| `test_duplicate_owner_override_remains_a_refusal` | 0 | 1 | H19: the pinned duplicate same-scope override refusal remains enforced |
| `test_crossed_original_endpoint_provenance_refuses` | 0 | 1 | H22: original before-source bytes cannot bind to after-artifact provenance |
| `test_changed_hinge_fields_can_still_bind` | 7 | 0 | H03/H05/H08/H12/H14 boundary only: changed raw initial, axis, limits, endpoints, joint path or joint ID can bind; hinge agreement remains explicitly false |
| `test_omitted_added_and_reordered_hinges_can_still_bind` | 4 | 0 | H21 boundary only: missing/extra/reordered joint rows can bind; complete joint-set agreement remains explicitly false |
| `test_unobserved_metadata_cannot_be_promoted_to_authority` | 1 | 0 | H20, H23, H28 boundary only: top-level module/scene, omitted program collections, URI/prose, names, transforms, geometry and unrelated ownership metadata stay unobserved |
| `test_sparse_object_mapping_is_not_partial_success` | 0 | 1 | H22: two empty repeated object maps do not qualify any input binding |
| `test_bounded_available_identity_retained_on_binding_refusal` | 0 | 1 | H22, H24: a failed binding retains exact bounded input hashes and byte counts |
| `test_source_and_artifact_size_limits_remain_bounded` | 0 | 2 | H24: source/GLB byte bounds refuse and do not hash the oversized input merely for a diagnostic |
| `test_missing_extra_and_nonbyte_sources_refuse` | 0 | 5 | H24: missing/extra closure members and nonbyte source inputs refuse as typed outcomes |
| `test_nonbyte_artifact_and_structural_failures_are_typed` | 0 | 5 | H24: nonbyte artifacts, truncated headers/chunks and invalid GLB bytes refuse without host exceptions |
| `test_unsupported_source_and_raw_profile_are_not_bypassed` | 0 | 2 | H11/H23/H24 boundary only: unsupported computed source initial and a direct artifact site extension remain typed refusals through pinned observers |
| **Total: 34 methods** | **28** | **720** | **748 matched public API outcomes; no complete H group closed** |

## Preserved failed fixture attempt

[Run 01](evidence/independent-controls/run-01/results.json) executed 33 methods
and 747 API calls. It recorded 26 binding returns and 721 typed refusals, but
**the run failed with two errors**: two cases expected a binding and instead
received the correct inherited `DUPLICATE_OVERRIDE` refusal. These are not
reported as 747 matched expectations or as an implementation pass.

The initial `final_override` recipe assigned the same owner parameter twice
within one object block. That is distinct from applying a final owner override
to a class default. The corrected positive recipe declares a distinct
`discarded` class-default member and one direct override per owner. A new
negative control explicitly retains the duplicate same-scope refusal. The
implementation and all three pinned dependency hashes were unchanged.

The original failed input bytes, failure log and exact pre-correction test and
fixture helper are retained alongside the checked implementation under
`evidence/independent-controls/run-01/`. Run 02 is a separate fresh directory;
it did not replace or rewrite run 01.

## Remaining qualification

C266 establishes whether the selected source/program/object records belong
together. The successful comparison of hinge fields, hinge definition/path/ID
sets and ordered source-associated endpoints remains a later interface. The
tests that permit changed or omitted hinges are intentional nonclaim controls,
not passes for those future comparison obligations.

H01 still needs complete hinge/endpoint comparison and its distinct historical
admission. H02–H18 still need the applicable comparison controls; inherited
source/raw suites and the boundary controls here do not close those groups.
H19–H24 and H27–H28 retain their broader source, comparison, resource or
nonclaim obligations beyond the partial checks listed above. H25's complete
numeric-limit policy is not newly qualified here. H26's historical file
admission, path/symlink and I/O checks are excluded and unrun in this slice.

Source site poses remain unevaluated. No source-derived site or joint
definition/span is relabeled a direct artifact record. Top-level module/scene
and program collections omitted from C261's public excerpt remain explicitly
unobserved. Full source/GLB validity, accepted revisions, edit atomicity,
rebuild equivalence, physical/native behavior, model trials, complete C255
semantics and comparative advantage remain unqualified.

The command for a new independent run is:

```sh
python3.12 -B docs/engineering/localized-repair-c266/test_hinge_binding.py --evidence-dir /tmp/c266-fresh-controls
```

The output directory must not already exist. Candidate publication,
independent code review, integration, actual-main verification and confirmed
saved delivery require their separate receipts.
