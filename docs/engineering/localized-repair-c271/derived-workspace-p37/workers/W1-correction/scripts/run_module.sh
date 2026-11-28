#!/bin/sh
# Run focused unittest modules exactly as the assignment prescribes, from the worktree root, and
# record the command, the start and end times, the exit status and the full output.
# Usage: run_module.sh <label> <module> [<module> ...]
set -u
label="$1"; shift
evidence=<local>/c271-p37/workers/W1-correction/runs
mkdir -p "$evidence"
cd <worktree> || exit 99
resolved="$(cd "$TMPDIR" && pwd -P)/"
log="$evidence/$label.log"
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
/usr/bin/env -i HOME="$HOME" LOGNAME="$LOGNAME" USER="$USER" PATH=/usr/bin:/bin TMPDIR="$resolved" \
  .venv/bin/python -B -m unittest "$@" -v > "$log" 2>&1
status=$?
ended="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
summary="$(grep -E '^(Ran [0-9]+ tests? in|OK|FAILED)' "$log" | tr '\n' ' ')"
digest="$(shasum -a 256 "$log" | cut -d' ' -f1)"
printf '{"label": "%s", "command": "/usr/bin/env -i HOME=<home> LOGNAME=<logname> USER=<user> PATH=/usr/bin:/bin TMPDIR=<resolved tmp>/ .venv/bin/python -B -m unittest %s -v", "cwd": "<worktree>", "started_at_utc": "%s", "ended_at_utc": "%s", "exit": %s, "result": "%s", "log": "runs/%s.log", "log_sha256": "%s"}\n' \
  "$label" "$*" "$started" "$ended" "$status" "$summary" "$label" "$digest" >> "$evidence/RUNS.jsonl"
echo "$label exit=$status $started..$ended :: $summary"
