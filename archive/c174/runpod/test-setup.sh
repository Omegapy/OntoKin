#!/usr/bin/env bash
# Local control-host tests. Every scheduler and Runpod invocation uses a fake executable.
set -euo pipefail
dir=$(cd -- "$(dirname -- "$0")" && pwd -P)
for script in "$dir"/*.sh; do bash -n "$script"; done
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
mock="$work/bin"
mkdir -p "$mock" "$work/receipts"
cat > "$mock/systemctl" <<'MOCK'
#!/bin/sh
if [ -f "$(dirname "$0")/shim-$1" ]; then
    echo 'systemd is not running in this container'
    exit 0
fi
case "$*" in
    "is-enabled atd.service") echo enabled ;;
    "is-active atd.service") echo active ;;
    *) exit 1 ;;
esac
MOCK
cat > "$mock/at" <<'MOCK'
#!/bin/sh
set -eu
here=$(dirname "$0")
[ -z "${RUNPOD_API_KEY:-}" ]
[ -f "./pod-deadlines.py" ]
printf '%s\n' "at $*" >> "$here/sequence"
cat > "$here/scheduled-$3"
[ ! -f "$here/refuse-$3" ]
MOCK
cat > "$mock/runpodctl" <<'MOCK'
#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
base = Path(__file__).resolve().parent
args = sys.argv[1:]
assert "RUNPOD_API_KEY" not in os.environ
with (base / "sequence").open("a") as log:
    print("cli " + args[1], file=log)
if args[:2] == ["pod", "list"]:
    print((base / "list.json").read_text() if (base / "list.json").exists() else "[]")
elif args[:2] == ["pod", "create"]:
    (base / "args").write_text(json.dumps(args))
    row = {"name": args[args.index("--name") + 1], "id": "fixture123"}
    (base / "list.json").write_text(json.dumps([row]))
    if (base / "fail-create").exists():
        sys.exit(1)
    print(json.dumps(row))
elif args in (["pod","stop","fixture123"],["pod","delete","fixture123"]):
    print("{}")
else:
    sys.exit(20)
MOCK
chmod +x "$mock"/{at,systemctl,runpodctl}
# Clear inherited approvals, endpoints and shell functions. Explicit fake credentials
# catch accidental export to the scheduler or selection of a different account.
runner=(env -i HOME="$HOME" PATH="$mock:/usr/bin:/bin" RUNPOD_CONTROL_DIR="$work/receipts" RUNPOD_API_KEY=fake-control)
"${runner[@]}" RUNPOD_BILLING_APPROVED=YES bash "$dir/create-pod.sh" > "$work/dry.log"
grep -q 'Dry-run only' "$work/dry.log"
if "${runner[@]}" bash "$dir/create-pod.sh" --launch > "$work/refusal.log" 2>&1; then exit 1; fi
grep -q 'Refusing billable' "$work/refusal.log"
test ! -e "$mock/sequence"
printf 'PASS dry-run and missing approval are inert\n'
for mode in is-enabled is-active; do
    touch "$mock/shim-$mode"
    if "${runner[@]}" RUNPOD_BILLING_APPROVED=YES bash "$dir/create-pod.sh" --launch > "$work/shim.log" 2>&1; then exit 1; fi
    grep -q "systemctl $mode must report" "$work/shim.log"
    test ! -e "$mock/sequence"
    rm -- "$mock/shim-$mode"
done
printf 'PASS zero-exit systemctl shims refuse allocation before scheduling or Runpod calls\n'
touch "$mock/refuse-24"
if "${runner[@]}" RUNPOD_BILLING_APPROVED=YES bash "$dir/create-pod.sh" --launch > "$work/atfail.log" 2>&1; then exit 1; fi
grep -q 'Could not queue delete' "$work/atfail.log"
test ! -e "$mock/args"
printf 'PASS unarmed deletion refuses allocation\n'
rm -- "$mock/refuse-24"
: > "$mock/sequence"
"${runner[@]}" RUNPOD_BILLING_APPROVED=YES bash "$dir/create-pod.sh" --launch > "$work/pass.log"
python3 - "$mock" <<'PY'
import json, re, sys
from pathlib import Path
b = Path(sys.argv[1])
args = json.loads((b/"args").read_text())
assert re.fullmatch(r"ontokin-flowhmr-c174-[0-9a-f]{32}", args[3])
assert args == ["pod", "create", "--name", args[3], "--image", "runpod/pytorch:1.0.3-cu1281-torch291-ubuntu2404",
                "--gpu-id", "NVIDIA A40", "--gpu-count", "1", "--cloud-type", "SECURE", "--container-disk-in-gb", "60",
                "--volume-in-gb", "100", "--volume-mount-path", "/workspace", "--ssh", "--ports", "22/tcp",
                "--wait", "--wait-timeout", "10m"]
assert (b/"sequence").read_text().splitlines() == ["cli list", "at now + 4 hours", "at now + 24 hours", "cli create"]
PY
for hours in 4 24; do "${runner[@]}" env -u RUNPOD_API_KEY sh "$mock/scheduled-$hours"; done
grep -qx 'cli stop' "$mock/sequence"
grep -qx 'cli delete' "$mock/sequence"
printf 'PASS exact GPU/SSH request and both queued commands target the fixture Pod\n'
rm -- "$mock/list.json"
touch "$mock/fail-create"
if "${runner[@]}" RUNPOD_BILLING_APPROVED=YES bash "$dir/create-pod.sh" --launch > "$work/incomplete.log" 2>&1; then exit 1; fi
test "$(tail -1 "$mock/sequence")" = 'cli stop'
# An incomplete create can only be resolved by exact, unambiguous name.
printf '[{"id":"other","name":"unrelated"}]\n' > "$mock/list.json"
"${runner[@]}" env -u RUNPOD_API_KEY sh "$mock/scheduled-24"
test "$(tail -1 "$mock/sequence")" = 'cli list'
python3 - "$mock" <<'PY'
import json, sys
from pathlib import Path
b = Path(sys.argv[1]); name = json.loads((b/"args").read_text())[3]
(b/"list.json").write_text(json.dumps([{"name":name,"id":"a"},{"name":name,"id":"b"}]))
PY
if "${runner[@]}" env -u RUNPOD_API_KEY sh "$mock/scheduled-24"; then exit 1; fi
test "$(tail -1 "$mock/sequence")" = 'cli list'
printf 'PASS create failure triggers stop; unmatched and ambiguous targets receive no mutation\n'
