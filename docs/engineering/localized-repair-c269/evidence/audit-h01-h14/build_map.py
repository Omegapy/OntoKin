#!/usr/bin/env python3
"""Render the human-audited H01-H14 clause map from retained evidence indexes."""
from __future__ import annotations

import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
P = "docs/engineering/"
OWN = P + "localized-repair-c269/evidence/audit-h01-h14/"
BASE = "23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb"
INDEX = json.loads((HERE / "EVIDENCE-INDEX.json").read_text())
FILES = {
    "C265": P + "localized-repair-c265/test_source_hinges.py",
    "C267": P + "localized-repair-c267/test_hinge_compare.py",
    "C268": P + "localized-repair-c268/test_endpoint_reader.py",
    "F266": P + "localized-repair-c266/binding_control_fixtures.py",
    "F267": P + "localized-repair-c267/comparison_control_fixtures.py",
    "F268": P + "localized-repair-c268/endpoint_control_fixtures.py",
}
RAW_PATH = P + "localized-repair-c261/evidence/independent/independent_controls.py"


def source(suite, method, assertion):
    path = FILES[suite]
    bounds = INDEX["method_locations"][path][method]
    return {"path": path, "revision": BASE, "method": method,
            "line_reference": bounds, "assertion": assertion}


def raw_source(start, end, assertion):
    return {"path": RAW_PATH, "revision": BASE, "method": "independent module-level case construction and audit()",
            "line_reference": {"start_line": start, "end_line": end}, "assertion": assertion}


def result(suite, method=None, label=None, pattern=None):
    metadata = INDEX["suites"][suite]
    selected = []
    for row in metadata["records"]:
        if method is not None and row.get("case", row.get("test", "")).split(".")[-1] != method:
            continue
        if label is not None and row.get("label") not in ([label] if isinstance(label, str) else label):
            continue
        if pattern is not None and not re.search(pattern, row.get("name", "")):
            continue
        selected.append(row)
    assert selected, (suite, method, label, pattern)
    out = {"path": metadata["result_path"], "record_pointers": [row["result_pointer"] for row in selected],
           "execution_revision": metadata["execution_revision"],
           "input_hash_binding": {"path": OWN + "EVIDENCE-INDEX.json", "suite": suite,
                                  "record_ids": [row["id"] for row in selected]},
           "outcomes": [{"record_id": row["id"], "label": row.get("label", row.get("name", row.get("test"))),
                         "outcome": row.get("outcome", row.get("observed")), "code": row.get("code")}
                        for row in selected]}
    if "published_reexecution" in metadata:
        out["later_revision_bound_execution"] = metadata["published_reexecution"]
        out["provenance_note"] = metadata["revision_status"]
    else:
        out["revision_binding_path"] = metadata["revision_binding_path"]
    return out


GROUPS = []


def group(number, description, boundaries, reason):
    g = {"id": f"H{number:02}", "frozen_requirement": description, "status": "complete",
         "reason": reason, "relevant_interface_boundaries": boundaries, "required_subcases": []}
    GROUPS.append(g)
    return g


def sub(g, description, assertions, executions, construction):
    g["required_subcases"].append({"id": g["id"] + "." + str(len(g["required_subcases"]) + 1).zfill(2),
        "description": description, "status": "complete", "source_assertions": assertions,
        "execution_results": executions, "independent_expected_value_construction": construction,
        "remaining_gap": None})


S265 = lambda method, text: source("C265", method, text)
S267 = lambda method, text: source("C267", method, text)
S268 = lambda method, text: source("C268", method, text)

g = group(1, "Both original frozen endpoint bundles and GLBs: eight complete hinge rows each, one shared definition, sixteen associated endpoint sites, exact hashes historically admitted only by the historical API.",
    ["raw source", "untrusted raw artifact", "source/artifact comparison", "historical admission"],
    "Both exact originals have independently enumerated full-field/source-site expectations and passing comparison plus historical-admission assertions; other APIs retain false historical authority.")
sub(g, "Both original GLBs expose all eight exact raw joint rows and their actual JSON pointers.",
    [raw_source(67,108,"audit() checks complete claims, number/sign signatures, actual field pointers, all objects and false authority flags."), raw_source(179,180,"Both original artifact bytes are independently decoded and observed.")],
    [result("C261",pattern=r"^original-(before|after)$")],
    "Direct standard-library JSON decoding of the original GLB byte chunks; no expected hinge values from the observer.")
sub(g, "Both original source bundles yield eight hinges, one shared definition, and sixteen ordered source-associated sites.",
    [S265("test_h01_both_original_source_endpoints","Asserts 8 hinges, 16 sites, 18 objects, explicit occurrence IDs and the one explicit Finger/flex definition."),
     S265("test_h01_complete_associations_are_independently_derived","Asserts ordered pivot/blade.base IDs, whole paths, separate object/class IDs and source-only interface/size."),
     S267("test_original_before_after_exact_bytes","Tests both exact original GLB bytes and complete record/site assertions through accept().")],
    [result("C265","test_h01_both_original_source_endpoints"), result("C265","test_h01_complete_associations_are_independently_derived"), result("C267","test_original_before_after_exact_bytes")],
    "Explicit three-key first rack and five-key second rack from actual sources; definition keys and canonical literal fields are independently specified.")
sub(g, "Historical before/after admission verifies each frozen size/hash and preserves complete comparison records.",
    [S268("test_original_before_after_with_path_and_string_roots","Both endpoints with Path/string roots use accept()."), S268("accept","Checks exact historicalAdmission pins, true historical flag and false accepted-revision/physical/trial flags."),
     S268("assert_semantics","Asserts every joint and ordered endpoint field, shared definition, 16 sites, hashes and witnesses against independently authored expectations.")],
    [result("C268","test_original_before_after_with_path_and_string_roots")],
    "Five C260 pins transcribed independently in endpoint_control_fixtures.py and checked against INPUTS.json/C253; expected_hinges() enumerates the original source memberships.")
sub(g, "Original raw comparison remains nonhistorical; the wrapper alone marks admitted originals historical.",
    [S268("test_comparison_records_and_nonclaims_preserved","Original raw and historical results agree except the declared wrapper schema, historical flag and historical-limit sentence."),
     S267("accept","historicalInputsBound and acceptedRevisionQualified are explicitly false for raw comparisons."), S265("assert_unqualified","Source raw observations cannot acquire historical authority.")],
    [result("C268","test_comparison_records_and_nonclaims_preserved"),result("C267","test_original_before_after_exact_bytes"),result("C265","test_h01_both_original_source_endpoints")],
    "Authority booleans are asserted from the four-interface contract, independently of hinge values.")

g = group(2, "Supported source-only initial change with provenance rebinding exposes the changed source value, retains the artifact initial claim and refuses comparison disagreement.",
    ["raw source values are source-derived", "artifact values remain claims", "provenance binding precedes field comparison"],
    "Independent source-value controls plus actual archived source-only/rebound comparison bytes support the changed source and unchanged artifact initial; the result is FIELD_MISMATCH at the initial pointer.")
sub(g,"Changed in-range literal initials come from actual source bytes with an updated import pin.",
    [S265("test_h02_h04_initial_changes_follow_bytes","Checks 0.125 rad, -0.25 rad and independently converted 15 deg; changed import source bytes and false authority are asserted."),
     S268("exercise_changed_pair","Raw source initial 0.25 is asserted directly against independent expected values in the different-size recipe.")],
    [result("C265","test_h02_h04_initial_changes_follow_bytes"),result("C268","test_supported_different_size_paired_initial_change_stays_raw_only",label="changed paired raw source False")],
    "Byte replacement plus SHA-256 import repinning; decimal/rational canonical expectations are independent. The raw source and source-only comparison controls are distinct executions, not asserted to be one call.")
sub(g,"Correctly rebound source-only initial 0.25 leaves artifact initial 0 and refuses field disagreement.",
    [S267("test_initial_source_artifact_and_paired_changes","Constructs synthetic(source_initial='0.25[rad]') without changing the artifact expected initial and requires FIELD_MISMATCH."),
     source("F267","synthetic","Rewrites actual source, exact import digest, source/program/object provenance; artifact initial comes from the separate initial argument, default 0."),
     raw_source(67,108,"Separate raw controls verify actual supplied claims and their pointers, rather than substitute source values.")],
    [result("C267","test_initial_source_artifact_and_paired_changes",label="source-only initial with rebound provenance"),result("C261",pattern=r"^original-before$")],
    "The retained C267 input archive contains the changed literal and old artifact initial; INSPECTION.json decodes these bytes without running an observer. Result pointer is /extras/ontokin/joints/0/initial.")

g = group(3,"Artifact-only in-range initial change remains visible, comparison refuses, historical admission fails bytes.",
    ["raw artifact inspection", "field disagreement", "historical size/hash admission"],
    "C268 performs all three operations on the same actual same-size artifact-only 0-to-0.5 byte mutation, with explicit raw value and refusal assertions.")
sub(g,"Raw artifact observer returns the changed in-range initial.",
    [S268("test_artifact_only_initial_change_remains_visible_but_unbound","Changes one actual JSON initial 0.0 to 0.5, preserves size and asserts raw records[0].claims.initial == 0.5.")],
    [result("C268","test_artifact_only_initial_change_remains_visible_but_unbound",label="same-size GLB-only initial change")],
    "Equal-width literal JSON byte replacement in the original before GLB; original source bytes are unchanged.")
sub(g,"The artifact-only change gives FIELD_MISMATCH in comparison and HISTORICAL_BINDING/HASH in admission.",
    [S268("test_artifact_only_initial_change_remains_visible_but_unbound","Requires comparison.Fault FIELD_MISMATCH and then historical hash refusal on the identical changed GLB bytes."), S268("refuse","Checks expected category/reason and absence of a partial qualified result.")],
    [result("C268","test_artifact_only_initial_change_remains_visible_but_unbound",label=["raw disagreement remains a field refusal","GLB-only supported field change historical refusal"])],
    "Comparison and historical outcomes are independent expected categories from C260; the per-call artifact hashes identify the same mutation.")

g = group(4,"Paired supported initial change with refreshed import/program/source bindings passes changed-value comparison, fails historical admission and grants no accepted revision.",
    ["supported changed inputs are inspectable", "raw agreement is not historical admission", "no accepted-revision claim"],
    "C267 paired 0.25 initial succeeds; C268 independently repeats the changed initial across raw interfaces and comparison, then rejects entry/leaf/artifact historical admission and checks authority boundaries.")
sub(g,"Actual source and GLB initial fields both change with corrected provenance and compare as 0.25.",
    [S267("test_initial_source_artifact_and_paired_changes","Accepts source_initial='0.25[rad]', initial=0.25; accept() checks all source/artifact fields."),
     source("F268","paired_change","Different-size recipe edits actual source and eight GLB initials, rebuilds required spans/object mappings and manifest/source hashes."),
     S268("exercise_changed_pair","Checks changed raw source, raw artifact and full comparison semantics.")],
    [result("C267","test_initial_source_artifact_and_paired_changes",label="paired initial"),result("C268","test_supported_different_size_paired_initial_change_stays_raw_only",label=["changed paired raw source False","changed paired raw artifact False","changed paired raw comparison False"])],
    "Explicit 0.25 rational expectation; provenance recipes import no observer or product parser. Retained input ZIP proves real source and artifact bytes changed.")
sub(g,"Paired changed initials cannot acquire historical or accepted-revision authority.",
    [S268("exercise_changed_pair","Historical refusal is tested first on the paired bundle and separately after restoring entry and leaf bytes to expose each boundary."),
     S267("accept","Requires historicalInputsBound and acceptedRevisionQualified false on accepted changed comparisons.")],
    [result("C268","test_supported_different_size_paired_initial_change_stays_raw_only",label=["supported paired bytes are not historical False","paired changed leaf historical boundary False","paired changed GLB historical boundary False"]),result("C267","test_initial_source_artifact_and_paired_changes",label="paired initial")],
    "Frozen pin expectations are independent of field agreement: changed entry gives HASH; changed longer leaf and GLB give SIZE. No accepted-revision qualification is inferred.")

g = group(5,"Each ordered limit has independent source-only, artifact-only and paired mutations; actual fields drive outcomes without baseline substitution.",
    ["lower and upper positions remain ordered", "source rebinding isolates numeric mismatch", "paired agreement uses actual changes"],
    "C267 contains all six required lower/upper by source/artifact/paired cases, with source and artifact input hashes, exact mismatch outcomes and complete independent expected-field assertions on the two paired passes.")
for index, title, literal in ((0,"lower","-0.5 rad"),(1,"upper","0.5 rad")):
    for mode in ("source-only","artifact-only","paired"):
        label = f"{mode} limit {index}"
        sub(g,f"{title.capitalize()} limit changes to {literal} in the {mode} case.",
            [S267("test_each_limit_source_artifact_and_paired_changes",f"Index {index} is independently selected; {mode} actual input change requires " + ("full accepted changed-field equality." if mode == "paired" else "FIELD_MISMATCH.")),
             source("F267","synthetic","Source limits and artifact limit arguments are separate; exact import/source/program/object bindings are regenerated.")],
            [result("C267","test_each_limit_source_artifact_and_paired_changes",label=label)],
            "Explicit source expression and separately supplied numeric tuple. Archived bytes show only the selected ordered bound differs from its original counterpart; comparison results are not used to form expected values.")
sub(g,"Separate raw interfaces observe actual changed ordered limits.",
    [S265("test_h05_each_ordered_limit_changes_independently","Independently changes lower, upper and both source bounds; checks exact decimal/Pi64 conversion."),raw_source(182,183,"Raw changed limits are compared against directly decoded artifact JSON by audit().")],
    [result("C265","test_h05_each_ordered_limit_changes_independently"),result("C261",pattern=r"^supported-field-limits")],
    "Source expectations use the 1000-digit decimal reference; raw expectations use the exact mutated JSON values, with no fixed original limits substituted.")

g = group(6,"Closed boundary equality and zero-width ranges, including initial at either endpoint; reversed or out-of-range values refuse.",
    ["canonical comparisons are inclusive", "no epsilon or clamping", "source and artifact structural refusals"],
    "Independent source, raw artifact and paired-comparison controls cover both boundaries, zero/nonzero zero-width ranges, reversed ranges and lower/upper excursions.")
sub(g,"Initial at the lower and upper boundary compares successfully.",
    [S265("test_h06_inclusive_boundaries_and_zero_width","Exact -1 and +1 endpoints pass."),S267("test_inclusive_boundary_zero_width_and_invalid_ranges","Accepted paired -1/1 boundaries receive complete field assertions."),raw_source(184,185,"Raw lower/upper boundary claims are retained unchanged.")],
    [result("C265","test_h06_inclusive_boundaries_and_zero_width"),result("C267","test_inclusive_boundary_zero_width_and_invalid_ranges",label=["closed boundary -1 1 -1","closed boundary -1 1 1"]),result("C261",pattern=r"^inclusive-range-\(-1, 2")],
    "Simple exact radian integers remove conversion ambiguity; independent source and artifact literals agree.")
sub(g,"Zero-width ranges at zero and nonzero values pass without widening.",
    [S265("test_h06_inclusive_boundaries_and_zero_width","Tests 0.125 equal bounds and signed-zero bounds."),S267("test_inclusive_boundary_zero_width_and_invalid_ranges","Tests paired (0,0,0) and (0.25,0.25,0.25)."),raw_source(184,185,"Raw zero-width and signed-zero cases pass.")],
    [result("C265","test_h06_inclusive_boundaries_and_zero_width"),result("C267","test_inclusive_boundary_zero_width_and_invalid_ranges",label=["closed boundary 0 0 0","closed boundary 0.25 0.25 0.25"]),result("C261",pattern=r"^inclusive-range-\((0|-0\.0)")],
    "Independent exact binary fractions and zeros; no expected tolerance.")
sub(g,"Reversed ranges refuse in source and artifact inputs.",
    [S265("test_h06_reversed_or_outside_limits_refuse_without_clamping","Requires MALFORMED for reversed source range."),S267("test_inclusive_boundary_zero_width_and_invalid_ranges","Source and artifact reversed ranges both require MALFORMED."),raw_source(186,187,"Raw reversed-range refusal.")],
    [result("C265","test_h06_reversed_or_outside_limits_refuse_without_clamping"),result("C267","test_inclusive_boundary_zero_width_and_invalid_ranges",label=["invalid source closed range","invalid artifact closed range"]),result("C261",pattern=r"^invalid-range-\(1, -1")],
    "The low/high positions are deliberately reversed, and tests require refusal rather than sorting.")
sub(g,"Initial below or above the closed range refuses, including adjacent binary64 excursions.",
    [S265("test_h06_reversed_or_outside_limits_refuse_without_clamping","Tests negative value below zero and 1.0000000000000002 above one."),raw_source(186,187,"Tests -ulp(0) and nextafter(1,+inf) outside raw limits."),S267("test_inclusive_boundary_zero_width_and_invalid_ranges","Source and artifact 1.001 above one require MALFORMED.")],
    [result("C265","test_h06_reversed_or_outside_limits_refuse_without_clamping"),result("C261",pattern=r"^invalid-range-\(0, 1"),result("C267","test_inclusive_boundary_zero_width_and_invalid_ranges",label=["invalid source closed range","invalid artifact closed range"])],
    "Expected exact inequalities use independently authored finite values and math.nextafter/ulp in controls; there is no epsilon allowance.")

g = group(7,"Equivalent signed deg/rad literals and canonical negative zero; exact one-round Pi64 conversion and mismatch refusal for mathematically unequal or adjacent binary64 values.",
    ["exact represented Pi64, not mathematical pi", "one final binary64 rounding", "positive/negative zero compare equally", "exact field equality"],
    "Source controls independently calculate signed degrees, radian equivalents and halfway ties. Comparison controls cover degree/radian agreement, negative zero, fractional degrees and adjacent/subnormal disagreements. This is finite control coverage, not exhaustive numeric certification.")
sub(g,"Exact Pi64 degree conversion, signed values and equivalent radian literals use independent expectations.",
    [S265("canonical_decimal","Uses 1000-digit Decimal and exact Decimal.from_float(Pi64), then one float conversion."),S265("test_h07_pi64_single_round_literals_and_ties","Checks 0.1 deg, -45 deg, 180 deg and equivalent radian literal."),
     source("F267","angle","Independent rational conversion rounds once."),S267("test_exact_deg_rad_negative_zero_and_adjacent_values","45 deg and 0.7853981633974483 rad compare to the same exact canonical value; fractional degree is also checked.")],
    [result("C265","test_h07_pi64_single_round_literals_and_ties"),result("C267","test_exact_deg_rad_negative_zero_and_adjacent_values",label=["exact literal 45[deg]","exact literal 0.7853981633974483[rad]","exact literal 0.1[deg]"])],
    "Expected values derive from the exact binary64 Pi64 constant and independent Decimal/Fraction arithmetic, never from the observer.")
sub(g,"One-round binary64 ties-to-even policy is checked at two exact halfway radian literals.",
    [S265("test_h07_pi64_single_round_literals_and_ties","The two long decimal literals are halfway around one and round to the even adjacent binary64 values through the independent decimal reference.")],
    [result("C265","test_h07_pi64_single_round_literals_and_ties")],
    "The exact literals 1+2^-53 and 1+3*2^-53 exercise opposite tie directions; all actual input hashes are in the retained call ledger.")
sub(g,"Negative zero is admitted and compares equally; raw decoded sign is preserved.",
    [S265("test_h06_inclusive_boundaries_and_zero_width","Checks -0 deg initial with signed-zero radian bounds."),S267("test_exact_deg_rad_negative_zero_and_adjacent_values","Paired -0 deg initial passes exact comparison."),raw_source(58,79,"numeric_signature() uses float.hex() to ensure the raw -0.0 sign survives observation."),raw_source(182,185,"Raw -0.0 initial and signed-zero limits are exercised.")],
    [result("C265","test_h06_inclusive_boundaries_and_zero_width"),result("C267","test_exact_deg_rad_negative_zero_and_adjacent_values",label="exact literal -0[deg]"),result("C261",pattern=r"supported-field-initial--0\.0|inclusive-range-\(-0\.0")],
    "Source canonical signed-zero equality follows the frozen policy; raw sign retention is separately asserted by an exact hexadecimal representation.")
sub(g,"Adjacent binary64 and mathematically unequal finite initial values refuse instead of using a tolerance.",
    [S265("test_h07_adjacent_binary64_is_observed_distinctly","0.10000000000000002 is observed as nextafter(0.1,+inf), distinct from 0.1."),S267("test_exact_deg_rad_negative_zero_and_adjacent_values","Smallest positive subnormal versus zero and nextafter(0.25,+inf) versus 0.25 require FIELD_MISMATCH."),S267("test_initial_source_artifact_and_paired_changes","Different supported 0 and 0.25 initials also require disagreement.")],
    [result("C265","test_h07_adjacent_binary64_is_observed_distinctly"),result("C267","test_exact_deg_rad_negative_zero_and_adjacent_values",label=["adjacent binary64 initial 0x0.0000000000001p-1022","adjacent binary64 initial 0x1.0000000000001p-2"]),result("C267","test_initial_source_artifact_and_paired_changes",label="artifact-only initial")],
    "Independent math.nextafter values and exact finite literals identify the unequal numbers; recorded failures point at the initial field.")

g = group(8,"Six signed basis axes and paired axis reversal preserve exact sign with identity normalization and no motion fitting.",
    ["axis is parent-site declaration data", "basis normalization is identity", "axis sign changes the declared field"],
    "All six axes are asserted separately in raw source, raw artifact and paired comparison; both one-sided sign reversals refuse.")
sub(g,"All six signed basis axes are preserved by both raw observers.",
    [S265("test_h08_six_signed_basis_axes_preserve_sign","Enumerates three component positions and both signs and asserts full exact axes."),raw_source(188,191,"Independent raw cases enumerate the same six input axes; audit() compares actual claims/signatures.")],
    [result("C265","test_h08_six_signed_basis_axes_preserve_sign"),result("C261",pattern=r"^basis-")],
    "Six explicitly generated coordinate basis vectors; no norm or motion-derived expected value.")
sub(g,"All six actual paired source/artifact axes, including negative reversal, compare successfully.",
    [S267("test_six_signed_basis_axes_and_reversal","Constructs and accepts six paired basis-axis changes; accept() checks exact source/artifact axes and parent-site axisFrame.")],
    [result("C267","test_six_signed_basis_axes_and_reversal",label=["paired basis [-1, 0, 0]","paired basis [1, 0, 0]","paired basis [0, -1, 0]","paired basis [0, 1, 0]","paired basis [0, 0, -1]","paired basis [0, 0, 1]"])],
    "Separate source expression and artifact axis tuple; exact field equality against independently generated basis vectors.")
sub(g,"Source-only and artifact-only sign reversals refuse rather than canonicalize sign.",
    [S267("test_six_signed_basis_axes_and_reversal","Changing source or artifact (0,0,1) to (0,0,-1) separately requires FIELD_MISMATCH.")],
    [result("C267","test_six_signed_basis_axes_and_reversal",label=["source-only axis sign","artifact-only axis sign"])],
    "Independent order/sign expectations; comparator source inspection confirms exact equality and no motion input.")

g = group(9,"Zero/nonunit/nonbasis source axes, including a language-valid nonbasis unit vector, refuse with invalid versus unsupported distinctions.",
    ["source profile is narrower than language", "invalid norm and unsupported valid form have different categories"],
    "Both source and comparison suites explicitly distinguish MALFORMED zero/nonunit axes from UNSUPPORTED_SOURCE_FORM for (0.6,0.8,0); near-unit nonbasis and wrong shape/type/unit forms are also retained.")
for text, labels in (("Zero and nonunit axes refuse as MALFORMED.",["source axis vec3(0, 0, 0)","source axis vec3(0, 0, 2)"]),
                    ("A valid language nonbasis unit vector refuses as UNSUPPORTED_SOURCE_FORM.",["source axis vec3(0.6, 0.8, 0)"])):
    sub(g,text,[S265("test_h09_nonbasis_and_invalid_axes_refuse","Explicit per-input refusal category separates invalid zero/nonunit from valid unsupported nonbasis vectors."),S267("test_unsupported_and_invalid_source_axes","The same category distinction propagates through comparison.")],
        [result("C265","test_h09_nonbasis_and_invalid_axes_refuse"),result("C267","test_unsupported_and_invalid_source_axes",label=labels)],
        "Independent vectors: zero, norm-two and the 3/5–4/5 unit direction. Adopted norm-domain rule distinguishes language validity from the finite basis subset.")
sub(g,"Near-unit nonbasis, wrong arity/type and unit-bearing source axes refuse without normalization or baseline substitution.",
    [S265("test_h09_nonbasis_and_invalid_axes_refuse","Tests tiny second component near the z axis, two components, boolean component, and Length unit; the finite source observer rejects each.")],
    [result("C265","test_h09_nonbasis_and_invalid_axes_refuse")],
    "Actual source byte mutations; expected refusal category is exact where the contract distinguishes it, with generic typed refusal used for malformed shapes.")

g = group(10,"Artifact wrong axis length/type, boolean, nonfinite values, tiny replacement of zero or opposite sign refuses without normalization, tolerance or repair.",
    ["raw invalid structure refuses", "a valid opposite basis remains a raw claim but comparison refuses its mismatch"],
    "Independent raw and comparison cases cover each specified malformed-axis form. Opposite sign is correctly observable in raw form and rejected only on disagreement with the source.")
sub(g,"Wrong axis length and whole-value type refuse.",
    [raw_source(192,193,"Axes with two/four components, a dictionary and null refuse."),S267("test_malformed_artifact_fields_and_strict_axis_shape","Two-component axis refuses through comparison.")],
    [result("C261",pattern=r"^axis-refusal-(\[0, 0\]|\[0, 0, 1, 0\]|\{'x': 0\}|None)$"),result("C267","test_malformed_artifact_fields_and_strict_axis_shape",label="artifact malformed axis [0, 1]")],
    "Independent JSON field replacements preserve actual invalid shapes; no array repair is applied.")
sub(g,"Boolean, string and null axis components refuse instead of participating in numeric equality.",
    [raw_source(192,193,"False, string zero and null component cases refuse."),S267("test_malformed_artifact_fields_and_strict_axis_shape","False and string-one axis components refuse through comparison.")],
    [result("C261",pattern=r"^axis-refusal-\[(False|'0'|None),"),result("C267","test_malformed_artifact_fields_and_strict_axis_shape",label=["artifact malformed axis [False, 0, 1]","artifact malformed axis [0, 0, '1']"])],
    "Explicit JSON primitive substitutions; no host truthiness or string conversion is allowed.")
sub(g,"NaN and Infinity axis components refuse as typed outcomes.",
    [S267("test_malformed_artifact_fields_and_strict_axis_shape","JSON axis mutations contain float('nan') or float('inf'); both call refuse()."),S267("refuse","A public typed refusal with no qualified records is required.")],
    [result("C267","test_malformed_artifact_fields_and_strict_axis_shape",label=["artifact malformed axis [0, 0, nan]","artifact malformed axis [0, 0, inf]"])],
    "Fixture encoder writes the actual nonfinite JSON tokens; input archive and recorded MALFORMED outcomes identify them. Negative Infinity is additionally covered as a consumed numeric field in C261.")
sub(g,"Tiny nonzero replacement of source zero refuses without a tolerance.",
    [raw_source(192,193,"math.ulp(0.0) replaces a zero axis component and raw parsing refuses."),S267("test_malformed_artifact_fields_and_strict_axis_shape","Artifact [1e-300,0,1] refuses through comparison.")],
    [result("C261",pattern=r"^axis-refusal-\[5e-324,"),result("C267","test_malformed_artifact_fields_and_strict_axis_shape",label="artifact malformed axis [1e-300, 0, 1]")],
    "Independent smallest-subnormal and 1e-300 values challenge zero equality; neither axis is normalized to the source basis.")
sub(g,"Valid opposite-sign basis claims remain visible raw but refuse source/artifact agreement.",
    [raw_source(188,191,"Negative basis vectors are exact raw claims, not normalized away."),S267("test_six_signed_basis_axes_and_reversal","Artifact-only opposite z sign requires FIELD_MISMATCH.")],
    [result("C261",pattern=r"^basis-\[0, 0, -1\]$"),result("C267","test_six_signed_basis_axes_and_reversal",label="artifact-only axis sign")],
    "The contract's raw claim boundary means a supported opposite sign is not intrinsically malformed; exact comparison supplies the required disagreement refusal.")

g = group(11,"Parameterized/computed source axis, limits and initial, including typed Angle parameter with baseline-equivalent default, refuse as unsupported without original-value substitution.",
    ["no expression evaluation or parameter-default substitution", "unsupported source form differs from language-invalidity judgment"],
    "The source control enumerates reference, arithmetic, call and conditional forms across the consumed fields and inserts a typed Angle parameter defaulting to the original zero. All eight cases require UNSUPPORTED_SOURCE_FORM; comparator arithmetic controls independently propagate that refusal.")
sub(g,"Parameterized/computed axis expressions refuse as unsupported.",
    [S265("test_h11_computed_numeric_fields_refuse","Axis forms include self.length component, 1+0 component and unit(vec3(...)); each requires UNSUPPORTED_SOURCE_FORM."),S267("test_computed_source_fields_do_not_use_baseline_values","Computed axis 1+0 also refuses through comparison.")],
    [result("C265","test_h11_computed_numeric_fields_refuse"),result("C267","test_computed_source_fields_do_not_use_baseline_values",label="computed source_axis")],
    "Actual unsupported expression bytes are supplied. No assertion says the Length-bearing axis is a valid full-language axis; it checks reference-form refusal under this smaller profile.")
sub(g,"Parameterized/computed limit expressions refuse as unsupported.",
    [S265("test_h11_computed_numeric_fields_refuse","Limits include self.bounds and upper bound 45deg+0rad; both require UNSUPPORTED_SOURCE_FORM."),S267("test_computed_source_fields_do_not_use_baseline_values","Computed upper limit also refuses in comparison.")],
    [result("C265","test_h11_computed_numeric_fields_refuse"),result("C267","test_computed_source_fields_do_not_use_baseline_values",label="computed source_limits")],
    "Actual reference/arithmetic syntax is rejected without attempting name/type evaluation. The control does not claim that the undeclared self.bounds fixture is a complete valid OntoKin source.")
sub(g,"Computed initial and a typed Angle parameter with baseline-equivalent zero default refuse as unsupported.",
    [S265("test_h11_computed_numeric_fields_refuse","Inserts public param start_angle: Angle = 0[rad], then checks self.start_angle, 0rad+0rad and a conditional; no case may substitute the default."),S267("test_computed_source_fields_do_not_use_baseline_values","Computed zero initial refuses through comparison.")],
    [result("C265","test_h11_computed_numeric_fields_refuse"),result("C267","test_computed_source_fields_do_not_use_baseline_values",label="computed source_initial")],
    "The actual typed parameter declaration and reference are inserted into supplied source. Its numerical default equals the original initial, so refusal specifically prevents baseline-value fallback.")

g = group(12,"Paired lexical joint rename retaining key, then joint-key change retaining name: path and definition/occurrence IDs follow separate actual tokens.",
    ["lexical name controls path", "stable key controls occurrence/definition IDs", "source/object bindings remain exact"],
    "Source controls separate names from keys. Paired comparison fixtures change actual source and artifact fields, assert all IDs/paths, and reject stale artifact name/key claims.")
sub(g,"Lexical rename with stable key changes path/name and preserves IDs in source and paired comparison.",
    [S265("test_h12_joint_name_and_key_are_separate","Renames flex to rotate with key flex; baseline IDs persist and paths end .rotate."),S267("test_joint_name_and_key_have_separate_authority","Paired rotation name keeps flex IDs; accept() checks both definition and occurrence identity.")],
    [result("C265","test_h12_joint_name_and_key_are_separate"),result("C267","test_joint_name_and_key_have_separate_authority",label="joint lexical rename retains key")],
    "Actual declaration token changes; independent expected_joints() separately takes joint_name and joint_key.")
sub(g,"Key change with stable name changes definition/occurrence IDs and preserves lexical path.",
    [S265("test_h12_joint_name_and_key_are_separate","Key hinge.v2_- appears in both identity namespaces while path remains .flex."),S267("test_joint_name_and_key_have_separate_authority","Paired key rotation.key-2 keeps name flex; accept() checks all independent fields.")],
    [result("C265","test_h12_joint_name_and_key_are_separate"),result("C267","test_joint_name_and_key_have_separate_authority",label="joint key change retains name")],
    "Opaque key strings remain distinct from names; actual source and row IDs change, not merely the expected-answer table.")
sub(g,"Source changes with stale artifact path or ID refuse.",
    [S267("test_joint_name_and_key_have_separate_authority","Restores old artifact path after source rename, or old element_id tail after source rekey; both require FIELD_MISMATCH.")],
    [result("C267","test_joint_name_and_key_have_separate_authority",label=["source joint change with stale artifact path","source joint change with stale artifact element_id"])],
    "Exact stale artifact claims are deliberately reintroduced after paired fixture generation; new source/program/object bindings are retained.")

g = group(13,"Source-only and paired endpoint-site name/key changes maintain correct site-definition and endpoint association without suffix/name guessing.",
    ["site name controls path", "site key controls source identity", "artifact contains endpoint paths but no direct site key/definition/span", "whole owning object association"],
    "Actual source site/part renames and keys are asserted independently. Paired name changes pass, stale parent/child paths refuse, and source-only key changes correctly update derived IDs without inventing direct artifact fields.")
sub(g,"Source-only site/part name and key changes update ordered endpoint IDs, whole paths and site definitions.",
    [S265("test_h13_endpoint_names_keys_and_part_names_are_independent","Changes pivot->anchor/pivot.key, base->foot/foot-key and blade->lever/blade.key; asserts independent endpoint paths/IDs and child definition key.")],
    [result("C265","test_h13_endpoint_names_keys_and_part_names_are_independent")],
    "Independent byte replacements separately address lexical tokens and quoted keys. Expected endpoint identities append actual keys to their correct object/class namespaces.")
sub(g,"Paired endpoint lexical names pass; separately stale parent and child paths after source renaming refuse.",
    [S267("test_site_names_and_derived_keys_remain_distinct","Paired socket/anchor names pass; restoring old pivot or base suffix independently requires FIELD_MISMATCH."),S267("accept","Every endpoint source ID/definition/path/name/key and bound object association is compared to independently authored expectations.")],
    [result("C267","test_site_names_and_derived_keys_remain_distinct",label=["paired endpoint lexical names","stale endpoint path after source rename parent_site","stale endpoint path after source rename child_site"])],
    "Source expressions and actual artifact path claims both change in the positive case. In negative cases only the selected artifact endpoint remains stale after correct provenance rebinding.")
sub(g,"Site-key-only changes retain artifact path claims and expose new source-derived site IDs/definitions.",
    [S267("test_site_names_and_derived_keys_remain_distinct","Changes parent/child keys to pivot.key-2/base.key-2; full accept() checks both endpoint identity namespaces and unchanged paths."),S267("accept","Asserts no artifactDefinitionId or artifactSpan on derived endpoint associations.")],
    [result("C267","test_site_names_and_derived_keys_remain_distinct",label="site-key change has source-only identity authority")],
    "The artifact has no site-key field to mutate. A correctly rebound key-only source change is therefore an agreement case with new derived identities, not a fabricated artifact key disagreement.")
sub(g,"Stale lexical endpoint and suffix-only/another-object path cannot be guessed into an association.",
    [S265("test_h13_missing_endpoint_name_cannot_guess_from_key","Renames the source site but retains the old endpoint expression and requires refusal."),S267("test_ordered_endpoint_swap_wrong_object_and_same_object","Terminal-only pivot and a different object's pivot both require FIELD_MISMATCH.")],
    [result("C265","test_h13_missing_endpoint_name_cannot_guess_from_key"),result("C267","test_ordered_endpoint_swap_wrong_object_and_same_object",label=["artifact endpoint wrong_object","artifact endpoint suffix_only"])],
    "Stable key or common terminal name cannot replace actual lexical resolution and full object path association.")

g = group(14,"Ordered endpoint swap, same-object endpoints or another object's site: retain order, enforce distinct objects and refuse mismatches.",
    ["parent and child remain ordered", "source endpoints belong to distinct occurrences", "full path and source object association"],
    "Raw/source swap controls retain order, a deliberate paired reversal agrees, artifact-only/same/wrong-object/suffix paths refuse, and either source endpoint replacement onto the other object refuses.")
sub(g,"Raw and source endpoint swaps preserve the authored parent/child order.",
    [raw_source(199,199,"Raw swapped claims are independently decoded and compared unchanged by audit()."),S265("test_h14_endpoint_order_is_preserved","Source swap yields parent blade/base and child pivot IDs without sorting; numeric fields stay as authored.")],
    [result("C261",pattern=r"^ordered-endpoint-swap$"),result("C265","test_h14_endpoint_order_is_preserved")],
    "The two endpoint fields are exchanged in actual copied source or artifact input, with explicitly ordered expected IDs.")
sub(g,"Supported paired endpoint reversal compares successfully.",
    [S267("test_ordered_endpoint_swap_wrong_object_and_same_object","Accepts a source+artifact swapped recipe; accept() checks exact ordered associations."),source("F267","synthetic","Rewrites both actual source endpoint expressions and writes artifact paths from the independently swapped recipe.")],
    [result("C267","test_ordered_endpoint_swap_wrong_object_and_same_object",label="supported paired endpoint reversal")],
    "Independent expected_joints(swapped=True) places the part site first and own site second; no numeric motion fitting is involved.")
sub(g,"Artifact-only swap, same path, another object's path and suffix-only paths refuse.",
    [S267("test_ordered_endpoint_swap_wrong_object_and_same_object","Each of swap, same, wrong_object and suffix_only is an independent artifact mutation requiring FIELD_MISMATCH.")],
    [result("C267","test_ordered_endpoint_swap_wrong_object_and_same_object",label=["artifact endpoint swap","artifact endpoint same","artifact endpoint wrong_object","artifact endpoint suffix_only"])],
    "Exact full-path expectations are derived from source occurrences; the wrong-object control reuses another row's valid terminal site so suffix matching cannot pass.")
sub(g,"Source same-object endpoint declarations refuse instead of producing a qualified hinge.",
    [S265("test_h14_same_object_endpoints_refuse","Tests child=self.pivot and parent=self.blade.base independently; both require MALFORMED."),S267("test_ordered_endpoint_swap_wrong_object_and_same_object","Source child=self.pivot also requires MALFORMED through comparison.")],
    [result("C265","test_h14_same_object_endpoints_refuse"),result("C267","test_ordered_endpoint_swap_wrong_object_and_same_object",label="source same-object endpoints")],
    "The positive source profile requires two distinct occurrence IDs even when the endpoint fields are individually resolvable declared sites.")

assert [row["id"] for row in GROUPS] == [f"H{i:02}" for i in range(1,15)]
for row in GROUPS:
    assert row["required_subcases"] and all(s["source_assertions"] and s["execution_results"] for s in row["required_subcases"])

payload = {
    "schema": "ontokin.c269.independent-hinge-coverage-map/0.1", "worker": "/root/audit_h01_h14",
    "audit_input_revision": BASE, "scope": "H01-H14 only", "groups": GROUPS,
    "summary": {"complete": sum(g["status"]=="complete" for g in GROUPS), "partial": 0, "absent": 0,
                "contradictory": 0, "material_subcases": sum(len(g["required_subcases"]) for g in GROUPS)},
    "status_definition": "Complete means that every material clause of this finite frozen control has identified independently authored assertions and retained successful expected outcomes on identified bytes. It does not certify all possible inputs or the whole C260 contract.",
    "identity_manifest": OWN + "INPUT-IDENTITIES.json", "execution_index": OWN + "EVIDENCE-INDEX.json",
    "new_inspection_results": OWN + "INSPECTION.json",
    "new_behavioral_executions": 0, "new_controls": 0, "unknown_operations": [],
    "qualification_boundary": [
        "Only H01-H14 were assigned to this worker. H15-H28 and contract-wide qualification belong to the Director's synthesis.",
        "C261 run-03 retains its original recorded local source revision and exact SHA bindings; the historical local Git object is unavailable, while the matching published reader is available.",
        "C265 run-06 retains detailed exact input hashes but no original Git execution revision. Its ledger is not relabeled. The later 5084dd6 clean discovery run separately passes the identical test/implementation/dependency/fixture bytes.",
        "C267/C268 selected call ledgers are from the retained 5084dd6 main-integration execution and their archived inputs were read/hash-verified, not rerun.",
        "Raw artifact values remain untrusted claims, source site records remain derived, and historical exact-byte admission does not authorize accepted revisions, physical/site/world behavior, native/model trials or comparative advantage."],
    "next_action": "Director synthesizes this map with the independently assigned H15-H28 audit, verifies the exact combined candidate, and performs the one authorized phase's review/publication/saved-handoff gates. No further behavior phase is started here.",
}
(HERE / "MAP.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(payload["summary"]))
