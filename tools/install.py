#!/usr/bin/env python3
"""Install the self-contained Orchi bundle without application dependencies."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/orchi/scripts"))
from orchi_core.installation import NAMES, install, inventory, main, shutil

if __name__ == "__main__":
    raise SystemExit(main())
