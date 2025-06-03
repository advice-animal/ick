import json
import os
import shutil
import sys
from pathlib import Path
from typing import List

from filelock import FileLock

from .sh import run_cmd


def find_uv() -> Path:
    uv_path = Path(sys.executable).parent / "uv"
    assert uv_path.exists()
    return uv_path


class PythonEnv:
    def __init__(self, env_path: Path, deps: List[str]) -> None:
        self.env_path = env_path
        self.deps = deps

    def bin(self, prog) -> Path:
        """
        Returns a theoretical Path for the given `prog`.

        Does not need to exist yet.
        """
        # TODO scripts and .exe for windows?
        return self.env_path / "bin" / prog

    def _deps_path(self) -> Path:
        return self.env_path / "deps.txt"

    def health_check(self) -> bool:
        py = self.bin("python")
        if not py.exists():
            return False
        try:
            _, returncode = run_cmd([py, "--version"], check=False)
        except PermissionError:
            return False
        if returncode != 0:
            return False

        # Eek, this could happen outside the lock, so be defensive against
        # concurrent modification more than usual
        try:
            deps = self._deps_path().read_text()
        except OSError:
            return False
        return deps == json.dumps(self.deps)

    def prepare(self):
        if self.health_check():
            return True

        with FileLock(self.env_path.with_suffix(".lock")):
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
            )

            # A bit silly to create a venv with no deps, but handle it gracefully
            #
            # This allows us to choose a python version per-env and give a
            # reasonable error during prepare if it's not present/downloadable
            # on the system.
            if self.deps:
                env["VIRTUAL_ENV"] = self.env_path
                run_cmd(
                    [uv, "pip", "install", *self.deps],
                    env=env,
                )
            self._deps_path().write_text(json.dumps(self.deps))
