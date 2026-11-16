"""CPU-only, fail-closed origin checks for the pinned C217 importer inventory.

Snapshot first and persist its JSON before calling classify_modules. Snapshots
retain missing, null, malformed and unreadable fields rather than substituting
guessed paths. This validates observed metadata, not a hostile Python host.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys


PREFIX = "io_scene_gltf2"
SOURCE_LOADER = "_frozen_importlib_external.SourceFileLoader"
NAMESPACE_LOADER = "_frozen_importlib_external.NamespaceLoader"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def _class_name(value):
    return None if value is None else type(value).__module__ + "." + type(value).__name__


def _field(owner, name, *, locations=False, loader=False):
    try:
        value = getattr(owner, name)
    except AttributeError:
        return {"available": False, "reason": "attribute-unavailable"}
    except BaseException as exc:
        return {"available": False, "reason": "attribute-read-error", "errorType": _class_name(exc)}
    try:
        if loader:
            value = _class_name(value)
        elif locations and value is not None:
            value = list(value)
        values = value if isinstance(value, list) else [value]
        if not all(item is None or type(item) in (str, bool, int) for item in values):
            return {"available": True, "unsupportedType": _class_name(value)}
        return {"available": True, "value": value}
    except BaseException as exc:
        return {"available": False, "reason": "attribute-conversion-error", "errorType": _class_name(exc)}


def snapshot_modules(modules):
    """Read raw attributes for every selected module without validating origins."""
    rows = []
    for name, module in sorted(list(modules.items())):
        if name != PREFIX and not name.startswith(PREFIX + "."):
            continue
        try:
            spec = getattr(module, "__spec__", None)
            identical = getattr(module, "__loader__", None) is getattr(spec, "loader", None)
        except BaseException:
            spec, identical = None, False
        rows.append({
            "module": name,
            "moduleName": _field(module, "__name__"),
            "file": _field(module, "__file__"),
            "cached": _field(module, "__cached__"),
            "moduleSearchLocations": _field(module, "__path__", locations=True),
            "moduleLoaderClass": _field(module, "__loader__", loader=True),
            "specName": _field(spec, "name"),
            "specOrigin": _field(spec, "origin"),
            "specCached": _field(spec, "cached"),
            "specHasLocation": _field(spec, "has_location"),
            "specSearchLocations": _field(spec, "submodule_search_locations", locations=True),
            "specLoaderClass": _field(spec, "loader", loader=True),
            "loaderObjectsIdentical": identical,
        })
    return rows


def _value(row, field):
    item = row[field]
    require(item.get("available") is True and "value" in item, "Unavailable or malformed " + field + ": " + row["module"])
    return item["value"]


def _absent_or_null(row, field):
    item = row[field]
    return item == {"available": False, "reason": "attribute-unavailable"} or (item.get("available") is True and "value" in item and item["value"] is None)


def _canonical_path(value, label):
    require(type(value) is str and value, "Invalid " + label)
    path = Path(value)
    require(path.is_absolute() and str(path) == str(path.resolve()), "Noncanonical or escaped " + label + ": " + value)
    return path


def inventory(build):
    """Derive exact module/package names from pinned relative source filenames."""
    root = _canonical_path(build["importer_root"], "importer root")
    require(root.name == PREFIX and root.is_dir(), "Unexpected importer root")
    concrete, packages, directories = {}, set(), {root}
    for item in build["importer_python_files"]:
        path = _canonical_path(item["path"], "pinned source path")
        require(path.is_relative_to(root) and path.suffix == ".py", "Pinned source outside importer tree")
        relative = path.relative_to(root)
        parts = list(relative.with_suffix("").parts)
        is_package = parts[-1] == "__init__"
        if is_package:
            parts.pop()
        require(all(part.isidentifier() for part in parts), "Unsupported pinned module name")
        name = ".".join([PREFIX, *parts])
        require(name not in concrete, "Conflicting pinned module name: " + name)
        concrete[name] = (path, item)
        if is_package:
            packages.add(name)
        parent = path.parent
        while parent.is_relative_to(root):
            directories.add(parent)
            if parent == root:
                break
            parent = parent.parent
    require(PREFIX in packages, "Pinned root package is missing")
    namespaces = {}
    for directory in sorted(directories):
        name = ".".join([PREFIX, *directory.relative_to(root).parts])
        if name in packages:
            continue
        require(name not in concrete, "Pinned module/directory conflict: " + name)
        require(directory.is_dir() and not (directory / "__init__.py").exists(), "Unpinned concrete initializer at namespace: " + name)
        namespaces[name] = directory
    return root, concrete, packages, namespaces


def _expected_caches(source, prefixes):
    tag = sys.implementation.cache_tag
    require(type(tag) is str and tag, "Interpreter has no source cache tag")
    optimization = "" if sys.flags.optimize == 0 else ".opt-" + str(sys.flags.optimize)
    basename = source.stem + "." + tag + optimization + ".pyc"
    paths = set()
    for prefix in prefixes:
        if prefix is None:
            paths.add(str(source.parent / "__pycache__" / basename))
        else:
            prefix = _canonical_path(prefix, "approved cache prefix")
            paths.add(str(prefix / str(source.parent).lstrip("/") / basename))
    return paths


def classify_modules(rows, build, cache_prefixes=(None,)):
    """Validate a previously persisted snapshot; return classified source rows."""
    root, concrete, packages, namespaces = inventory(build)
    require(type(rows) is list, "Module snapshot must be an array")
    result, seen = [], set()
    for row in rows:
        name = row["module"]
        require(name not in seen, "Duplicate loaded importer module: " + name)
        seen.add(name)
        require(_value(row, "moduleName") == name and _value(row, "specName") == name, "Module/spec names differ: " + name)
        require(row["loaderObjectsIdentical"] is True, "Module/spec loader objects differ: " + name)
        loader = _value(row, "moduleLoaderClass")
        require(loader == _value(row, "specLoaderClass"), "Module/spec loader classes differ: " + name)
        if name in concrete:
            source, binding = concrete[name]
            require(loader == SOURCE_LOADER, "Unsupported concrete source loader: " + name)
            require(_value(row, "specHasLocation") is True, "Concrete source has no spec location: " + name)
            file_value, origin = _value(row, "file"), _value(row, "specOrigin")
            require(_canonical_path(file_value, "module file") == source and _canonical_path(origin, "spec origin") == source, "Concrete module origin differs: " + name)
            if name in packages:
                expected_locations = [str(source.parent)]
                require(_value(row, "moduleSearchLocations") == expected_locations and _value(row, "specSearchLocations") == expected_locations, "Concrete package locations differ: " + name)
            else:
                require(_absent_or_null(row, "moduleSearchLocations") and _value(row, "specSearchLocations") is None, "Concrete nonpackage has search locations: " + name)
            raw = source.read_bytes()
            actual = {"bytes": len(raw), "sha256": "sha256:" + hashlib.sha256(raw).hexdigest()}
            require(actual == {"bytes": binding["bytes"], "sha256": "sha256:" + binding["sha256"]}, "Loaded importer source differs: " + name)
            cached = _value(row, "cached")
            require(cached == _value(row, "specCached") and cached in _expected_caches(source, cache_prefixes), "Concrete cache metadata differs: " + name)
            require(not Path(cached).exists() and not Path(cached).is_symlink(), "Loaded importer has existing bytecode cache: " + name)
            result.append({"module": name, "kind": "concrete-source", "file": file_value, "resolvedFile": str(source), "source": actual,
                           "cached": cached, "cachedFileExists": False, "specOrigin": origin, "loaderClass": loader,
                           "searchLocations": [str(source.parent)] if name in packages else None})
        else:
            require(name in namespaces, "Loaded importer module has unpinned name: " + name)
            directory = namespaces[name]
            require(loader == NAMESPACE_LOADER, "Unsupported namespace loader: " + name)
            require(_value(row, "specHasLocation") is False and _value(row, "specOrigin") is None, "Namespace has a concrete spec origin: " + name)
            require(_absent_or_null(row, "file") and _absent_or_null(row, "cached") and _value(row, "specCached") is None, "Namespace has concrete file/cache metadata: " + name)
            expected_locations = [str(directory)]
            require(_value(row, "moduleSearchLocations") == expected_locations and _value(row, "specSearchLocations") == expected_locations, "Namespace locations differ from pinned inventory: " + name)
            require(directory.is_relative_to(root) and directory.is_dir() and not (directory / "__init__.py").exists(), "Namespace directory changed: " + name)
            result.append({"module": name, "kind": "namespace-package", "file": None, "resolvedFile": None, "source": None,
                           "cached": None, "cachedFileExists": False, "specOrigin": None, "loaderClass": loader,
                           "searchLocations": expected_locations})
    return result
