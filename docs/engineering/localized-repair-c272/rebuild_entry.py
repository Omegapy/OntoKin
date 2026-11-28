"""C272 declared rebuild entry (DEC-007).

It runs as `INSTALL_ENV/bin/python -I -B rebuild_entry.py` in a new workspace that holds
only `main.ok`, `hinges.ok` and this file. It uses the installed `ontokin-reference`
wheel, never a checkout, and the delivery run's route: Agent/0.2 `create` at level
`evaluated`, then `export` to `ontokin.glb/0.2` with `{"helpers": false}`, then `artifact`
retrieval, then the semantic sidecar from the accepted program and the retrieved bytes.
Outputs go to `./out/`.
"""
import base64
import hashlib
import json
import platform
import sys
from pathlib import Path

import ontokin
from ontokin.program_agent import ProgramAgentService
from ontokin.semantic_export import build_semantic_manifest, canonical_bytes

DECLARED = {"main.ok": None, "hinges.ok": {"package_id": "example.hinges", "version": "1.0.0"}}
here = Path.cwd()
files = {name: (here / name).read_bytes() for name in DECLARED}
bundle = {"schema_version": "ontokin.bundle/0.1",
          "entry": {"filename": "main.ok", "source": files["main.ok"].decode("utf-8")},
          "modules": [{**DECLARED["hinges.ok"], "filename": "hinges.ok", "source": files["hinges.ok"].decode("utf-8")}]}
out = here / "out"
out.mkdir()
exchanges = []
with ProgramAgentService(out / "store", protocol="ontokin.agent/0.2") as service:
    serial = 0

    def call(operation, **fields):
        global serial
        serial += 1
        request = {"schema_version": "ontokin.agent/0.2", "project_id": "c272-rebuild",
                   "request_id": f"rebuild-{serial:03d}-{operation}", "operation": operation, **fields}
        response = service.handle(request)
        kept = json.loads(json.dumps(response))
        if isinstance(kept.get("result"), dict) and "data_base64" in kept["result"]:
            kept["result"]["data_base64"] = "omitted"
        exchanges.append({"request": request, "response": kept})
        if response["status"] != "succeeded":
            raise SystemExit(f"{operation} failed: {kept}")
        return response

    created = call("create", bundle=bundle, expected_program_revision=None, requested_level="evaluated")
    revision = created["program_revision"]
    exported = call("export", program_revision=revision, destination="ontokin.glb/0.2", options={"helpers": False})
    glb, offset = bytearray(), 0
    while offset is not None:
        chunk = call("artifact", artifact_id=exported["result"]["artifact_id"], offset=offset, max_bytes=65536)
        glb.extend(base64.b64decode(chunk["result"]["data_base64"], validate=True))
        offset = chunk["result"]["next_offset"]
    glb = bytes(glb)
    program = service.read_program("c272-rebuild", revision)
    accepted = service.accepted_revision("c272-rebuild")
    semantic = canonical_bytes(build_semantic_manifest(program, glb, accepted_program_revision=accepted,
                                                       required_features=["stable_identities", "dimensions_units_frames"]))
    implementation = service.implementation
(out / "scene.glb").write_bytes(glb)
(out / "scene.semantic.json").write_bytes(semantic)
loaded = sorted({str(Path(m.__file__).resolve()) for m in list(sys.modules.values())
                 if getattr(m, "__file__", None) and m.__name__.split(".")[0] == "ontokin"})
(out / "rebuild-report.json").write_text(json.dumps({
    "program_revision": revision, "accepted_revision": accepted, "implementation": implementation,
    "python": platform.python_version(), "executable": sys.executable, "sys_path": sys.path,
    "ontokin_package": str(Path(ontokin.__file__).resolve().parent), "ontokin_modules_loaded": loaded,
    "flags": {"isolated": sys.flags.isolated, "dont_write_bytecode": sys.flags.dont_write_bytecode},
    "inputs": {n: hashlib.sha256(b).hexdigest() for n, b in files.items()},
    "outputs": {"scene.glb": hashlib.sha256(glb).hexdigest(), "scene.semantic.json": hashlib.sha256(semantic).hexdigest()},
    "exchanges": exchanges}, indent=2) + "\n")
