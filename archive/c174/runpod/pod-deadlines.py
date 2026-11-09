"""Register and run the two off-Pod C174 cleanup jobs from the private control directory."""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def matching_pod(cli, name):
    output = subprocess.check_output([cli, "pod", "list", "--all", "--name", name], timeout=90)
    items = json.loads(output)
    if not isinstance(items, list):
        raise ValueError("Unexpected Pod list")
    ids = [pod["id"] for pod in items if pod["name"] == name]
    if len(ids) > 1 or any(not re.fullmatch(r"[A-Za-z0-9_-]+", pod_id) for pod_id in ids):
        raise ValueError("Ambiguous Pod identity. Inspect the account before cleanup.")
    return ids[0] if ids else None


def main():
    action, cli = sys.argv[1:]
    helper = Path(__file__).resolve()
    directory = helper.parent
    name = directory.name
    if not re.fullmatch(r"ontokin-flowhmr-c174-[a-f0-9]{32}", name):
        raise ValueError("Run the helper from this launch's private control directory")
    if not Path(cli).is_absolute():
        raise ValueError("Expected an absolute runpodctl executable")
    id_file = directory / "pod-id"
    if action == "arm":
        if sys.platform != "linux":
            raise ValueError("A persistent Linux control host with atd is required")
        for mode, expected in (("is-enabled", "enabled"), ("is-active", "active")):
            state = subprocess.check_output(["systemctl", mode, "atd.service"], text=True, timeout=15)
            if state.strip() != expected:
                raise ValueError(f"systemctl {mode} must report {expected!r} for atd.service")
        if matching_pod(cli, name):
            raise ValueError("Proposed Pod name is already in use")
        at = shutil.which("at")
        if not at:
            raise ValueError("Install the at scheduler first")
        for operation, hours in (("stop", 4), ("delete", 24)):
            log = directory / f"{operation}.log"
            command = shlex.join([sys.executable, str(helper), operation, cli])
            command += f" >> {shlex.quote(str(log))} 2>&1\n"
            with (directory / f"schedule-{operation}.log").open("x") as receipt:
                result = subprocess.run([at, "now", "+", str(hours), "hours"], input=command,
                                        text=True, cwd=directory, stdout=receipt, stderr=subprocess.STDOUT)
            if result.returncode:
                raise RuntimeError(f"Could not queue {operation}. Consult {receipt.name}.")
        print("Both at jobs accepted. See schedule-stop.log and schedule-delete.log.")
    elif action == "record":
        pod = json.loads((directory / "create.json").read_text())
        pod_id = pod["id"]
        if pod["name"] != name or not re.fullmatch(r"[A-Za-z0-9_-]+", pod_id):
            raise ValueError("Unexpected identity in creation response")
        # Replace atomically so a control-host interruption cannot leave a partial ID.
        temp = directory / "pod-id.tmp"
        temp.write_text(pod_id + "\n")
        os.replace(temp, id_file)
        print(f"Pod {pod_id} answered the SSH banner check. Authenticate using runpodctl ssh info {pod_id}.")
    elif action in ("stop", "delete"):
        # Once recorded, the immutable ID follows the original Pod even if it was renamed.
        pod_id = id_file.read_text().strip() if id_file.exists() else matching_pod(cli, name)
        if not pod_id:
            print("No matching Pod found. Reconcile any unknown creation outcome in the account.")
            return
        if not re.fullmatch(r"[A-Za-z0-9_-]+", pod_id):
            raise ValueError("Invalid recorded Pod ID. Inspect the account.")
        subprocess.run([cli, "pod", action, pod_id], check=True, timeout=90)
    else:
        raise ValueError("Unknown control operation")


if __name__ == "__main__":
    main()
