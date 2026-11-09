"""Command-line entry point for the observation development workflow."""
import argparse
import json
from pathlib import Path
import sys

from .observation import ADAPTERS, import_observation, load_observation


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    ingest = commands.add_parser("import", help="normalize a model's local NPZ export")
    ingest.add_argument("adapter", choices=ADAPTERS)
    ingest.add_argument("source", type=Path)
    ingest.add_argument("output", type=Path)
    ingest.add_argument("--fps", type=float, help="assert a uniformly sampled chronological sequence")
    ingest.add_argument("--checkpoint", help="user-supplied model checkpoint identity")
    ingest.add_argument("--capture", help="user-supplied capture identifier")
    ingest.add_argument("--source-kind", choices=("provided", "published", "synthetic"), default="provided")
    check = commands.add_parser("inspect", help="verify the bundle and display its manifest")
    check.add_argument("observation", type=Path)
    point = commands.add_parser("point", help="unproject a Solv3R pixel and compare another view")
    point.add_argument("observation", type=Path)
    for key in ("view", "u", "v"):
        point.add_argument(key, type=int)
    point.add_argument("--target-view", type=int)
    fit = commands.add_parser("synthesize", help="fit, execute and test an editable root-motion action")
    fit.add_argument("observation", type=Path)
    fit.add_argument("output", type=Path)
    fit.add_argument("--start-frame", type=int, default=0)
    fit.add_argument("--stop-frame", type=int, help="exclusive upper bound")
    fit.add_argument("--max-error-m", type=float, default=0.025)
    run = commands.add_parser("run-worker", help="run an already configured external model and import its result")
    run.add_argument("adapter", choices=ADAPTERS)
    run.add_argument("media", type=Path)
    run.add_argument("output", type=Path)
    for key in ("checkout", "python", "checkpoint"):
        run.add_argument("--" + key, type=Path, required=True)
    run.add_argument("--timeout-s", type=int, default=1800)
    run.add_argument("--static-camera", action="store_true")
    args = vars(parser.parse_args(argv))
    operation = args.pop("operation")
    try:
        if operation == "import":
            result = import_observation(**args)
        elif operation == "inspect":
            result, _ = load_observation(args["observation"])
        elif operation == "point":
            from .geometry import inspect_point
            result = inspect_point(**args)
        elif operation == "synthesize":
            from .synthesis import synthesize
            result = synthesize(args.pop("observation"), args.pop("output"), **args)
        else:
            from .worker import run_worker
            result = run_worker(**args)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    except (ValueError, OSError) as error:
        print(f"Observation workflow: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
