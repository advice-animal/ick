import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

from filelock import FileLock


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
            subprocess.check_output([py, "--version"])
        except subprocess.CalledProcessError:
            return False
        except PermissionError:
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
            subprocess.check_output([uv, "venv", self.env_path], env={"UV_PYTHON_PREFERENCE": "system"}, stderr=subprocess.STDOUT)

            # A bit silly to create a venv with no deps, but handle it gracefully
            #
            # This allows us to choose a python version per-env and give a
            # reasonable error during prepare if it's not present/downloadable
            # on the system.
            if self.deps:
                subprocess.check_output([uv, "pip", "install", *self.deps], env={"VIRTUAL_ENV": self.env_path}, stderr=subprocess.STDOUT)
            self._deps_path().write_text(json.dumps(self.deps))
