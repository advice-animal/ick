import shutil
import subprocess
import sys
from pathlib import Path

from filelock import FileLock


def find_uv() -> Path:
    uv_path = Path(sys.executable).parent / "uv"
    assert uv_path.exists()
    return uv_path


class PythonEnv:
    def __init__(self, env_path: Path, deps):
        self.env_path = env_path
        self.deps = deps

    def bin(self, prog):
        # TODO scripts and .exe for windows?
        return self.env_path / "bin" / prog

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
        else:
            return True

    def prepare(self):
        with FileLock(self.env_path.with_suffix(".lock")):
            uv = find_uv()
            if not self.health_check():
                if self.env_path.exists():
                    shutil.rmtree(self.env_path)
                # TODO selection of python
                subprocess.check_output([uv, "venv", self.env_path], env={"UV_PYTHON_PREFERENCE": "system"})
            # A bit silly to create a venv with no deps, but handle it gracefully
            if self.deps:
                subprocess.check_output([uv, "pip", "install", *self.deps], env={"VIRTUAL_ENV": self.env_path})
