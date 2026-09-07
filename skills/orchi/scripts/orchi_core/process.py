"""Bounded foreground subprocesses. POSIX process groups are killed on all exits."""
from __future__ import annotations
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
from .common import require


def run(argv: list[str], cwd: Path, timeout: int, output_limit: int,
        env: dict[str, str] | None = None, stdin: bytes = b"") -> dict:
    require(bool(argv) and all(isinstance(x, str) for x in argv), "INVALID_COMMAND", "Expected argv, not shell text")
    start = time.monotonic()
    base_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                "PYTHONDONTWRITEBYTECODE": "1", "GIT_TERMINAL_PROMPT": "0"}
    base_env.update(env or {})
    with tempfile.TemporaryFile() as inp, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        inp.write(stdin)
        inp.seek(0)
        proc = subprocess.Popen(argv, cwd=cwd, env=base_env, stdin=inp, stdout=out, stderr=err,
                                start_new_session=(os.name == "posix"))
        stopped = None
        try:
            while proc.poll() is None:
                if time.monotonic() - start > timeout:
                    stopped = "timeout"
                    break
                if os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > output_limit:
                    stopped = "output_limit"
                    break
                time.sleep(0.02)
        finally:
            if os.name == "posix":
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif proc.poll() is None:
                proc.kill()
            proc.wait(timeout=10)
        out.seek(0); err.seek(0)
        stdout, stderr = out.read(output_limit), err.read(output_limit)
        if len(stdout) + len(stderr) > output_limit:
            stopped = "output_limit"
        return {"argv": argv, "returncode": proc.returncode, "stopped": stopped,
                "stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace"),
                "seconds": round(time.monotonic() - start, 4),
                "passed": proc.returncode == 0 and stopped is None}
