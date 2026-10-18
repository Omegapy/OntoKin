#!/usr/bin/env python3
"""Run the explicit adopted impulse-0.1 acceptance and evidence gate."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ontokin.impulse_conformance import main

if __name__ == "__main__":
    raise SystemExit(main())
