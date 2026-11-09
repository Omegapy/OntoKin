#!/usr/bin/env bash
# Stage only the four public inputs that the C174 launcher identifies by SHA-256.
set -euo pipefail
root=${ONTOKIN_WORKSPACE:-/workspace}
if [[ $root != /* || $# -gt 1 || ( $# -eq 1 && $1 != --check ) ]]; then
    echo 'Usage: ONTOKIN_WORKSPACE=/absolute/workspace bash stage-public.sh [--check]' >&2
    exit 2
fi
mode=${1:-download}
flow=$root/FlowHMR
[[ -d $flow ]] || { echo "Prepare the FlowHMR checkout first: $flow" >&2; exit 3; }
model=$root/models/flowhmr_latest/flowhmr_latest.ckpt
release='https://huggingface.co/fafsaf1/flowhmr-0.46B/resolve/1eb105e554e0cfc1846ea5feac8c2d516a36d319/flowhmr_latest'

stage() (
    local path=$1 sha=$2 url=$3 part
    if [[ -e $path || -L $path ]]; then
        [[ -f $path ]] || { echo "Expected a regular file: $path" >&2; exit 1; }
        printf '%s  %s\n' "$sha" "$path" | sha256sum -c -
        exit
    fi
    [[ $mode != --check ]] || { echo "Missing public file: $path" >&2; exit 1; }
    mkdir -p -- "$(dirname -- "$path")"
    part=$(mktemp -- "$path.download.XXXXXXXX")
    trap 'rm -f -- "$part"' EXIT
    curl --fail --location --retry 3 --output "$part" "$url"
    printf '%s  %s\n' "$sha" "$part" | sha256sum --check --status || {
        echo "Downloaded bytes failed SHA-256 verification: $path" >&2; exit 1;
    }
    mv -T -- "$part" "$path"
    printf 'Verified public file: %s\n' "$path"
)
stage "$flow/ckpts/yolox/yolox_l.pth" \
    1e6b7fa6240375370b2a8a8eab9066b3cdd43fd1d0bfa8d2027fd3a51def2917 \
    'https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_l.pth'
stage "$flow/assets/body_models/smpl_neutral_J_regressor.pt" \
    70e3213bd30fe8d8ce37b54675282745e406f915a51511a003aeff99b6da04cf \
    'https://raw.githubusercontent.com/zju3dv/GVHMR/main/hmr4d/utils/body_model/smpl_neutral_J_regressor.pt'
stage "$model" b7eb06b119feaf5ad7287bafdb2fff38d42dfc22ea9d256f8cdd2ada26dfc53a \
    "$release/flowhmr_latest.ckpt"
# The controller and FlowHMR read the YAML beside the resolved checkpoint.
config=$(dirname -- "$(realpath -e -- "$model")")/config.yml
if [[ -L $model && ! -f $config ]]; then
    echo "Supply the release configuration beside the linked checkpoint: $config" >&2
    exit 1
fi
stage "$config" 5deae01800c031975558bf9675819e8d1e24803414f692b8b5c2196b266c64d7 "$release/config.yml"
