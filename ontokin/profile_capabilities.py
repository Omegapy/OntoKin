"""Explicit feature membership for the experimental execution-budget profile.

These sets describe source semantics. They do not register an Agent service or
infer compatibility from a numeric version.
"""

BUDGET_PROFILE = "planar-reach-budget-0.1"
EXTRUSION_PROFILE = "polygon-extrusion-0.1"
EXECUTION_PROFILES = frozenset({BUDGET_PROFILE, EXTRUSION_PROFILE})
REACH_PROFILES = frozenset({"planar-reach-0.1", *EXECUTION_PROFILES})
FORCE_PROFILES = frozenset({"force-0.1", *REACH_PROFILES})
IMPULSE_PROFILES = frozenset({"impulse-0.1", *FORCE_PROFILES})
SURFACE_PROFILES = frozenset({"surface-0.1", *IMPULSE_PROFILES})
CONSTRUCTION_PROFILES = frozenset({"construction-0.1", *SURFACE_PROFILES})

