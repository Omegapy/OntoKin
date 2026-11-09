#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 3 || $1 != /* || $2 != /* || $3 != /* ]]; then
    echo 'Usage: bash evaluate-capture.sh RESTORED_JOB CAPTURE_JOB NEW_EVALUATION_DIR (absolute paths)' >&2
    exit 2
fi
kit=$(cd -- "$(dirname -- "$0")" && pwd -P)
cd -- "$1/review/checkout"
PYTHONPATH="$PWD" "$1/review/venv/bin/python" -B "$kit/qualification/evaluate-stretch.py" "$2" "$3"
