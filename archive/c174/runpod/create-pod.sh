#!/usr/bin/env bash
# Preview by default. For an approved allocation, arm both cleanup jobs before creating one Pod.
set -euo pipefail
if [[ $# -gt 1 || ( $# -eq 1 && $1 != --launch ) ]]; then
    echo 'Usage: bash create-pod.sh [--launch]' >&2
    exit 2
fi
gpu=${RUNPOD_GPU:-NVIDIA A40}
image=${RUNPOD_IMAGE:-runpod/pytorch:1.0.3-cu1281-torch291-ubuntu2404}
name=ontokin-flowhmr-c174-UNIQUE
if [[ $# == 1 ]]; then
    [[ ${RUNPOD_BILLING_APPROVED:-} == YES ]] || {
        echo 'Refusing billable Pod creation without RUNPOD_BILLING_APPROVED=YES.' >&2
        exit 3
    }
    name=ontokin-flowhmr-c174-$(python3 -c 'import uuid; print(uuid.uuid4().hex)')
fi
args=(pod create --name "$name" --image "$image" --gpu-id "$gpu" --gpu-count 1
      --cloud-type SECURE --container-disk-in-gb 60 --volume-in-gb 100
      --volume-mount-path /workspace --ssh --ports 22/tcp --wait --wait-timeout 10m)
printf 'Proposed command: runpodctl'
printf ' %q' "${args[@]}"
printf '\nControl-host deadlines: request stop at 4h and permanent deletion at 24h.\n'
if [[ $# == 0 ]]; then
    echo 'Dry-run only. No scheduler or Runpod command ran.'
    exit 0
fi
umask 077
state_root=${RUNPOD_CONTROL_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/ontokin/runpod}
[[ $state_root == /* ]] || { echo 'RUNPOD_CONTROL_DIR must be absolute.' >&2; exit 2; }
receipt="$state_root/$name"
mkdir -p -- "$state_root"
mkdir -- "$receipt"
echo "Private control receipts: $receipt"
pkg=$(cd -- "$(dirname -- "$0")" && pwd -P)
cp -- "$pkg/pod-deadlines.py" "$receipt/"
cli=$(type -P runpodctl) || { echo 'Install runpodctl first.' >&2; exit 4; }
# Use the same persisted runpodctl identity now and when the scheduler runs.
control=(env -i HOME="$HOME" PATH="$PATH" LC_ALL=C RUNPOD_NO_UPDATE_CHECK=1)
"${control[@]}" python3 "$receipt/pod-deadlines.py" arm "$cli"
if ! "${control[@]}" "$cli" "${args[@]}" > "$receipt/create.json" 2> "$receipt/create.stderr"; then
    echo "Allocation or SSH readiness failed. Reconcile $name before a retry. See $receipt/create.stderr." >&2
    "${control[@]}" python3 "$receipt/pod-deadlines.py" stop "$cli"
    exit 5
fi
if ! "${control[@]}" python3 "$receipt/pod-deadlines.py" record "$cli"; then
    echo "Unexpected create receipt. Reconcile $name before retrying." >&2
    "${control[@]}" python3 "$receipt/pod-deadlines.py" stop "$cli"
    exit 5
fi
