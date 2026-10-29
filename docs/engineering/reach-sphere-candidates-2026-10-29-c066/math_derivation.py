"""Reproduce exact conditional C066 mathematics without executing OntoKin.

Only rational inequalities, exact decimal spelling, and a subnormal rounding-cell
model are evaluated. There are no trigonometric calls or generated mesh arrays.
The symbolic identities and geometric reductions listed below are mathematical
premises of this finite calculation, not certified properties of native libm.
"""

from fractions import Fraction as Q
import hashlib
import json


def rational(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def nearest_even_integer(value):
    """Exact rounding-cell model for a nonnegative rational in subnormal units."""
    quotient, remainder = divmod(value.numerator, value.denominator)
    twice = 2 * remainder
    if twice < value.denominator:
        return quotient
    if twice > value.denominator:
        return quotient + 1
    return quotient + (quotient % 2)


def derive():
    # Prove positive nested-radical bounds using exact rational squaring
    sqrt2_low, sqrt2_high = Q("1.4142"), Q("1.4143")
    assert sqrt2_low ** 2 < 2 < sqrt2_high ** 2
    a_low, a_high = Q("0.7653"), Q("0.7654")
    assert a_low ** 2 < 2 - sqrt2_high
    assert 2 - sqrt2_low < a_high ** 2

    sin5_low, cos5_low = Q("0.8314"), Q("0.5555")
    assert (2 * sin5_low) ** 2 < 2 + a_low
    assert (2 * cos5_low) ** 2 < 2 - a_high
    cos_pi8_high, sin_pi8_high = Q("0.924"), Q("0.383")
    assert 2 + sqrt2_high < (2 * cos_pi8_high) ** 2
    assert a_high / 2 < sin_pi8_high

    candidate_low = sqrt2_low * sin5_low + cos5_low
    selected_lower = Q("1.73")
    excluded_upper = Q("1.71")
    assert candidate_low > selected_lower
    latitude4_upper = 1 + sqrt2_high / 2
    latitude6_upper = Q("1.415") * cos_pi8_high + sin_pi8_high
    assert sqrt2_high < Q("1.415")
    assert latitude4_upper < excluded_upper
    assert latitude6_upper < excluded_upper
    assert 2 + cos_pi8_high < excluded_upper ** 2

    coordinate_error = Q(1, 1000)
    actual_selected_lower = selected_lower - 3 * coordinate_error
    actual_excluded_upper = excluded_upper + 3 * coordinate_error
    assert actual_selected_lower == Q("1.727")
    assert actual_excluded_upper == Q("1.713")
    assert actual_selected_lower > actual_excluded_upper

    # Strict normal-factor intervals map to open nearest-even rounding cells
    mu = Q(1, 1 << 1074)
    radius = 2 * mu
    assert radius * Q(1, 4) == mu / 2
    assert radius * Q(3, 4) == 3 * mu / 2
    assert radius * 1 == 2 * mu
    assert nearest_even_integer(Q(1, 2)) == 0
    assert nearest_even_integer(Q(3, 2)) == 2
    assert nearest_even_integer(Q(5, 2)) == 2

    # These are explicit interval representatives, not constructor outputs
    selected_factors = (Q(3, 5), Q(3, 5), Q(3, 5))
    excluded_factors = (Q(2, 5), Q(4, 5), Q(2, 5))
    assert all(Q(1, 4) < value < Q(3, 4) for value in selected_factors)
    assert Q(1, 4) < excluded_factors[0] < Q(3, 4)
    assert Q(3, 4) < excluded_factors[1] < 1
    assert Q(1, 4) < excluded_factors[2] < Q(3, 4)
    selected_units = tuple(nearest_even_integer(2 * value) for value in selected_factors)
    excluded_units = tuple(nearest_even_integer(2 * value) for value in excluded_factors)
    assert selected_units == (1, 1, 1)
    assert excluded_units == (1, 2, 1)
    assert sum(selected_units) * mu == 3 * mu
    assert sum(excluded_units) * mu == 4 * mu
    assert 4 * mu > 3 * mu
    assert 2 * mu < Q(1, 1 << 150)

    # An exact terminating decimal exists within the inspected literal budget
    decimal_digits = str(5 ** 1073)
    decimal_spelling = "0." + decimal_digits.zfill(1073)
    assert Q(decimal_spelling) == radius
    assert 0 < radius < Q(1, 1 << 1022)
    assert len(decimal_spelling) == 1075 < 4096
    assert radius.denominator.bit_length() == 1074 < 32768

    return {
        "schema_version": "ontokin.c066-conditional-mathematics/0.1",
        "status": "passed",
        "execution_scope": "standard-library exact rational derivation only",
        "product_imports": 0,
        "product_requests": 0,
        "runtime_suites": 0,
        "native_trigonometric_evaluations": 0,
        "generated_meshes": 0,
        "symbolic_mathematical_premises": [
            "a = sqrt(2 - sqrt(2)); cos(pi/8) = sqrt(2 + sqrt(2))/2; sin(pi/8) = a/2",
            "sin(5*pi/16) = sqrt(2+a)/2; cos(5*pi/16) = sqrt(2-a)/2",
            "At diagonal longitudes the ideal L1 is sqrt(2)*sin(theta)+abs(cos(theta))",
            "Its northern maximizing latitude is atan(sqrt(2)), strictly between pi/4 and 3*pi/8",
            "Unimodality reduces excluded diagonal latitudes to 4 and 6",
            "An excluded longitude is at least pi/16 from a diagonal and gives L1 at most sqrt(2+cos(pi/8))",
        ],
        "ideal_lattice_rational_bounds": {
            "selected_strict_lower": rational(selected_lower),
            "selected_derived_lower": rational(candidate_low),
            "excluded_strict_upper": rational(excluded_upper),
            "latitude4_derived_upper": rational(latitude4_upper),
            "latitude6_derived_upper": rational(latitude6_upper),
            "all_bounds_scale_by_positive_radius": True,
        },
        "conditional_actual_coordinate_theorem": {
            "unverified_native_premise": "Each actual coordinate differs from its ideal coordinate by at most radius/1000",
            "selected_strict_lower_times_radius": rational(actual_selected_lower),
            "excluded_strict_upper_times_radius": rational(actual_excluded_upper),
            "strict_gap_times_radius": rational(actual_selected_lower - actual_excluded_upper),
            "selected_indices": [133, 141, 149, 157, 325, 333, 341, 349],
            "native_constructor_premise_established": False,
        },
        "conditional_subnormal_witness": {
            "radius": "2^-1073",
            "mu": "2^-1074",
            "unverified_native_premise": "All eight shortlisted normal magnitudes lie strictly between 1/4 and 3/4; index69 x/z do likewise and its y magnitude lies strictly between 3/4 and 1",
            "shortlist_l1_in_mu_units": 3,
            "excluded_index": 69,
            "excluded_l1_in_mu_units": 4,
            "native_normal_factor_membership_observed": False,
            "complete_native_mesh_maximum_claimed": False,
            "stored_binary32_components_round_to_zero_in_model": True,
            "exact_decimal_characters": len(decimal_spelling),
            "exact_decimal_sha256": hashlib.sha256(decimal_spelling.encode("ascii")).hexdigest(),
            "exact_decimal_equals_radius": True,
            "source_parser_or_export_executed": False,
        },
        "limitations": [
            "The exact radical identities and monotonicity reductions are stated mathematical premises, not native libm measurements",
            "No native angle/trigonometric/coordinate enclosure is certified",
            "No complete source program, export, supplied-byte request or benchmark was executed",
            "No authority, first-exception, complete-request-cost or runtime-saving premise is established",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(derive(), indent=2, sort_keys=True))
