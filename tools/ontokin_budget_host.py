#!/usr/bin/env python3
"""Example operator-controlled launcher for source 0.7 execution budgets.

Install or expose this launcher only where this host policy is authorized.
Source code and command arguments cannot change these independently set ceilings.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ontokin.cli import main
from ontokin.execution_budget import HostPolicy


if __name__ == "__main__":
    raise SystemExit(main(host_policy=HostPolicy(400000, 80000,
                                               "example-workshop-400k-80s")))
