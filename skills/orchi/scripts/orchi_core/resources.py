"""Explicit same-host shared-check exclusion, not a distributed lease service."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import time
from .common import digest, require


@contextmanager
def acquire(policy, names: list[str]):
    if not names:
        yield
        return
    require(policy.resource_directory is not None, "RESOURCE_DIRECTORY_REQUIRED", "Configure a common operator-owned directory")
    root = Path(policy.resource_directory)
    require(not any(p.is_symlink() for p in [root, *root.parents]), "UNSAFE_PATH", "Resource lock directory must not be symlinked")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    handles = []
    deadline = time.monotonic() + policy.resource_wait_seconds
    try:
        # A fixed order avoids cycles when a check needs several resources.
        for name in sorted(set(names)):
            descriptor = os.open(root / (digest({"resource": name}) + ".lock"),
                                 os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
            handles.append(descriptor)
            while True:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    require(time.monotonic() < deadline, "RESOURCE_BUSY", "Timed out waiting for named check resource: " + name)
                    time.sleep(0.05)
        yield
    finally:
        for descriptor in reversed(handles):
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
