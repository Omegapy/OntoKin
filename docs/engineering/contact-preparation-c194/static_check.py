#!/usr/bin/env python3
"""Validate frozen preparation without constructing, simulating or rendering."""
import ast
import copy
import json
import sys
from common import CASES, C193, HERE, REPO, artifact_reader, require, verify_inputs

sys.path.insert(0, str(REPO))
from prototypes.guided_contact_v02.common import Budget, load_contract
from prototypes.guided_contact_v02.source import Source


def parse_only(path):
    context = Source(path, path.read_bytes(), Budget(1000000, 80000), load_contract())
    context.parse()
    context.validate()
    return context.canonical

inputs = verify_inputs()
historical = json.loads((C193 / "independent/frozen/expectations.json").read_text())
current = json.loads((HERE / "frozen/expectations.json").read_text())
for key in ("unchanged_limits", "unchanged_recording", "unchanged_twenty_unrelated_pairs",
            "mapping_invariants", "runtime"):
    require(current[key] == historical[key], "An inherited numerical or mapping rule changed: " + key)
starter_ok = (HERE / "starters/gauge.ok").read_bytes()
starter_py = (HERE / "starters/gauge.py").read_bytes()
starter_assignment, = [n for n in ast.parse(starter_py).body if isinstance(n, ast.Assign)]
require(parse_only(HERE / "starters/gauge.ok") == ast.literal_eval(starter_assignment.value),
        "380 mm source starters are not canonically equal")
reader = artifact_reader()
preservation = reader.verify_frozen()
backend = json.loads((REPO / "docs/language-design/guided-contact-v0.2/backend.json").read_text())
for case, target in (("G", 365), ("H", 375)):
    ok = (HERE / ("sources/" + case + ".ok")).read_bytes()
    python = (HERE / ("sources/" + case + ".py")).read_bytes()
    require(starter_ok.count(b"at = [380, 130, -220][mm];") == 1, "Ambiguous .ok starter coordinate")
    require(ok == starter_ok.replace(b"at = [380, 130, -220][mm];", ("at = [" + str(target) + ", 130, -220][mm];").encode()),
            "The .ok edit changed more than the left-stop coordinate")
    require(starter_py.count(b"'at_mm': [380, 130, -220]") == 1, "Ambiguous Python starter coordinate")
    require(python == starter_py.replace(b"'at_mm': [380, 130, -220]", ("'at_mm': [" + str(target) + ", 130, -220]").encode()),
            "The Python edit changed more than the left-stop coordinate")
    tree = ast.parse(python)
    assign, = [n for n in tree.body if isinstance(n, ast.Assign)]
    require(len(tree.body) == 2 and isinstance(tree.body[0], ast.Expr) and ast.literal_eval(tree.body[0].value),
            "Python source must contain only its docstring and literal DESIGN")
    require(len(assign.targets) == 1 and isinstance(assign.targets[0], ast.Name) and assign.targets[0].id == "DESIGN",
            "Python assignment target differs")
    design = ast.literal_eval(assign.value)
    canonical = json.loads((HERE / ("frozen/" + case + "-canonical.json")).read_text())
    require(design == canonical, "Python literal differs from frozen canonical case")
    require(parse_only(HERE / ("sources/" + case + ".ok")) == canonical,
            "Parsed .ok differs from Python and frozen canonical case")
    from common import BACKEND_SHA, SOURCE_BINDING
    reader.check_source(canonical, CASES[case], backend, BACKEND_SHA, SOURCE_BINDING)
    require((target - 180) / 125 == CASES[case]["ideal_first_contact_s"], "Contact-time derivation differs")
    require(target - 180 == CASES[case]["left_final_travel_mm"], "Travel derivation differs")
print(json.dumps({"passed": True, "native_builds": 0, "native_resimulations": 0,
                  "source_cases": ["G", "H"], "inputs": inputs, "preservation": preservation}, indent=2))

