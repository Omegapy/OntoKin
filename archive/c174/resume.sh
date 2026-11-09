#!/usr/bin/env bash
# Run the greenhouse capture and evaluation once on the prepared project worker.
set -euo pipefail
if [[ $# != 5 ]]; then
    echo 'Usage: bash resume.sh RESTORED_JOB FLOWHMR_CHECKOUT WORKER_PYTHON FLOWHMR_CHECKPOINT NEW_OUTPUT' >&2
    exit 2
fi
for path in "$@"; do
    [[ $path == /* ]] || { echo 'Use absolute paths for all five arguments.' >&2; exit 2; }
done
kit=$(cd -- "$(dirname -- "$0")" && pwd -P)
out=$5
mkdir -- "$out"
# Each stage records its exit code, including a timed-out readiness screen.
stage() {
    local name=$1
    shift
    local rc=0
    "$@" > "$out/$name.stdout" 2> "$out/$name.stderr" || rc=$?
    echo "$rc" > "$out/$name.exitcode"
    if [[ $rc != 0 ]]; then
        echo "Stopped at $name (exit $rc). See $out/$name.stdout and $out/$name.stderr." >&2
        return "$rc"
    fi
}
stage preflight timeout 300 "$3" -I -B "$kit/worker/worker_preflight.py" "$2" "$4"
stage capture bash "$kit/run-capture.sh" "$1" "$2" "$3" "$4" "$out/capture"
stage evaluation bash "$kit/evaluate-capture.sh" "$1" "$out/capture" "$out/evaluation"
echo "See $out/evaluation/evaluation.json and review the motion before closing issue 109."
