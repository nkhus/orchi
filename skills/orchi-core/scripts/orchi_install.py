#!/usr/bin/env python3
"""Standard-library installation, registration, and removal from an installed bundle."""
import sys

sys.dont_write_bytecode = True
from orchi_core.installation import main

if __name__ == "__main__":
    raise SystemExit(main())
