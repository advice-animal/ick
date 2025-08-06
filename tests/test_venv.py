import os
import subprocess
from pathlib import Path

from ick.venv import PythonEnv, find_uv


def test_find_uv() -> None:
    assert os.access(find_uv(), os.X_OK)


def test_env_happy_path(tmp_path: Path) -> None:
    p = PythonEnv(tmp_path, [])
    pybin = p.bin("python")
    assert not pybin.exists()
    assert not p.health_check()

    p.prepare()
    assert pybin.exists()
    assert p.health_check()

    evil_python = pybin.with_suffix(".tmp")
    evil_python.write_bytes(b"#! /usr/bin/false\n")
    os.replace(evil_python, pybin)
    assert pybin.exists()
    assert not os.access(pybin, os.X_OK)
    p._cached_health = None
    assert not p.health_check()

    pybin.chmod(0o755)
    assert pybin.exists()
    assert os.access(pybin, os.X_OK)
    assert not p.health_check()

    p.prepare()
    assert p.health_check()

    # cover one last line where prepare is a no-op
    p.prepare()


def test_env_with_deps(tmp_path: Path) -> None:
    p = PythonEnv(tmp_path, ["ast-grep-cli"])
    p.prepare()
    assert p.bin("ast-grep").exists()
    subprocess.check_output([p.bin("ast-grep"), "--version"])
