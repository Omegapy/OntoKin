#!/usr/bin/env bash
# Collect only the receipts and outputs from a completed or refused C174 attempt.
set -euo pipefail
umask 077
if [[ $# != 2 || ! -d $1 || $2 != /* ]]; then
    echo 'Usage: bash collect-evidence.sh C174_JOB NEW_ABSOLUTE_RETURN_DIR' >&2
    exit 2
fi
job=$(realpath -e -- "$1")
name=$(basename -- "$job")
[[ $name == c174-* && -f $job/handoff.zip.sha256 ]] || { echo 'Select the exact C174 job printed by the runner.' >&2; exit 2; }
dest=$(realpath -m -- "$2")
[[ $dest != "$job" && $dest != "$job/"* ]] || { echo 'Choose a return directory outside the job.' >&2; exit 2; }
mkdir -- "$dest"
cd -- "$job"
files=(handoff.zip.sha256)
for stage in package-check restore resume; do
    for suffix in stdout stderr exitcode; do
        path="$stage.$suffix"
        [[ ! -f $path ]] || files+=("$path")
    done
done
[[ ! -d output ]] || files+=(output)
tar -czf "$dest/$name.tar.gz" -- "${files[@]}"
cd -- "$dest"
tar -tzf "$name.tar.gz" > contents.txt
sha256sum -- "$name.tar.gz" > SHA256SUMS
sha256sum -c SHA256SUMS
printf 'Copy the entire return directory off the Pod: %s\n' "$dest"
