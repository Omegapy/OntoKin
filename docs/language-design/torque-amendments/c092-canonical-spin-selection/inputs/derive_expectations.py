"""Independently freeze C092 point-selector examples from the preserved kernel.

This is specification evidence, not a producer/reader implementation. It uses
the exact C091 independently authored guarded arithmetic. No runtime evaluator,
producer pose helper, plans, output artifacts, or candidate implementation is
imported. Invocation: python3 -B derive_expectations.py REPO ABSENT_OUTPUT_JSON
"""
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
import importlib.util
import json
import platform
import sys

BASE = Path(__file__).resolve().parent
REPO = Path(sys.argv[1]).resolve()
OUTPUT = Path(sys.argv[2]).resolve()
if OUTPUT.exists():
    raise ValueError("Use a fresh output path; preserved results are immutable")
INPUTS = json.loads((BASE / "DERIVATION-INPUTS.json").read_text())
for relative, receipt in INPUTS["repository_inputs"].items():
    raw = (REPO / relative).read_bytes()
    if len(raw) != receipt["bytes"] or sha256(raw).hexdigest() != receipt["sha256"]:
        raise ValueError("Derivation input differs: " + relative)
raw = (BASE / "reviewed_torque_axis_exact.py").read_bytes()
if sha256(raw).hexdigest() != INPUTS["preserved_kernel"]["sha256"]:
    raise ValueError("Preserved independent kernel differs")
sys.path.insert(0, str(REPO))
from ontokin.reach_reference import _Arithmetic, ReferenceError

spec = importlib.util.spec_from_file_location(
    "ontokin.c092_preserved_exact_kernel", BASE / "reviewed_torque_axis_exact.py")
KERNEL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(KERNEL)

STAGES = (96, 192, 384, 768, 1536)
GRID = 1 << 96
RHO = F(1, 1 << 97)
GUARD = F(1, 1 << 86)
STEPS = 0


def bounded_tick():
    global STEPS
    STEPS += 1
    if STEPS > 100000:
        raise RuntimeError("Independent freeze exhausted 100000 scalar steps")


A = _Arithmetic(check=bounded_tick)


def ratio(value):
    value = F(value)
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def plan_at(omega, elapsed, precision):
    omega = tuple(F(v) for v in omega)
    A.tick(); A.guard(*omega, elapsed)
    maximum = max(map(abs, omega))
    if maximum == 0:
        raise ValueError("Stationary advance preserves its complete anchor before selection")
    scaled = tuple(A.exact(v, maximum, "div") for v in omega)
    square = A.exact_sum(*(A.exact(v, v, "mul") for v in scaled))
    norm = KERNEL.sqrt_bounds(square, precision, A)
    pi = KERNEL.pi_bounds(precision, A)
    span = A.exact(maximum, abs(elapsed), "mul")
    quotient = A.exact(A.exact(span, norm[1], "mul"), pi[0], "div")
    A.tick()
    kmax = quotient.numerator // quotient.denominator + 2
    A.guard(kmax)
    angular_width = A.exact(span, A.exact(norm[1], norm[0], "sub"), "mul")
    pi_width = A.exact(kmax, A.exact(pi[1], pi[0], "sub"), "mul")
    error = A.exact(A.exact(A.exact(angular_width, pi_width, "add"), 4, "div"), RHO, "add")
    return {"precision": precision, "omega": omega, "elapsed": F(elapsed),
            "maximum": maximum, "scaled": scaled, "norm": norm, "pi": pi,
            "kmax": kmax, "error": error}


def select(omega, elapsed):
    if not any(omega) or elapsed == 0:
        return None, [], "preserve_complete_anchor"
    tried = []
    for precision in STAGES:
        plan = plan_at(omega, elapsed, precision)
        tried.append({"precision": precision, "argument_error": ratio(plan["error"]),
                      "certifies": plan["error"] <= GUARD})
        if plan["error"] <= GUARD:
            return plan, tried, "selected"
    return None, tried, "finite_numeric_refusal"


def point(plan):
    factor = A.exact(A.exact(plan["maximum"], plan["elapsed"], "mul"), 2, "div")
    low, high = sorted(A.exact(factor, n, "mul") for n in plan["norm"])
    pair = KERNEL.reduced_sincos(low, high, plan["pi"], A)
    if pair is None:
        return None
    sine, cosine = pair
    middle = A.exact(A.exact(*plan["norm"], "add"), 2, "div")
    unit = tuple(KERNEL.nearest_grid(A.exact(v, middle, "div"), A) for v in plan["scaled"])
    return KERNEL.rotation((cosine, *(A.exact(v, sine, "mul") for v in unit)), A)


def description(plan, tried, outcome):
    return {"outcome": outcome,
            "selected_precision": None if plan is None else plan["precision"],
            "tried": tried}


rows = []
pi_proofs = []
for precision in STAGES:
    # For an exact Cartesian norm the entire selector error is K*dpi/4+rho.
    # K=floor(M*D/pi_lo)+2. This gives an exact threshold with no searching.
    pi = KERNEL.pi_bounds(precision, A)
    midpoint = A.exact(A.exact(pi[0], pi[1], "add"), 2, "div")
    assert 0 < pi[0] <= midpoint <= pi[1] < F(22, 7)
    assert F(11, 14) + RHO < 1
    pi_proofs.append({"precision": precision, "lower": ratio(pi[0]), "upper": ratio(pi[1]),
                      "positive_and_below_22_over_7": True,
                      "reduced_grid_midpoint_upper_bound": ratio(F(11, 14) + RHO),
                      "upper_bound_strictly_below_one": True})
    width = A.exact(pi[1], pi[0], "sub")
    allowance = A.exact(A.exact(4, A.exact(GUARD, RHO, "sub"), "mul"), width, "div")
    A.tick()
    largest_k = allowance.numerator // allowance.denominator
    magnitude = F(1 << 512) if precision == 1536 else F(1)
    boundary = A.exact(A.exact(largest_k - 1, pi[0], "mul"), magnitude, "div")
    step = A.exact(F(1, 1 << precision), magnitude, "div")
    omega = (magnitude, F(0), F(0))
    for position, elapsed in (("below", A.exact(boundary, step, "sub")),
                              ("at", boundary),
                              ("above", A.exact(boundary, step, "add"))):
        for sign in (1, -1):
            elapsed_signed = A.exact(sign, elapsed, "mul")
            plan, tried, outcome = select(omega, elapsed_signed)
            expected = (precision if position == "below" else
                        STAGES[STAGES.index(precision) + 1] if precision != STAGES[-1] else None)
            assert (None if plan is None else plan["precision"]) == expected
            quaternion = None if plan is None else point(plan)
            assert plan is None or quaternion is not None
            rows.append({"id": f"stage-{precision}-{position}-{'positive' if sign > 0 else 'negative'}",
                         "omega": [ratio(v) for v in omega], "elapsed": ratio(elapsed_signed),
                         "transition_precision": precision, "position": position,
                         "pi_width": ratio(width), "largest_certifying_k": str(largest_k),
                         "quaternion_grid_integers": None if quaternion is None else
                             [str(int(v * GRID)) for v in quaternion],
                         **description(plan, tried, outcome)})

omega = tuple(map(F, (0.6, 0.8, 0.0)))
witness = []
for precision in STAGES:
    plan = plan_at(omega, F(1), precision)
    q = point(plan)
    assert q is not None
    local = tuple(KERNEL.nearest_grid(-v, A) for v in omega)
    transported = KERNEL.rotated(q, local, A)
    incoming = tuple(KERNEL.nearest_grid(A.exact(v, w, "add"), A) for v, w in zip(omega, transported))
    exposed = KERNEL.exposed_vector(incoming, A)
    witness.append({"precision": precision, "certifies_at_one": plan["error"] <= GUARD,
                    "quaternion_grid_integers": [str(int(v * GRID)) for v in q],
                    "released_omega_grid_integers": [str(int(v * GRID)) for v in incoming],
                    "released_omega_binary64_hex": [float(v).hex() for v in exposed],
                    "axis_world_x_admitted": not any(exposed[1:]),
                    "argument_error_at_one": ratio(plan["error"]),
                    "certifies_at_16384": plan_at(omega, F(16384), precision)["error"] <= GUARD})
assert witness[0]["released_omega_grid_integers"] == ["0", "0", "0"]
assert all(row["released_omega_grid_integers"] == ["0", "0", "1"] for row in witness[1:])

rounding = []
for numerator, expected in ((1, 0), (3, 2), (-1, 0), (-3, -2), (5, 2), (-5, -2)):
    value = F(numerator, 2 * GRID)
    actual = KERNEL.nearest_grid(value, A)
    assert actual == F(expected, GRID)
    rounding.append({"input": ratio(value), "expected_grid_integer": str(expected)})

permutations = []
for name, q in (("identity", (F(1), F(0), F(0), F(0))),
                ("half_turn_z", (F(0), F(0), F(0), F(1))),
                ("quarter_turn_z", (F(1, 2), F(0), F(0), F(1, 2)))):
    rotated = KERNEL.rotated(q, (F(1), F(0), F(0)), A)
    permutations.append({"id": name, "q": [ratio(v) for v in q],
                         "input": [ratio(v) for v in (F(1), F(0), F(0))],
                         "rotated": [ratio(v) for v in rotated]})

lever = (F(1), F(2), F(3))
impulse = (F(2), F(4), F(6))
cross = KERNEL.cross(lever, impulse, A)
assert cross == (F(0), F(0), F(0))

stationary = []
for name, vector, elapsed in (("zero_elapsed", omega, F(0)),
                              ("zero_speed", (F(0), F(0), F(0)), F(16384))):
    plan, tried, outcome = select(vector, elapsed)
    assert plan is None and tried == [] and outcome == "preserve_complete_anchor"
    stationary.append({"id": name, "omega": [ratio(v) for v in vector],
                       "elapsed": ratio(elapsed), **description(plan, tried, outcome),
                       "requires": "retain complete anchor components, error and materialized projection; still admit current operands/context"})

# Explicitly malformed already-selected enclosures demonstrate that the later
# reducer has a finite failure result. These are helper controls, not a claim
# that the first-stage selector can reach this malformed plan.
bad_reduction = KERNEL.reduced_sincos(F(-1), F(1), KERNEL.pi_bounds(96, A), A)
assert bad_reduction is None

c3_names = ("p05-cancelling", "p06-zero", "p16-neutral-com-force",
            "p23-partial-sum-overflow-cancels", "p24-underflow-is-neutral", "p30-underflow-replacement")
c3_guard = plan_at((F(0), F(0), F(1, 2)), F(3), 96)
assert c3_guard["error"] <= GUARD
c3 = []
for index, name in enumerate(c3_names):
    relative = f"docs/language-design/torque-v0.1/freeze/sources/{name}.ok"
    raw = (REPO / relative).read_bytes()
    c3.append({"id": name, "path": relative, "sha256": sha256(raw).hexdigest(),
               "argument": "omega=(0,0,0.5), every elapsed phase/point in [0,3]; all plans first certify at96"
                   if index < 3 else "omega=0 and canonical alpha=0 throughout; complete stationary anchor preserved",
               "max_argument_error": ratio(c3_guard["error"]) if index < 3 else ratio(0),
               "frozen_physical_fields_and_error_expectations": "unchanged"})

origin_vector = (F(0), F(0), F(1, 4))
origin_full = point(plan_at(origin_vector, F(1), 96))
origin_half = point(plan_at(origin_vector, F(1, 2), 96))
incorrect_reseed = KERNEL.product(origin_half, origin_half, A)
assert incorrect_reseed != origin_full
origin_recipe = {
    "omega": [ratio(v) for v in origin_vector], "actual_source_clock": "0",
    "zero_force_activation": "0.5", "zero_force_completion": "0.75", "sample_clock": "1",
    "expected_elapsed": "1",
    "expected_quaternion_grid_integers": [str(int(v * GRID)) for v in origin_full],
    "incorrect_half_plus_half_quaternion_grid_integers": [str(int(v * GRID)) for v in incorrect_reseed],
    "incorrect_reseed_differs": incorrect_reseed != origin_full,
    "axis": "world_z", "incoming_omega_binary64_hex": ["0x0.0p+0", "0x0.0p+0", "0x1.0000000000000p-2"],
    "disposition": "accepted after; zero force changes no canonical acceleration/orientation anchor",
}

cyclic = (F(1, 2),) * 4
evolved_parent = KERNEL.product(point(plan_at((F(0), F(1), F(0)), F(1), 96)), cyclic, A)
evolved_local_rate = KERNEL.rotated(evolved_parent, (F(1, 2), F(0), F(0)), A)
evolved_omega = tuple(KERNEL.nearest_grid(A.exact(a, b, "add"), A)
                      for a, b in zip((F(0), F(1), F(0)), evolved_local_rate))
assert evolved_omega == (F(0), F(3, 2), F(0))
evolved_q = KERNEL.product(evolved_parent, KERNEL.axis_rotation((F(1), F(0), F(0)), F(1, 2), A), A)
permuted_lever = KERNEL.rotated(cyclic, (F(1), F(2), F(3)), A)
assert permuted_lever == (F(3), F(1), F(2))
permuted_cross = KERNEL.cross(permuted_lever, (F(3), F(1), F(2)), A)
assert permuted_cross == (F(0), F(0), F(0))
source_permutations = {
    "evolved-permutation.ok": {
        "parent_quaternion_grid_integers": [str(int(v * GRID)) for v in evolved_parent],
        "pre_release_quaternion_grid_integers": [str(int(v * GRID)) for v in evolved_q],
        "released_omega_binary64_hex": [float(v).hex() for v in evolved_omega],
        "axis": "world_y", "clock": "1", "disposition": "accepted after",
        "proof": "Parent q=(a,b,b,a) maps self X exactly to world Y; local hinge rate1/2 plus world-Y parent rate1 gives3/2; all intermediate orthogonal components are exactly zero"},
    "nonzero-parallel-impulse.ok": {
        "world_lever": [ratio(v) for v in permuted_lever],
        "world_impulse": [ratio(v) for v in (F(3), F(1), F(2))],
        "angular_cross": [ratio(v) for v in permuted_cross],
        "released_omega_binary64_hex": ["0x0.0p+0"] * 3,
        "axis": "world_z", "clock": "0", "applied_count": 1,
        "disposition": "accepted after",
        "proof": "Cyclic quaternion(1/2,1/2,1/2,1/2) maps(1,2,3) to(3,1,2), exactly parallel to the nonzero impulse; angular cross is exactly zero while linear impulse remains nonzero"},
}

for name in ("ontokin.reach_pose", "ontokin.reach_runtime", "ontokin.torque_runtime",
             "ontokin.reach_numeric", "ontokin.evaluator", "ontokin.torque_reference"):
    if name in sys.modules:
        raise RuntimeError("Forbidden producer or candidate import: " + name)

result = {
    "schema": "ontokin.c092-independent-selector-expectations/1",
    "status": "passed",
    "scope": "Mathematical freeze before candidate implementation; not runtime/release acceptance",
    "python": sys.version, "platform": platform.platform(),
    "source_commit": INPUTS["source_commit"],
    "derivation_script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    "independent_kernel_sha256": INPUTS["preserved_kernel"]["sha256"],
    "scalar_steps": STEPS, "scalar_step_cap": 100000, "operand_bit_cap": 32768,
    "stage_boundaries": rows,
    "all_five_pi_enclosure_range_proofs": pi_proofs,
    "witness_candidates": witness,
    "witness_under_proposed_rule": {
        "selected_precision_at_one": 96,
        "released_omega_binary64_hex": ["0x0.0p+0", "0x0.0p+0", "0x0.0p+0"],
        "after_side_admission": "accepted", "latched_axis": "world_x",
        "history_invariance": "all admitted histories choose this point's stage96; a long-prefix request may separately use stage192",
        "expected_rotation_error_terms": {
            "axis_or_spin_constructor": ratio(F(1, 1 << 74)),
            "each_rescale_or_product": ratio(F(1, 1 << 91)),
            "each_actual_public_rotation_materialization": ratio(F(1, 1 << 50)),
            "each_rounded_vector_euclidean_allowance": ratio(F(1, 1 << 96)),
            "carry_forward": "all inherited complete RotationValue, reference/error origins and ordered transfer uncertainty; exact canonical cancellation does not zero uncertainty"},
        "error_scope_limit": "Constants and preservation obligations are derived here. Full source-DAG error coefficients remain a separately required independent reader/continuous certificate gate; no final complete numerical error projection is claimed."},
    "rounding_ties": rounding, "quaternion_permutations": permutations,
    "nonzero_parallel_cross": {"lever": [ratio(v) for v in lever], "impulse": [ratio(v) for v in impulse],
                               "expected": [ratio(v) for v in cross]},
    "genuine_off_axis": [{"component": ratio(F(sign, GRID)), "binary64_hex": float(F(sign, GRID)).hex(),
                           "world_x_admitted": False} for sign in (1, -1)],
    "stationary": stationary,
    "selected_reduction_failure_control": {"lower": ratio(-1), "upper": ratio(1), "precision": 96,
                                           "reduction_result": None, "required_disposition": "terminal numeric refusal; no stage retry",
                                           "scope": "malformed-enclosure helper control, not a valid source witness"},
    "c3_literal_compatibility": c3,
    "unchanged_force_source_origin": origin_recipe,
    "source_permutations_and_parallel_impulse": source_permutations,
    "forbidden_imports_absent": True,
}
OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": result["status"], "stage_boundary_cases": len(rows),
                  "scalar_steps": STEPS, "witness_selected_precision": 96,
                  "output": str(OUTPUT)}))
