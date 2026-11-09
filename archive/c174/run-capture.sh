#!/usr/bin/env bash
# Invoke from a provisioned Linux worker with the authorized body assets.
set -euo pipefail
if [[ $# != 5 ]]; then
    echo 'Usage: bash run-capture.sh RESTORED_JOB FLOWHMR_CHECKOUT WORKER_PYTHON FLOWHMR_CHECKPOINT NEW_JOB' >&2
    exit 2
fi
for path in "$@"; do
    [[ $path == /* ]] || { echo 'All five paths must be absolute.' >&2; exit 2; }
done
kit=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$1/review/checkout
controller=$1/review/venv/bin/python
video=$kit/capture/stretch_slow_static_1280x720_25fps.mp4
[[ ! -e $5 && ! -L $5 ]] || { echo 'Use a new output directory.' >&2; exit 2; }
printf '%s  %s\n' 2005ac3b8c994d6cfebbb53d52a2262e4167686d757731b6f8a2347f276ea535 "$video" | sha256sum -c -
# The controller resolves the checkpoint before FlowHMR chooses its config.yml.
checkpoint=$(realpath -e -- "$4")
config=$(dirname -- "$checkpoint")/config.yml
printf '%s  %s\n' b7eb06b119feaf5ad7287bafdb2fff38d42dfc22ea9d256f8cdd2ada26dfc53a "$checkpoint" | sha256sum -c -
check_config() {
    printf '%s  %s\n' 5deae01800c031975558bf9675819e8d1e24803414f692b8b5c2196b266c64d7 "$config" | sha256sum -c -
}
check_config
cd "$repo"
[[ $(git rev-parse HEAD) == 038370794d828972cf5a06cdceac50275eda65f0 ]] || { echo 'Unexpected OntoKin revision.' >&2; exit 2; }
[[ -z $(git status --porcelain --untracked-files=no) ]] || { echo 'The OntoKin checkout has tracked changes.' >&2; exit 2; }
"$controller" -B -m tools.perception run-worker flowhmr "$video" "$5" --checkout "$2" \
    --python "$3" --checkpoint "$checkpoint" --static-camera --timeout-s 1800
check_config
PYTHONPATH="$repo" "$controller" -B "$kit/qualification/verify-capture.py" "$5" "$video" --stretch \
    > "$5/capture-check.json" 2> "$5/capture-check.stderr"
