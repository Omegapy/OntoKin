"""Check readback-config-001.json against HOST, the freeze's bindings, the provider's constants and PLAN-REVIEW-001 (read only).

Usage: python3 -I -S -B check_config.py CONFIG HOST FREEZE PLAN_REVIEW PROVIDER OUT.json
The provider's constants are read from its source text with ast (it is not imported).
"""
import ast, hashlib, json, os, stat, sys

config_path, host_path, freeze_path, review_path, provider_path, destination = sys.argv[1:7]
config = json.load(open(config_path, "rb"))
host = json.load(open(host_path, "rb"))
freeze = json.load(open(freeze_path, "rb"))
review = json.load(open(review_path, "rb"))
tree = ast.parse(open(provider_path, "rb").read())
constants = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        try:
            constants[node.targets[0].id] = ast.literal_eval(node.value)
        except Exception:
            pass
bindings = {row["path"]: row for row in freeze["bindings"]}


def describe(path):
    info = os.lstat(path)
    return {"path": path, "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(), "size_bytes": info.st_size,
            "mode": oct(stat.S_IMODE(info.st_mode)), "nlink": info.st_nlink}


checks = {}
keys = constants["CONFIG_KEYS"].split() if isinstance(constants.get("CONFIG_KEYS"), str) else None
checks["closed_keys"] = sorted(config) == sorted("schema contract contract_source amendment_adoption source host dependencies runtime methods evidence_root parent".split())
checks["schema"] = config["schema"] == "ontokin.current-host-readback-config/0.2.0"
checks["contract"] = config["contract"] == constants.get("CONTRACT")
root = config["source"]["root"]
checks["source_equals_host"] = {k: config["source"][k] == host["source"][k] for k in ("root", "commit", "tree", "inventory")}
checks["dependencies_equal_host"] = {"root": config["dependencies"]["root"] == host["dependencies"]["root"],
                                     "inventory": config["dependencies"]["inventory"] == host["dependencies"]["inventory"]}
checks["runtime_equals_host"] = config["runtime"] == {"executable": host["runtime"]["executable"], "version": host["runtime"]["version"]} \
    and config["runtime"]["version"] == constants.get("NODE_VERSION")
host_actual = describe(config["host"]["path"])
checks["host_descriptor"] = {k: config["host"][k] == host_actual[k] for k in ("sha256", "size_bytes", "mode")}
checks["host_sha_equals_review_record"] = config["host"]["sha256"] == "858ef72a949ce7575787290601ae70d117090a460781b2e660a3b0d4f0162666"
for key, relative in (("contract_source", constants.get("CONTRACT_PATH")), ("amendment_adoption", constants.get("AMENDMENT_ADOPTION_PATH"))):
    actual = describe(os.path.join(root, relative))
    checks[key] = {"path": config[key]["path"] == os.path.join(root, relative),
                   **{k: config[key][k] == actual[k] for k in ("sha256", "size_bytes", "mode")}, "nlink_one": actual["nlink"] == 1}
checks["pr06_adoption"] = config["amendment_adoption"]["sha256"] == "872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937" \
    and config["amendment_adoption"]["size_bytes"] == 5396
text = json.dumps(review)
checks["pr06_in_plan_review_record"] = "872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937" in text
methods_actual = describe(config["methods"]["path"])
checks["methods_descriptor"] = {k: config["methods"][k] == methods_actual[k] for k in ("sha256", "size_bytes", "mode")}
methods = json.load(open(config["methods"]["path"], "rb"))
checks["methods_bodies_equal_provider_constants"] = methods["original_bodies"] == constants.get("ORIGINAL_BODIES")
checks["methods_source_test"] = methods["source_test"] == "tests/test_static_tray_readback_v01.py"
discovery_actual = describe(methods["discovery"]["path"])
checks["discovery_descriptor"] = {k: methods["discovery"][k] == discovery_actual[k] for k in ("sha256", "size_bytes", "mode")}
discovery = json.load(open(methods["discovery"]["path"], "rb"))
map_actual = describe(os.path.join(root, constants.get("BASELINE_MAP")))
checks["baseline_map"] = discovery["baseline_map"] == {k: map_actual[k] for k in ("path", "sha256", "size_bytes", "mode")}
method_ids = sorted("test_static_tray_readback_v01." + name for name in constants["ORIGINAL_BODIES"] if ".test_" in name)
checks["discovery_has_the_seven"] = all(i in discovery["method_ids"] for i in method_ids) and len(method_ids) == 7
checks["evidence_root"] = {"value": config["evidence_root"] == freeze["places"]["<A1>"], "absent_now": not os.path.lexists(config["evidence_root"]),
                           "outside_source": not config["evidence_root"].startswith(root + "/")}
checks["parent_null"] = config["parent"] is None
checks["config_outside_source"] = not config_path.startswith(root + "/")
checks["config_nlink_one"] = os.lstat(config_path).st_nlink == 1
checks["host_git"] = {"path": host["git"]["path"], "sha_equals_binding": bindings.get(host["git"]["path"], {}).get("sha256") == host["git"]["sha256"]}
flat = []


def walk(value, prefix=""):
    if isinstance(value, dict):
        for k, v in value.items():
            walk(v, prefix + "/" + k)
    else:
        flat.append((prefix, value))


walk(checks)
checks["all_true"] = all(v is True for k, v in flat if not k.startswith("/host_git/path"))
with open(destination, "x") as fh:
    json.dump(checks, fh, indent=1)
    fh.write("\n")
print(json.dumps(checks, indent=1))
