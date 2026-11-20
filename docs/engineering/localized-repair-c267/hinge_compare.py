#!/usr/bin/env python3
"""Compare finite source and artifact hinge declarations without execution."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import types


SCHEMA = "ontokin.c267.hinge-comparison/0.1"
CONTRACT = "ontokin.c260.hinge-declarations/0.1"
MAX_SOURCE_BYTES = 65536
MAX_GLB_BYTES = 4 * 1024 * 1024
DEPENDENCIES = {
    "binding": ("localized-repair-c266/hinge_binding.py", 17639,
                "8f6b26f0bedad335b069975d0491e5565a25f0793b3bc48802e90d3993aa0d0a"),
    "source": ("localized-repair-c265/source_hinges.py", 38229,
               "70d5e5b6247347bf44eaa3be0bc9c91b13f10d4717b4b32261eaebad75987132"),
    "artifact": ("localized-repair-c261/hinge_glb.py", 14036,
                 "6167b3a56a2b1a600812340d85ee02eaa3b6399801d585a758333aabcfaa5e08"),
    "identity": ("localized-repair-c257/ownership.py", 35942,
                 "c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1"),
}
UNOBSERVED = [
    "/extras/ontokin/source fields other than entry_source_id and entry_revision",
    "/extras/ontokin/module and /extras/ontokin/scene",
    "/extras/ontokin/program/collections and other fields omitted by C261",
    "Node display names, transforms, geometry and metadata outside the retained mapping",
    "Site definitions, poses, interface and size as direct artifact measurements",
    "Joint definitions, source spans and coordinate evolution as direct artifact measurements",
    "Ownership/follow/motion validity beyond source occurrence provenance",
]
LIMITS = [
    "Agreement covers only C260 finite hinge fields, complete joint sets and ordered endpoint associations",
    "Source-derived definitions and site records are associations, not direct artifact observations",
    "Site pose expressions remain source byte witnesses; no pose or world-alignment evaluation",
    "No historical byte admission, accepted revision, edit atomicity or clean rebuild",
    "No complete source/glTF/C255 validity, physical validity, native execution, model trial or comparative benefit",
    "The exact C265 source, C261 artifact and C266 input-binding profiles remain unchanged",
    "Bare-CR line-comment termination remains an unsupported source form",
]


class Fault(ValueError):
    """Whole-comparison refusal retaining bounded available input identities."""

    def __init__(self, code, detail, pointer="", origin=None):
        self.code, self.detail = code, detail
        self.pointer, self.origin = pointer, origin
        self.sourceHashes, self.sourceBytes = {}, {}
        self.artifactSha256, self.artifactBytes = None, None
        super().__init__(f"{code}: {pointer}: {detail}")


def _require(condition, detail, pointer="", code="INPUT_BINDING", origin=None):
    if not condition:
        raise Fault(code, detail, pointer, origin)


def _dependencies():
    """Validate pinned bytes on every call, then load only captured modules."""
    root = Path(__file__).absolute().parent.parent
    captured = {}
    for name, (relative, size, digest) in DEPENDENCIES.items():
        path = root / relative
        for component in (path, *path.parents):
            _require(not component.is_symlink(), "symlink in pinned dependency path")
        _require(path.is_file(), "missing pinned dependency: " + relative)
        _require(path.stat().st_size == size, "pinned dependency size: " + relative)
        with path.open("rb") as handle:
            raw = handle.read(size + 1)
        _require(len(raw) == size and hashlib.sha256(raw).hexdigest() == digest,
                 "pinned dependency bytes: " + relative)
        captured[name] = path, raw
    modules = {}
    for name in ("binding", "source", "artifact"):
        path, raw = captured[name]
        module = types.ModuleType("_c267_pinned_" + name)
        module.__file__ = str(path)
        sys.modules[module.__name__] = module
        exec(compile(raw, str(path), "exec"), module.__dict__)
        modules[name] = module
    return modules


def _invoke(module, function, *args):
    try:
        return getattr(module, function)(*args)
    except module.Fault as exc:
        code = "UNSUPPORTED_ARTIFACT_FORM" if exc.code == "UNSUPPORTED" else exc.code
        raise Fault(code, exc.detail, getattr(exc, "pointer", ""),
                    getattr(exc, "origin", None)) from exc


def _equal(actual, expected, pointer, origin=None):
    # The pinned raw reader has already refused booleans and nonfinite numbers
    # Exact numeric equality preserves signed axes and treats signed zeros equally
    _require(actual == expected, "artifact hinge field differs from source", pointer,
             "FIELD_MISMATCH", origin)


def _endpoint(site, path, pointer, objects, sites):
    """Associate the whole path and source site identity without splitting text."""
    sid, oid = tuple(site["id"]), tuple(site["objectId"])
    _require(sid in sites and sites[sid] == site,
             "endpoint is absent from the complete source site map", pointer)
    _require(oid in objects, "endpoint owning object is not bound", pointer)
    owner = objects[oid]
    _require(site["objectDefinitionId"] == owner["definitionId"]
             and site["id"] == owner["id"] + [site["key"]]
             and site["definitionId"] == owner["definitionId"] + [site["key"]]
             and site["path"] == owner["path"] + "." + site["name"],
             "source site and bound object associations differ", pointer)
    _equal(path, site["path"], pointer, site["sourceOrigins"]["declaration"])
    return {"source": site, "artifactPath": path, "artifactOrigin": pointer,
            "objectBinding": owner}


def _compare(files, raw):
    modules = _dependencies()
    binding = _invoke(modules["binding"], "bind_hinge_inputs", files, raw)
    source = _invoke(modules["source"], "observe_source_hinges", files)
    artifact = _invoke(modules["artifact"], "observe_glb_hinges", raw)
    for key in ("sourceHashes", "sourceBytes", "sourceManifest", "programRevision"):
        _require(binding[key] == source[key], "input binding and source observation differ: " + key)
    for key in ("artifactSha256", "artifactBytes"):
        _require(binding[key] == artifact[key], "input binding and artifact observation differ: " + key)

    objects = {tuple(row["id"]): row for row in binding["records"]}
    source_objects = {tuple(row["id"]): row for row in source["objects"]}
    _require(set(objects) == set(source_objects)
             and len(objects) == len(binding["records"])
             and len(source_objects) == len(source["objects"]),
             "complete source and bound object sets differ")
    for oid, row in source_objects.items():
        _require(objects[oid]["path"] == row["path"]
                 and objects[oid]["definitionId"] == row["definitionId"],
                 "source and bound object identity/path/class differ")

    sites = {tuple(row["id"]): row for row in source["sites"]}
    site_paths = {row["path"] for row in source["sites"]}
    _require(len(sites) == len(source["sites"]) == len(site_paths),
             "source site identities and paths must be unique")
    expected = {tuple(row["id"]): row for row in source["records"]}
    actual = {tuple(row["claims"]["element_id"]): row for row in artifact["records"]}
    _require(len(expected) == len(source["records"])
             and len(actual) == len(artifact["records"]), "joint identities must be unique")
    _require(set(expected) == set(actual), "complete source and artifact joint identity sets differ",
             "/extras/ontokin/joints", "FIELD_MISMATCH")
    _require({row["path"] for row in source["records"]}
             == {row["claims"]["path"] for row in artifact["records"]},
             "complete source and artifact joint path sets differ", "/extras/ontokin/joints", "FIELD_MISMATCH")

    records = []
    for jid, joint in expected.items():
        row = actual[jid]
        claims, origins = row["claims"], row["origins"]
        oid = tuple(joint["ownerId"])
        _require(oid in objects, "joint owning object is not bound", origins["element_id"])
        owner = objects[oid]
        _require(joint["ownerDefinitionId"] == owner["definitionId"]
                 and joint["id"] == owner["id"] + [joint["key"]]
                 and joint["definitionId"] == owner["definitionId"] + [joint["key"]]
                 and joint["path"] == owner["path"] + "." + joint["name"],
                 "source joint and bound owning object associations differ", origins["element_id"])
        declaration = joint["sourceOrigins"]["declaration"]
        for key, value in (("element_id", joint["id"]), ("path", joint["path"]),
                           ("kind", joint["kind"])):
            _equal(claims[key], value, origins[key], declaration)
        for key in ("axis", "limits", "initial"):
            _equal(claims[key], joint[key], origins[key],
                   joint["sourceOrigins"]["fields"][key]["expression"])
        endpoints = {}
        for role, source_key, artifact_key in (("parent", "parentSite", "parent_site"),
                                               ("child", "childSite", "child_site")):
            site = joint[source_key]
            _require(joint[source_key + "Id"] == site["id"], "ordered source site identity differs")
            endpoints[role] = _endpoint(site, claims[artifact_key], origins[artifact_key], objects, sites)
        _require(endpoints["parent"]["source"]["objectId"] != endpoints["child"]["source"]["objectId"],
                 "ordered endpoints must belong to distinct source objects")
        records.append({"id": joint["id"], "path": joint["path"], "definitionId": joint["definitionId"],
                        "source": joint, "artifact": {"claims": claims, "origins": origins},
                        "ownerBinding": owner, "endpoints": endpoints})

    return {"schema": SCHEMA, "contract": CONTRACT, "kind": "source-artifact-hinge-comparison",
            "comparisonScope": "C260 finite declaration fields, complete joint set and ordered site associations",
            "sourceHashes": dict(source["sourceHashes"]), "sourceBytes": dict(source["sourceBytes"]),
            "sourceManifest": source["sourceManifest"], "programRevision": source["programRevision"],
            "artifactSha256": artifact["artifactSha256"], "artifactBytes": artifact["artifactBytes"],
            "sourceAuthorityOrigins": binding["sourceAuthorityOrigins"],
            "records": records, "sites": source["sites"], "objects": binding["records"],
            "hingeCount": len(records), "siteCount": len(sites), "objectCount": len(objects),
            "inputBindingVerified": True, "hingeComparisonVerified": True,
            "hingeSetAgreementVerified": True, "endpointAgreementVerified": True,
            "historicalInputsBound": False, "sitePosesEvaluated": False,
            "sourceValidityQualified": False, "acceptedRevisionQualified": False,
            "completeC255Semantic": False, "executionAllowed": False, "realTrialSuccess": None,
            "directSiteTableObserved": False, "jointDefinitionOrSpanObserved": False,
            "unobservedFields": UNOBSERVED.copy(), "limits": LIMITS.copy()}


def compare_hinges(source_files, raw):
    """Compare supplied source/GLB bytes or raise Fault without a qualified set."""
    hashes, sizes = {}, {}
    if type(source_files) is dict:
        for name in ("main.ok", "hinges.ok"):
            value = source_files.get(name)
            if type(value) is bytes:
                sizes[name] = len(value)
                if len(value) <= MAX_SOURCE_BYTES:
                    hashes[name] = hashlib.sha256(value).hexdigest()
    artifact_size = len(raw) if type(raw) is bytes else None
    artifact_hash = hashlib.sha256(raw).hexdigest() if type(raw) is bytes and len(raw) <= MAX_GLB_BYTES else None
    try:
        return _compare(source_files, raw)
    except Fault as exc:
        fault = exc
    except OSError as exc:
        fault = Fault("IO_ERROR", type(exc).__name__)
    except (UnicodeError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            ArithmeticError, RecursionError) as exc:
        fault = Fault("MALFORMED", type(exc).__name__)
    fault.sourceHashes, fault.sourceBytes = hashes, sizes
    fault.artifactSha256, fault.artifactBytes = artifact_hash, artifact_size
    raise fault
