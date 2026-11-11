"""Absolute, isolated entry points for the selected C199 static-tray adapter."""
from __future__ import annotations

import sys

# This executes before importing any repository package. -B alone does not
# suppress reads of existing bytecode; the source-only checkout rejects it.
if __name__ == "__main__":
    if not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
        sys.stderr.write('{"passed":false,"code":"OTRAY-E-BINDING","reason":"Use the locked host interpreter with -IBS"}\n')
        raise SystemExit(2)
    from pathlib import Path
    _root = Path(__file__).resolve().parents[2]
    _parent = _root / "prototypes"
    _parent_caches = [_parent / "__init__.pyc", _parent / "__init__.pyo", *(_parent / "__pycache__").glob("__init__.*")]
    if any(p.is_file() and p.suffix in {".pyc", ".pyo"} for p in _parent_caches):
        sys.stderr.write('{"passed":false,"code":"OTRAY-E-BINDING","reason":"Unbound parent initializer bytecode prevents source-only bootstrap"}\n')
        raise SystemExit(2)
    for _relative in ("ontokin", "prototypes/static_tray_v01", "tools/static_tray_reader_v01"):
        if any(p.suffix in {".pyc", ".pyo"} for p in (_root / _relative).rglob("*")):
            sys.stderr.write('{"passed":false,"code":"OTRAY-E-BINDING","reason":"Unbound repository bytecode cache prevents source-only bootstrap"}\n')
            raise SystemExit(2)
    sys.path.insert(0, str(_root))

import argparse
import json
from pathlib import Path

from prototypes.static_tray_v01.canonical import decode_record, record_identity
from prototypes.static_tray_v01.errors import PROFILE, TrayError
from prototypes.static_tray_v01.lock import build_lock, read_json, verify_lock
from prototypes.static_tray_v01.sources import lower_source
from prototypes.static_tray_v01.supervisor import Clock, Stop
from prototypes.static_tray_v01.transaction import alarm_until, run_transaction, write_new


def validate(args):
    clock = Clock(total_ms=30000)
    result = {"schema": "ontokin.static-tray.validation/0.1.0", "passed": False, "native_starts": 0,
              "receiving_starts": 0, "source_budget": {"max_operations": 100000, "max_elapsed_ms": 30000}}
    try:
        with alarm_until(clock, clock.end):
            if args.profile != PROFILE:
                raise TrayError("PROFILE", "An exact explicit mapping selector is required.", stage="selector")
            if args.record:
                path = Path(args.record)
                if path.is_symlink() or not path.is_file():
                    raise TrayError("RECORD", "Canonical input must be a regular nonsymlink file.", stage="record")
                with path.open("rb") as stream:
                    data = stream.read(32769)
                record = decode_record(data)
                result.update(record=record, canonical_record_identity=record_identity(data))
            else:
                manifest = read_json(args.source, 32768)
                route = args.route
                if route is None:
                    route = {"ontokin.files/0.1": "ontokin", "ontokin.static-tray.python-sources/0.1.0": "direct-python"}.get(manifest.get("schema_version"))
                lowered = lower_source(route, args.source, args.profile, check=clock.check)
                result.update(record=lowered.record, provenance=lowered.provenance, route=route)
            clock.check()
            result["passed"] = True
    except (Stop, TrayError, OSError, ValueError) as exc:
        result["error"] = exc.to_dict() if isinstance(exc, TrayError) else exc.as_dict() if isinstance(exc, Stop) else {"code": "OTRAY-E-CLOSURE", "reason": str(exc)}
    result["elapsed_ms"] = clock.elapsed_ms()
    write_new(args.result, result)
    return result


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    v = commands.add_parser("validate", help="Bounded source or canonical record validation; no native process")
    v.add_argument("--profile", required=True)
    source = v.add_mutually_exclusive_group(required=True)
    source.add_argument("--source")
    source.add_argument("--record")
    v.add_argument("--route", choices=["ontokin", "direct-python"])
    v.add_argument("--result", required=True)
    r = commands.add_parser("run", help="One independently approved assigned native transaction")
    r.add_argument("--route", required=True, choices=["ontokin", "direct-python"])
    for name in ("source", "lock", "slot", "store", "result"):
        r.add_argument("--" + name, required=True)
    r.add_argument("--cancel-file")
    seal = commands.add_parser("seal-inputs", help="Freeze actual committed input bytes; does not approve execution")
    for name in ("output", "schedule-root", "blender-root", "blender-archive", "distribution-inventory", "host-inventory", "format-manifest"):
        seal.add_argument("--" + name, required=True)
    readback = commands.add_parser("seal-readback", help="Pin the supplemental Khronos/Three.js dependency closure and twelve read-only slots")
    for name in ("output", "node", "dependencies-root", "schedule-root", "host-inventory"):
        readback.add_argument("--" + name, required=True)
    verify = commands.add_parser("verify-inputs", help="Read-only full input verification; no native process")
    verify.add_argument("--lock", required=True)
    verify.add_argument("--without-approval", action="store_true")
    verify.add_argument("--result", required=True)
    qualify = commands.add_parser("qualify", help="Run the immutable twelve-slot schedule once, stopping at the first unexpected result")
    qualify.add_argument("--lock", required=True)
    life = commands.add_parser("lifecycle-control", help="Reserved interface; the reviewed L-R1 amendment owns its exact coordinator")
    life.add_argument("--case", required=True)
    life.add_argument("--lock", required=True)
    life.add_argument("--result", required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "validate":
            result = validate(args)
        elif args.command == "run":
            result = run_transaction(args.lock, args.slot, route=args.route, source=args.source, store=args.store,
                                     result_path=args.result, cancel_file=args.cancel_file)
        elif args.command == "seal-inputs":
            lock, digest = build_lock(args.output, schedule_root=args.schedule_root, blender_root=args.blender_root,
                blender_archive=args.blender_archive, distribution_inventory=args.distribution_inventory, host_inventory=args.host_inventory,
                format_manifest=args.format_manifest)
            result = {"passed": True, "input_lock_sha256": digest, "slots": len(lock["slots"]), "approval_created": False,
                      "native_starts": 0, "receiving_starts": 0}
        elif args.command == "seal-readback":
            from prototypes.static_tray_v01.format_check import build_manifest
            manifest, digest = build_manifest(args.output, node=args.node, dependencies_root=args.dependencies_root,
                schedule_root=args.schedule_root, host_inventory=args.host_inventory)
            result = {"passed": True, "supplemental_manifest_sha256": digest, "read_only_slots": len(manifest["slots"]),
                      "checker_starts": 0, "native_starts": 0, "approval_created": False}
        elif args.command == "verify-inputs":
            clock = Clock(total_ms=30000)
            with alarm_until(clock, clock.end):
                lock, digest = verify_lock(args.lock, approval=not args.without_approval, check=clock.check)
            result = {"passed": True, "input_lock_sha256": digest, "elapsed_ms": clock.elapsed_ms(),
                      "approval_required": not args.without_approval, "native_starts": 0, "receiving_starts": 0}
            write_new(args.result, result)
        elif args.command == "qualify":
            from prototypes.static_tray_v01.qualification import run_qualification
            result = run_qualification(args.lock, progress=lambda row: print(json.dumps(row, sort_keys=True), flush=True))
        else:
            result = {"passed": False, "native_starts": 0, "direct_child_starts": 0,
                      "error": {"code": "OTRAY-E-BINDING", "reason": "The separate reviewed C199 L-R1 amendment and run_lifecycle.py coordinator own all lifecycle slots. This interface cannot start additional controls."}}
            write_new(args.result, result)
        summary = {k: result[k] for k in ("passed", "state", "status", "slot", "native_starts", "receiving_starts", "input_lock_sha256", "supplemental_manifest_sha256", "error") if k in result}
        print(json.dumps(summary, sort_keys=True, allow_nan=False), flush=True)
        return 0 if result.get("passed") is True or result.get("state") == "ACCEPTED" or result.get("measured_gates_passed") is True else 1
    except (Stop, TrayError, OSError, ValueError, KeyError) as exc:
        result = {"passed": False, "native_starts": 0,
                  "error": exc.as_dict() if isinstance(exc, Stop) else exc.to_dict() if isinstance(exc, TrayError) else {"code": "OTRAY-E-BINDING", "reason": type(exc).__name__ + ": " + str(exc)}}
        # Each new requested result is retained; a prior result is never replaced.
        output = getattr(args, "result", None)
        if output and not Path(output).exists():
            write_new(output, result)
        print(json.dumps(result, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
