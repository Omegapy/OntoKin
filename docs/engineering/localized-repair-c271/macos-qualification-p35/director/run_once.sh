#!/bin/sh
# Director's single-run wrapper for gate MH (C271-P35), FAILURE-CAPTURE FC-K2 and FC-K3.
# Usage: run_once.sh NAME CWD ENVFILE -- ARGV...
# Runs ARGV once in CWD, never again. It writes, by exclusive creation beside the attempt:
#   <evidence>/NAME.stdout.txt, NAME.stderr.txt, NAME.exit.txt and NAME.command.json.
# It refuses before any start when one of them exists. It starts no Python and retries nothing.
set -u
set -C
E=<local>/c271-p35/evidence
name="$1"; cwd="$2"; envfile="$3"; shift 3
[ "$1" = "--" ] || { echo "run_once: expected --" >&2; exit 90; }
shift
for s in stdout.txt stderr.txt exit.txt command.json; do
  if [ -e "$E/$name.$s" ] || [ -L "$E/$name.$s" ]; then echo "run_once: present $E/$name.$s" >&2; exit 90; fi
done
envsha=$(/usr/bin/shasum -a 256 "$envfile" | /usr/bin/cut -c1-64)
boot_before=$(/usr/sbin/sysctl -n kern.bootsessionuuid)
start_utc=$(/bin/date -u +%Y-%m-%dT%H:%M:%SZ)
t0=$(/usr/bin/perl -MTime::HiRes=time -e 'printf "%.6f", time')
( cd "$cwd" && exec "$@" ) > "$E/$name.stdout.txt" 2> "$E/$name.stderr.txt"
status=$?
t1=$(/usr/bin/perl -MTime::HiRes=time -e 'printf "%.6f", time')
end_utc=$(/bin/date -u +%Y-%m-%dT%H:%M:%SZ)
boot_after=$(/usr/sbin/sysctl -n kern.bootsessionuuid)
printf '%s\n' "$status" > "$E/$name.exit.txt"
wall=$(/usr/bin/perl -e "printf '%.6f', $t1 - $t0")
/usr/bin/jq -n --arg schema "ontokin.c271.p35-command-record/1" --arg name "$name" --arg cwd "$cwd" \
  --arg envfile "$envfile" --arg envsha "$envsha" --arg start "$start_utc" --arg end "$end_utc" \
  --arg t0 "$t0" --arg t1 "$t1" --arg wall "$wall" --arg bb "$boot_before" --arg ba "$boot_after" \
  --arg status "$status" \
  --arg so "$E/$name.stdout.txt" --arg se "$E/$name.stderr.txt" --arg ex "$E/$name.exit.txt" \
  --arg sosha "$(/usr/bin/shasum -a 256 "$E/$name.stdout.txt" | /usr/bin/cut -c1-64)" \
  --arg sesha "$(/usr/bin/shasum -a 256 "$E/$name.stderr.txt" | /usr/bin/cut -c1-64)" \
  --arg sosize "$(/usr/bin/stat -f %z "$E/$name.stdout.txt")" --arg sesize "$(/usr/bin/stat -f %z "$E/$name.stderr.txt")" \
  '{schema: $schema, name: $name, argv: $ARGS.positional, cwd: $cwd,
    environment: {file: $envfile, sha256: $envsha},
    started_at_utc: $start, ended_at_utc: $end, start_epoch_s: $t0, end_epoch_s: $t1, wall_time_s: $wall,
    boot: {before: $bb, after: $ba},
    exit: {status: ($status | tonumber)},
    streams: {stdout: {path: $so, sha256: $sosha, size_bytes: ($sosize | tonumber)},
              stderr: {path: $se, sha256: $sesha, size_bytes: ($sesize | tonumber)},
              exit: {path: $ex}},
    retries: 0, written_by: "director/run/run_once.sh"}' --args "$@" > "$E/$name.command.json"
echo "run_once: $name exit=$status wall=${wall}s boot_before=$boot_before boot_after=$boot_after"
exit 0
