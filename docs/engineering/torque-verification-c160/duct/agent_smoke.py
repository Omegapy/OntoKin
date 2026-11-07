"""Use a fresh Agent/0.11 CLI store to create, export and retrieve the pilot duct."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    args = parser.parse_args()
    repo = args.checkout.resolve()
    source = Path(__file__).with_name("duct.ok").read_text()
    protocol = "ontokin.agent/0.11"
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        records = []
        def send(operation, **fields):
            request = dict(schema_version=protocol, project_id="duct-pilot",
                           request_id=operation + "-1", operation=operation, **fields)
            request_path = folder / (operation + ".json")
            request_path.write_text(json.dumps(request))
            run = subprocess.run([sys.executable, "-B", "-m", "ontokin", "agent",
                                  "--protocol", protocol, "--store", str(folder/"store"),
                                  "--request", str(request_path), "--wait"],
                                 cwd=repo, capture_output=True, check=False)
            if run.returncode:
                raise ValueError((run.stdout[:1024], run.stderr[:1024]))
            result = json.loads(run.stdout)
            if result["status"] != "succeeded":
                raise ValueError(result)
            records.append(dict(operation=operation, status=result["status"],
                                accepted_revision=result["accepted_program_revision"]))
            return result
        created = send("create", bundle={"schema_version": "ontokin.bundle/0.1",
                                         "entry": {"filename": "shape.ok", "source": source},
                                         "modules": []}, expected_program_revision=None,
                       requested_level="constructed")
        revision = created["accepted_program_revision"]
        exported = send("export", program_revision=revision, destination="ontokin.glb/0.11",
                        options={"fps": 2, "end": "1", "helpers": False})["result"]
        part = send("artifact", artifact_id=exported["artifact_id"], offset=0, max_bytes=65536)["result"]
        payload = base64.b64decode(part["data_base64"], validate=True)
        actual = "sha256:" + hashlib.sha256(payload).hexdigest()
        if (part["next_offset"] is not None or actual != exported["sha256"]
                or len(payload) != exported["total_bytes"]):
            raise ValueError("incomplete or mismatched artifact")
        print(json.dumps(dict(protocol=protocol, source=hashlib.sha256(source.encode()).hexdigest(),
                              source_filename="shape.ok", artifact_sha256=actual, bytes=len(payload),
                              operations=records), indent=2))


if __name__ == "__main__":
    main()
