#!/usr/bin/env python3
"""Run the fixed source surface acceptance mapping; missing evidence stays pending.

Examples:
  python tools/run_surface_conformance.py --output results/surface.json
  python tools/run_surface_conformance.py --allow-pending --output results/ci.json
  python tools/run_surface_conformance.py --full-suite-only --output results/tests.json
  python tools/run_surface_conformance.py --external-evidence release.json \
      --evidence-root evidence --output results/release.json

Exit 1 means an executed test failed or evidence changed during execution; exit 2
means selected requirements still need external evidence. --allow-pending only
changes exit 2 for a CI pre-attestation run; it never changes recorded statuses.
The versioned exact release/full-suite/CI record formats and predetermined
fixture/capture requirements are in surface-v0.1/conformance.json.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin.surface_conformance import main

if __name__ == "__main__":
    raise SystemExit(main())
