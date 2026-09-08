"""Exact Git snapshots, no checkout-based source authority and Git hooks disabled; operator-owned checkout filters remain trusted configuration."""
from __future__ import annotations
import os
from functools import lru_cache
import re
import subprocess
import tempfile
from pathlib import Path
from .common import OrchiError, path, require, sha, protected


class Repository:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        require(self.root.is_dir(), "REPOSITORY_NOT_FOUND", str(self.root))
        require(self.git("rev-parse", "--show-object-format").strip() == b"sha1", "GIT_FORMAT", "This profile requires SHA-1 Git repositories")

    def git(self, *args: str, data: bytes | None = None, env: dict | None = None, cwd: Path | None = None) -> bytes:
        e = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        e.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                  "GIT_TERMINAL_PROMPT": "0", "GIT_NO_REPLACE_OBJECTS": "1",
                  "GIT_AUTHOR_NAME": "Orchi", "GIT_AUTHOR_EMAIL": "orchi@localhost",
                  "GIT_COMMITTER_NAME": "Orchi", "GIT_COMMITTER_EMAIL": "orchi@localhost"})
        e.update(env or {})
        p = subprocess.run(["git", "-c", f"core.hooksPath={os.devnull}", "-c", "commit.gpgsign=false", "-c", "core.fsmonitor=false",
                            "-c", "core.quotePath=false", *args], cwd=cwd or self.root, env=e,
                           input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        if p.returncode:
            raise OrchiError("GIT_ERROR", p.stderr.decode(errors="replace")[-2000:])
        return p.stdout

    def resolve(self, ref: str) -> str:
        require(not ref.startswith("-") and "\n" not in ref, "INVALID_REF", ref)
        return self.git("rev-parse", "--verify", ref + "^{commit}").decode().strip()

    @lru_cache(maxsize=512)
    def tree(self, commit: str) -> str:
        return self.git("rev-parse", commit + "^{tree}").decode().strip()

    @lru_cache(maxsize=512)
    def files(self, commit: str) -> dict[str, tuple[str, str]]:
        require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "IMMUTABLE_REF_REQUIRED", "Pass a resolved commit, not a mutable ref")
        result = {}
        for line in self.git("ls-tree", "-rz", "--full-tree", commit).split(b"\x00"):
            if not line:
                continue
            meta, name = line.split(b"\t", 1)
            mode, kind, oid = meta.decode().split()
            result[name.decode("utf-8")] = (mode, oid)
        return result

    @lru_cache(maxsize=4096)
    def read(self, commit: str, name: str) -> bytes:
        name = path(name)
        f = self.files(commit).get(name)
        require(f is not None, "MISSING_SOURCE", f"{name}@{commit}")
        require(f[0] in {"100644", "100755"}, "UNSAFE_SOURCE", f"Not a regular file: {name}")
        size = int(self.git("cat-file", "-s", f[1]))
        require(size <= 8_000_000, "SOURCE_TOO_LARGE", name)
        return self.git("cat-file", "blob", f[1])

    def hashes(self, commit: str, names: list[str]) -> dict[str, str | None]:
        files = self.files(commit)
        return {p: files[p][1] if p in files else None for p in sorted(set(names))}

    def diff(self, a: str, b: str) -> list[str]:
        x, y = self.files(a), self.files(b)
        return sorted(p for p in x.keys() | y.keys() if x.get(p) != y.get(p))

    def blob(self, content: bytes) -> str:
        return self.git("hash-object", "-w", "--stdin", data=content).decode().strip()

    def compose(self, base: str, edits: dict[str, tuple[str, str] | None], message: str) -> str:
        with tempfile.TemporaryDirectory(prefix="orchi-index-") as tmp:
            env = {"GIT_INDEX_FILE": str(Path(tmp) / "index")}
            self.git("read-tree", base, env=env)
            lines = []
            for p, item in sorted(edits.items()):
                path(p)
                if item is None:
                    lines.append(f"0 {'0'*40}\t{p}\0")
                else:
                    require(item[0] in {"100644", "100755"}, "UNSAFE_MODE", p)
                    lines.append(f"{item[0]} {item[1]}\t{p}\0")
            if lines:
                self.git("update-index", "-z", "--index-info", data="".join(lines).encode(), env=env)
            tree = self.git("write-tree", env=env).decode().strip()
        return self.commit(tree, base, message)

    def write(self, base: str, contents: dict[str, bytes | None], message: str) -> str:
        files = self.files(base)
        edits = {p: ((files.get(p, ("100644",))[0], self.blob(v)) if v is not None else None) for p, v in contents.items()}
        return self.compose(base, edits, message)

    def commit(self, tree: str, parent: str, message: str) -> str:
        commit = self.git("commit-tree", tree, "-p", parent, data=(message + "\n").encode()).decode().strip()
        # Keep every immutable candidate reachable even if controller crashes before accepting it.
        self.git("update-ref", f"refs/orchi/keep/{commit}", commit)
        return commit

    def pin(self, label: str, commit: str):
        require(re.fullmatch(r"[a-z0-9./-]+", label) is not None and ".." not in label, "INVALID_REF", label)
        self.git("update-ref", "refs/orchi/" + label, commit)

    def worktree(self, directory: Path, commit: str) -> Path:
        require(not directory.exists() and not directory.is_symlink(), "WORKSPACE_EXISTS", str(directory))
        directory.parent.mkdir(parents=True, exist_ok=True)
        self.git("worktree", "add", "--detach", str(directory), commit)
        return directory

    def snapshot(self, directory: Path, start: str, allowed: set[str]) -> str:
        require(self.git("rev-parse", "HEAD", cwd=directory).decode().strip() == start,
                "WORKER_COMMITTED", "Worker must leave commits and integration to the controller")
        dirty = self.git("diff", "--name-only", "-z", "HEAD", cwd=directory).split(b"\0")
        untracked = self.git("ls-files", "--others", "--exclude-standard", "-z", cwd=directory).split(b"\0")
        changes = sorted({p.decode("utf-8") for p in dirty + untracked if p})
        require(set(changes) <= allowed, "SCOPE_VIOLATION", "Unexpected writes: " + ", ".join(set(changes) - allowed))
        old, edits = self.files(start), {}
        for p in changes:
            path(p)
            require(not protected(p), "PROTECTED_PATH", p)
            f = directory / p
            # Check all components, not just the leaf: an intermediate directory may be a symlink.
            require(not any(q.is_symlink() for q in [f, *list(f.parents)[:len(Path(p).parts)-1]]), "UNSAFE_PATH", p)
            require(f.resolve().is_relative_to(directory.resolve()), "UNSAFE_PATH", p)
            if not f.exists():
                edits[p] = None
            else:
                require(f.is_file() and f.stat().st_size <= 8_000_000, "UNSAFE_FILE", p)
                mode = "100755" if f.stat().st_mode & 0o111 else "100644"
                edits[p] = (mode, self.blob(f.read_bytes()))
        return self.compose(start, edits, "Orchi task candidate")

    def merge_candidate(self, head: str, start: str, candidate: str) -> str:
        changes = self.diff(start, candidate)
        before, current, after = self.files(start), self.files(head), self.files(candidate)
        require(all(before.get(p) == current.get(p) for p in changes), "INTEGRATION_CONFLICT", "Written paths changed since dispatch")
        return self.compose(head, {p: after.get(p) for p in changes}, "Orchi verified integration candidate")

    def patch(self, a: str, b: str, max_bytes: int = 200_000) -> str:
        result = self.git("diff", "--no-ext-diff", "--no-textconv", "--no-renames", a, b)
        if len(result) > max_bytes:
            return "Diff exceeds inline limit. Inspect exact refs with git diff --no-ext-diff --no-textconv " + a + " " + b
        return result.decode("utf-8", errors="replace")

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        ancestor, descendant = self.resolve(ancestor), self.resolve(descendant)
        if ancestor == descendant:
            return True
        try:
            bases = self.git("merge-base", "--all", ancestor, descendant).decode().splitlines()
        except OrchiError as exc:
            # --all returns no merge base for disconnected histories. Resolve above
            # already rejects absent/non-commit inputs; unrelated histories are not an ancestor.
            if exc.code == "GIT_ERROR" and not str(exc).strip():
                return False
            raise
        return ancestor in bases

    def three_way(self, base: str, ours: str, theirs: str) -> tuple[dict, list[str]]:
        """Conservative file-level composition; never silently resolve two changed versions."""
        before, local, upstream = self.files(base), self.files(ours), self.files(theirs)
        edits, conflicts = {}, []
        for name in sorted(before.keys() | local.keys() | upstream.keys()):
            b, o, t = before.get(name), local.get(name), upstream.get(name)
            if o == t or t == b:
                continue
            if o == b:
                edits[name] = t
            else:
                conflicts.append(name)
        return edits, conflicts
