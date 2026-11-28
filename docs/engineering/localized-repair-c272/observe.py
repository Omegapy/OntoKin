"""C272 observation of delivered bytes through the existing, unchanged observers (TASK-016).

It imports no OntoKin product module. Each reused observer is loaded from its
pinned bytes, as later components of C255 to C268 do, and is used only for what
its contract establishes:
- C256 `associate_glb`: geometry, the 126 poses, and the identity/definition join;
- C257 `compare_ownership`: owner agreement between source and GLB;
- C258 `compare_follows`: follow agreement between source and GLB;
- C267 `compare_hinges`: hinge agreement between source and GLB.

C268's historical exact-byte reader is never used for fresh output.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

ENGINEERING = Path(__file__).resolve().parents[1]
PINS = {
    "c255_oracle": ("localized-repair-c255/oracle.py", "b7275bd40bd429397ce6db5608bc025493a5e92cfc378f70e05cc799f50ff593"),
    "c256_reader": ("localized-repair-c256/reader.py", "5993d1a9ca1cbccd4518ed6f113238d18f6b71ba02befd59900b93fe47ef6e6a"),
    "c257_ownership": ("localized-repair-c257/ownership.py", "c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1"),
    "c258_follows": ("localized-repair-c258/follows.py", "397413d7c403693a349075711bc3dd77fab863d200b06a979cec2f0112114937"),
    "c267_hinge_compare": ("localized-repair-c267/hinge_compare.py", "9b2899d95471546a25a8a7e5ed9d9ac2a1e42854c31808d4e68aff2582686b58"),
}


class ObservationFault(Exception):
    def __init__(self, code: str, detail: str):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


def pinned(name: str):
    """Load one reused component from its exact bytes; a changed file refuses."""
    module_name = "_c272_" + name
    if module_name in sys.modules:
        return sys.modules[module_name]
    relative, expected = PINS[name]
    path = ENGINEERING / relative
    raw = path.read_bytes()
    if path.is_symlink() or hashlib.sha256(raw).hexdigest() != expected:
        raise ObservationFault("COMPONENT_PIN", relative)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _call(label: str, function, *args):
    try:
        return function(*args), None
    except Exception as error:  # Each observer raises its own typed fault class.
        return None, {"observer": label, "code": getattr(error, "code", type(error).__name__),
                      "detail": str(getattr(error, "detail", error))}


def observe_delivery(source_files: dict, glb: bytes, artifact_name: str) -> dict:
    """Observe one delivered GLB with its accepted source closure; never repairs an invalid artifact."""
    measured, fault = _call("c256.associate_glb", pinned("c256_reader").associate_glb, glb, source_files, artifact_name)
    faults = [fault] if fault else []
    result = {"artifact": {"name": artifact_name, "bytes": len(glb), "sha256": hashlib.sha256(glb).hexdigest()},
              "faults": faults, "geometry": None, "poses": None, "identities": None, "agreements": {}}
    if measured is not None:
        result.update(geometry=measured["geometry"], poses=measured["poses"], identities=measured["identityJoins"],
                      programRevision=measured["programRevision"], sourceEndpoint=measured["sourceEndpoint"])
    for label, module, function, flag in (
            ("ownership", "c257_ownership", "compare_ownership", "ownershipConsistent"),
            ("follows", "c258_follows", "compare_follows", "followConsistent"),
            ("hinges", "c267_hinge_compare", "compare_hinges",
             ("inputBindingVerified", "hingeComparisonVerified", "hingeSetAgreementVerified", "endpointAgreementVerified"))):
        flags = flag if isinstance(flag, tuple) else (flag,)
        value, fault = _call(f"{module}.{function}", getattr(pinned(module), function), source_files, glb)
        if fault:
            faults.append(fault)
            result["agreements"][label] = {"consistent": False, "fault": fault}
        else:
            agreed = all(value.get(f) is True for f in flags)
            result["agreements"][label] = {"consistent": agreed, "flags": list(flags),
                                           "records": len(value.get("records") or []),
                                           "artifactSha256": value.get("artifactSha256"),
                                           "limits": value.get("limits")}
            if not agreed:
                faults.append({"observer": f"{module}.{function}", "code": "DISAGREEMENT", "detail": ", ".join(flags)})
    result["valid"] = not faults
    return result
