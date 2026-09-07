"""Explicit human/operator commands for key creation and exact gate signing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from .common import OrchiError, read_json, write_json, require
from .signing import keygen, sign


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    key = sub.add_parser("keygen", help="Create an operator-owned Ed25519 keypair without overwriting files")
    key.add_argument("--private", required=True, type=Path)
    key.add_argument("--public", required=True, type=Path)
    approval = sub.add_parser("sign", help="Sign a gate request already reviewed by the human operator")
    approval.add_argument("--request", required=True, type=Path)
    approval.add_argument("--private", required=True, type=Path)
    approval.add_argument("--decision", choices=["approve", "reject"], required=True)
    approval.add_argument("--operator", required=True)
    approval.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "keygen":
            require(args.private.resolve() != args.public.resolve(), "INVALID_KEY_PATH", "Private and public paths must differ")
            for path in (args.private, args.public):
                require(not path.exists() and not path.is_symlink(), "KEY_EXISTS", "Refusing to overwrite " + str(path))
                require(path.parent.is_dir(), "MISSING_DIRECTORY", "Create the operator-owned parent directory first")
            public = keygen(args.private)
            try:
                with args.public.open("x", encoding="utf-8") as handle:
                    handle.write(public)
            except BaseException:
                args.private.unlink()  # Only the key created by this call; existing keys fail preflight.
                raise
            result = {"private_path": str(args.private), "public_path": str(args.public)}
        else:
            request = read_json(args.request)
            if isinstance(request, dict) and set(request) == {"ok", "result"}:
                require(request["ok"] is True, "INVALID_REQUEST", "Cannot sign a failed command result")
                request = request["result"]
            require(isinstance(request, dict) and request.get("format") == "orchi-gate",
                    "INVALID_REQUEST", "Use an exact gate request exported by Orchi")
            require(not args.out.exists() and not args.out.is_symlink(), "OUTPUT_EXISTS", "Use a new decision output path")
            write_json(args.out, sign(request, args.private, args.decision, args.operator))
            result = {"decision": args.decision, "output": str(args.out)}
        print(json.dumps({"ok": True, "result": result}, indent=2))
        return 0
    except (OrchiError, OSError, ValueError, TypeError) as exc:
        print(json.dumps({"ok": False, "code": getattr(exc, "code", "INPUT_ERROR"), "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
