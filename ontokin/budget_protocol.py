"""Explicit Agent/0.7 requests, separate from the frozen earlier registries."""
from __future__ import annotations

import copy

from . import program_protocol as legacy
from .agent_protocol import ProtocolError, _bad, _integer, _object
from .execution_budget import DEFAULT_LIMITS, MAX_LIMIT
from .program_bindings import ProgramBinding
from .profile_capabilities import BUDGET_PROFILE

SCHEMA_VERSION = "ontokin.agent/0.7"
DEFINITION = ProgramBinding(SCHEMA_VERSION, "0.7", BUDGET_PROFILE, "ontokin.glb/0.7",
    "budget-program-agent.sqlite3", "ontokin.budget-program-agent-store/0.1", True, True)
MAX_BUDGETS = {**legacy.MAX_BUDGETS, **{key: MAX_LIMIT for key in DEFAULT_LIMITS}}
OPERATIONS = {name: (set(required), set(optional))
              for name, (required, optional) in legacy.SURFACE_OPERATIONS.items()}
OPERATIONS["artifact"][1].add("budgets")


class BudgetProtocol:
    SCHEMA_VERSION = SCHEMA_VERSION
    definition = DEFINITION
    profile = BUDGET_PROFILE
    destination = DEFINITION.destination
    MAX_BUDGETS = MAX_BUDGETS
    OPERATIONS = OPERATIONS
    canonical_request = staticmethod(legacy.canonical_request)

    @classmethod
    def validate_request(cls, request):
        if request.get("schema_version") != cls.SCHEMA_VERSION:
            _bad("This service requires explicit " + cls.SCHEMA_VERSION + ".")
        operation = request.get("operation")
        if not isinstance(operation, str) or operation not in cls.OPERATIONS:
            _bad("Unknown " + cls.SCHEMA_VERSION + " operation.", operations=sorted(cls.OPERATIONS))
        required, optional = cls.OPERATIONS[operation]
        _object(request, "request", legacy.COMMON | required | optional,
                legacy.COMMON | required)
        if "budgets" in request:
            _object(request["budgets"], "budgets", set(cls.MAX_BUDGETS))
            for name, value in request["budgets"].items():
                _integer(value, "budgets." + name, 1, cls.MAX_BUDGETS[name])
        if "destination" in request and request["destination"] != cls.definition.destination:
            _bad(cls.SCHEMA_VERSION + " requires the explicit " + cls.destination + " destination.")
        # Validate every inherited shape without registering a new legacy route.
        # Only execution caps, version selectors and the artifact cap field differ.
        projected = copy.deepcopy(request)
        projected["schema_version"] = legacy.REACH_SCHEMA_VERSION
        if "destination" in projected:
            projected["destination"] = "ontokin.glb/0.6"
        if "budgets" in projected:
            projected["budgets"] = {key: value for key, value in projected["budgets"].items()
                                    if key not in DEFAULT_LIMITS}
            if operation == "artifact":
                projected.pop("budgets")
        legacy.validate_request(projected, schema_version=legacy.REACH_SCHEMA_VERSION)
        for patch in request.get("patches", []):
            if patch["element_id"] != ["sources", patch["source_id"]]:
                _bad(cls.SCHEMA_VERSION + " patches require the exact file source scope.",
                     required_element_id=["sources", patch["source_id"]])

    @classmethod
    def envelope(cls, request, status, accepted=None):
        result = legacy.envelope(request, status, accepted,
                                 schema_version=legacy.REACH_SCHEMA_VERSION)
        result["schema_version"] = cls.SCHEMA_VERSION
        result["execution_budget"] = None
        return result


def bind():
    return BudgetProtocol()
