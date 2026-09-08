"""Small shared primitives; no repository code is imported."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


class OrchiError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise OrchiError(code, message)


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def path(value: str) -> str:
    require(isinstance(value, str) and bool(value), "UNSAFE_PATH", "Expected a nonempty relative path")
    p = PurePosixPath(value)
    require(not p.is_absolute() and "\\" not in value and not any(ord(c) < 32 for c in value),
            "UNSAFE_PATH", f"Invalid path: {value!r}")
    require(all(s not in ("", ".", "..") for s in value.split("/")), "UNSAFE_PATH", f"Noncanonical path: {value}")
    require(not any(c in value for c in "*?[]:") and not value.startswith(("~", "-")),
            "UNSAFE_PATH", f"Only exact repository paths are accepted: {value}")
    return value


def is_core(value: str) -> bool:
    return value.startswith("docs/")


def secret_path(value: str) -> bool:
    parts = value.lower().split("/")
    return any(p.startswith(".env") or p in {"secrets", "credentials", ".ssh", ".aws"} for p in parts) or value.lower().endswith((".pem", ".key", ".p12"))


def protected(value: str) -> bool:
    parts = value.split("/")
    return (is_core(value) or secret_path(value) or
            any(p in {".git", ".agents", ".codex", ".github", ".gitmodules", ".gitattributes", "AGENTS.md", "AGENTS.override.md"} for p in parts) or
            value.startswith(("initiatives/", "changes/", "history/")))


def core_target(value: str) -> str:
    value = path(value)
    require(is_core(value) and value.endswith(".md") and not secret_path(value), "INVALID_KNOWLEDGE_TARGET", value)
    return value


def safe_text(data: bytes, label: str, limit: int = 512_000) -> str:
    require(len(data) <= limit, "SOURCE_TOO_LARGE", label)
    try:
        text = data.decode("utf-8")
    except UnicodeError as e:
        raise OrchiError("BINARY_CONTEXT", label) from e
    require("\x00" not in text, "BINARY_CONTEXT", label)
    # Conservative recognizers, not a DLP guarantee. Do not echo secret content.
    require(not re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{30,}", text),
            "SECRET_IN_CONTEXT", label)
    return text


def read_json(file: str | Path) -> Any:
    p = Path(file)
    require(not p.is_symlink(), "UNSAFE_PATH", "JSON input must not be a symlink")
    return json.loads(safe_text(p.read_bytes(), str(p), 8_000_000))


def write_json(file: str | Path, value: Any) -> None:
    p = Path(file)
    p.parent.mkdir(parents=True, exist_ok=True)
    require(not p.is_symlink(), "UNSAFE_PATH", str(p))
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def integration_base(state: dict) -> str:
    """The original baseline never changes; this is the last accepted upstream snapshot."""
    return state.get("integration_base") or state["baseline"]
