#!/usr/bin/env bash
# Install FlowHMR's pinned video runtime on the provisioned Runpod worker.
set -euo pipefail
ROOT=${ONTOKIN_WORKSPACE:-/workspace}
DIR=$(cd -- "$(dirname -- "$0")" && pwd -P)
FLOW=$ROOT/FlowHMR
VENV=$ROOT/envs/flowhmr
CONTROLLER_ENV=$ROOT/envs/ontokin
REV=87ebb483ce9da32be72c67971bc8fd76f27251f3
[[ $# == 0 && $ROOT == /* ]] || { echo 'Usage: ONTOKIN_WORKSPACE=/absolute/workspace bash bootstrap-v2m.sh' >&2; exit 2; }
[[ $(uname -sm) == 'Linux x86_64' ]] || { echo 'C174 requires Linux x86-64.' >&2; exit 3; }
command -v nvidia-smi >/dev/null || { echo 'No nvidia-smi; provision a GPU-enabled Pod first.' >&2; exit 3; }
VRAM_MIB=$(nvidia-smi --id=0 --query-gpu=memory.total --format=csv,noheader,nounits | tr -d '[:space:]')
[[ $VRAM_MIB =~ ^[0-9]+$ ]] && (( VRAM_MIB >= 39000 )) || {
    echo "Need approximately 40 GB of GPU memory; observed ${VRAM_MIB:-unknown} MiB." >&2; exit 3;
}
for tool in git curl sha256sum c++; do
    command -v "$tool" >/dev/null || { echo "Missing required tool: $tool." >&2; exit 3; }
done
# Use conda-forge for both interpreters even when the base image has another Conda.
if ! command -v conda >/dev/null; then
    if [[ ! -x $ROOT/miniforge3/bin/conda ]]; then
        mkdir -p "$ROOT/installers"
        installer=$ROOT/installers/Miniforge3-26.9.4-1-Linux-x86_64.sh
        curl -fL --retry 3 -o "$installer" \
          'https://github.com/conda-forge/miniforge/releases/download/26.9.4-1/Miniforge3-26.9.4-1-Linux-x86_64.sh'
        printf '%s  %s\n' 571b410272cc434f28bc6c5c49ca8ffd4a4d1bcba9f57f1b6baccdb46446cfcc "$installer" | sha256sum -c -
        bash "$installer" -b -p "$ROOT/miniforge3"
    fi
    export PATH="$ROOT/miniforge3/bin:$PATH"
fi
mkdir -p "$ROOT/envs" "$ROOT/jobs"
if [[ ! -e $FLOW ]]; then
    git clone --no-checkout https://github.com/flowhmr/flowhmr.git "$FLOW"
    git -C "$FLOW" checkout --detach "$REV"
fi
[[ -d $FLOW/.git && $(git -C "$FLOW" rev-parse HEAD) == "$REV" ]] || {
    echo "Use a fresh workspace or the pinned FlowHMR checkout at $FLOW." >&2; exit 4;
}
[[ -z $(git -C "$FLOW" status --porcelain --untracked-files=no --ignore-submodules=untracked) ]] || {
    echo 'The FlowHMR checkout has tracked changes.' >&2; exit 4;
}
git -C "$FLOW" submodule update --init --recursive
if [[ ! -x $VENV/bin/python ]]; then
    conda create -y --override-channels -c conda-forge -p "$VENV" python=3.10 pip
fi
if [[ ! -x $CONTROLLER_ENV/bin/python3.12 ]]; then
    conda create -y --override-channels -c conda-forge -p "$CONTROLLER_ENV" python=3.12.14 pip
fi
"$CONTROLLER_ENV/bin/python3.12" -I -c 'import sys; assert sys.implementation.name == "cpython" and sys.version_info[:3] == (3,12,14)'
"$VENV/bin/python" -I -c 'import sys; assert sys.implementation.name == "cpython" and sys.version_info[:2] == (3,10)'
# Child processes must also find this interpreter when compiling editable YOLOX.
export PATH="$VENV/bin:$PATH"
unset PYTHONHOME PYTHONPATH
"$VENV/bin/python" -m pip install setuptools wheel
"$VENV/bin/python" -m pip install -r "$FLOW/requirements.txt" -r "$FLOW/tools/web/requirements.txt"
"$VENV/bin/python" -m pip install --no-build-isolation --no-deps -e "$FLOW/third_party/YOLOX"
# YOLOX also declares unrelated export dependencies. Check the V2M contract C174 actually runs.
"$VENV/bin/python" -IB - "$DIR/../worker/worker_preflight.py" "$FLOW" <<'PY'
import json
import runpy
import sys
from pathlib import Path
probe = runpy.run_path(sys.argv[1])
checkout = Path(sys.argv[2])
checks = {"source": probe["source"](checkout), "cuda": probe["cuda"](),
          "ffmpeg": probe["ffmpeg"](checkout), "dependencies": probe["dependencies"](checkout)}
print(json.dumps(checks, indent=2))
if any(record["status"] != "pass" for record in checks.values()):
    sys.exit("C174 worker runtime checks failed")
PY
bash "$DIR/stage-public.sh"
printf 'Runtime and four public inputs verified. Stage the authorized SAM and neutral SMPL-H files before capture.\n'
