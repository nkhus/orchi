"""Operator approvals: signed exact requests, separate from worker permissions."""
from __future__ import annotations
import base64
import os
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from .common import canonical, require, OrchiError


def keygen(private_path: Path) -> str:
    require(not private_path.exists(), "KEY_EXISTS", "Refusing to overwrite an operator key")
    k = Ed25519PrivateKey.generate()
    data = k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    fd = os.open(private_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return k.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()


def sign(request: dict, key: Path, decision: str, operator: str) -> dict:
    require(decision in {"approve", "reject"} and bool(operator.strip()), "INVALID_DECISION", "Specify decision and operator")
    require(not key.is_symlink(), "UNSAFE_KEY", "Do not use a key symlink")
    k = serialization.load_pem_private_key(key.read_bytes(), password=None)
    require(isinstance(k, Ed25519PrivateKey), "INVALID_KEY", "Use Ed25519")
    body = {"request": request, "decision": decision, "operator": operator}
    return {**body, "signature": base64.b64encode(k.sign(canonical(body))).decode()}


def verify(request: dict, approval: dict, public_pem: str):
    require(set(approval) == {"request", "decision", "operator", "signature"}, "INVALID_APPROVAL", "Unexpected approval fields")
    require(approval["request"] == request, "STALE_APPROVAL", "Approval does not match the pending exact request")
    require(approval["decision"] in {"approve", "reject"} and bool(approval["operator"].strip()), "INVALID_APPROVAL", "Invalid decision")
    try:
        key = serialization.load_pem_public_key(public_pem.encode())
        require(isinstance(key, Ed25519PublicKey), "INVALID_KEY", "Use Ed25519")
        body = {k: approval[k] for k in ("request", "decision", "operator")}
        key.verify(base64.b64decode(approval["signature"], validate=True), canonical(body))
    except (InvalidSignature, ValueError, TypeError) as e:
        raise OrchiError("BAD_SIGNATURE", "Invalid operator signature") from e
