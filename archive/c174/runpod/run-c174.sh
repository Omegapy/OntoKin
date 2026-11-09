#!/usr/bin/env bash
# Run from the integrated C174 kit already extracted on the Pod.
set -euo pipefail
umask 077
if [[ $# != 1 || ! -f $1 ]]; then
    echo 'Usage: bash runpod/run-c174.sh /path/to/integrated-C174.zip' >&2
    exit 2
fi
archive=$(realpath -e -- "$1")
kit=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
root=${ONTOKIN_WORKSPACE:-/workspace}
[[ $root == /* && -d $root ]] || { echo 'Choose an existing absolute ONTOKIN_WORKSPACE.' >&2; exit 2; }
root=$(realpath -e -- "$root")
jobs=$(realpath -m -- "$root/jobs")
if [[ $archive == "$kit/"* || $jobs == "$kit" || $jobs == "$kit/"* ]]; then
    echo 'Keep both the archive and jobs directory outside the extracted handoff.' >&2
    exit 2
fi
controller="$root/envs/ontokin/bin/python3.12"
worker="$root/envs/flowhmr/bin/python"
flow="$root/FlowHMR"
weights="$root/models/flowhmr_latest/flowhmr_latest.ckpt"
[[ -x $controller && -x $worker ]] || { echo 'Run bootstrap-v2m.sh on the Pod first.' >&2; exit 3; }
"$controller" -IB -c 'import sys; assert sys.implementation.name == "cpython" and sys.version_info[:3] == (3, 12, 14), "C174 requires CPython 3.12.14"'
export PATH="$root/envs/ontokin/bin:$PATH"
mkdir -p -- "$jobs"
job=$(mktemp -d -- "$jobs/c174-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXXXX")
echo "C174 job directory: $job"
stage() {
    local name=$1 rc=0
    shift
    "$@" > "$job/$name.stdout" 2> "$job/$name.stderr" || rc=$?
    echo "$rc" > "$job/$name.exitcode"
    if (( rc != 0 )); then
        echo "Stopped at $name (exit $rc). See $job/$name.stderr and $job/$name.stdout." >&2
    fi
    return "$rc"
}
sha256sum -- "$archive" > "$job/handoff.zip.sha256"
stage package-check "$controller" -IB "$kit/runpod/verify_kit.py" "$archive" "$kit"
stage restore bash "$kit/restore-main.sh" "$job/restored"
stage resume bash "$kit/resume.sh" "$job/restored" "$flow" "$worker" "$weights" "$job/output"
echo "Review the qualified capture and both action outcomes in $job/output."
