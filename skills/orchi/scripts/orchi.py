#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic==2.13.4", "cryptography==46.0.4", "PyYAML==6.0.3"]
# ///
"""Run Orchi with `uv run /path/to/orchi/scripts/orchi.py`."""
import sys
sys.dont_write_bytecode = True
from orchi_core.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
