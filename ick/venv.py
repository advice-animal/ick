import json
import os
import shutil
import sys
from pathlib import Path

from filelock import FileLock

from .sh import run_cmd, run_cmd_status


def find_uv() -> Path:
    uv_path = Path(sys.executable).parent / "uv"
    assert uv_path.exists()
    return uv_path


class PythonEnv:
    def __init__(self, env_path: Path, deps: list[str] | None) -> None:
        self.env_path = env_path
        self.deps = deps or []
        self._cached_health: bool | None = None

    def bin(self, prog) -> Path:  # type: ignore[no-untyped-def] # FIX ME
        """
        Returns a theoretical Path for the given `prog`.

        Does not need to exist yet.
        """
        # TODO scripts and .exe for windows?
        return self.env_path / "bin" / prog  # type: ignore[no-any-return] # FIX ME

    def _deps_path(self) -> Path:
        return self.env_path / "deps.txt"

    def health_check(self) -> bool:
        # Both None (we don't know) and False (we know it's not working) should
        # cause us to check again...
        if not self._cached_health:
            py = self.bin("python")
            if not py.exists():
                self._cached_health = False
                return self._cached_health
            try:
                _, returncode = run_cmd_status([py, "--version"], check=False)
            except PermissionError:
                self._cached_health = False
                return self._cached_health
            if returncode != 0:
                self._cached_health = False
                return self._cached_health

            # Eek, this could happen outside the lock, so be defensive against
            # concurrent modification more than usual
            try:
                deps = self._deps_path().read_text()
            except OSError:
                self._cached_health = False
                return self._cached_health
            self._cached_health = deps == json.dumps(self.deps)

        assert self._cached_health is not None
        return self._cached_health

    def prepare(self, blocking: bool = True) -> bool:
        """
        Attempt to set up this venv.

        Returns True if it's ready to go.
        Returns False if it's not ready, but we think some other thread is working on it.
        Blocks if we're that thread, then returns True.
        """
        if self.health_check():
            return True

        with FileLock(self.env_path.with_suffix(".lock"), blocking=blocking) as lock:
            if not lock.is_locked:
                return False

            # Double check that we still need to set it up.
            if self.health_check():
                return True

            uv = find_uv()

            if self.env_path.exists():
                shutil.rmtree(self.env_path)
            # TODO: should a rule be able to specify the version of Python it needs?
            # If it's not on the system should it download?
            python_exe = sys.executable

            # Important: env is intended to inherit some stuff from the system
            # here, like $HOME to find your uv.toml configuring mirrors, or
            # other vars including $UV_NATIVE_TLS.
            #
            # Setting UV_SYSTEM_PYTHON=1 without setting PATH causes
            # hard-to-debug failures, so only inherit a couple for now.
            env = {}
            for k, v in os.environ.items():
                if k in ("HOME", "UV_CACHE_DIR", "UV_NATIVE_TLS") or k.startswith("XDG_"):
                    env[k] = v

            run_cmd(
                [uv, "venv", "--python", python_exe, self.env_path],
                env=env,
                timeout=10,
            )

            # A bit silly to create a venv with no deps, but handle it gracefully
            #
            # This allows us to choose a python version per-env and give a
            # reasonable error during prepare if it's not present/downloadable
            # on the system.
            if self.deps:
                env["VIRTUAL_ENV"] = self.env_path  # type: ignore[assignment] # FIX ME
                run_cmd(
                    [uv, "pip", "install", *self.deps],
                    env=env,
                )
            self._deps_path().write_text(json.dumps(self.deps))
            self._cached_health = None
        return True
