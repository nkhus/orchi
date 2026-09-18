#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic==2.13.4", "cryptography==46.0.4", "PyYAML==6.0.3"]
# ///
"""Human-operated signing tools. Never give a worker access to the private key."""
import sys
sys.dont_write_bytecode = True
from orchi_core.operator_cli import main

if __name__ == "__main__":
    raise SystemExit(main())
