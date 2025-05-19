"""
A better `tempfile` that finds a temp dir on the same device as another.

This helps with performance on both `git clone` and `uv pip` because you can
use reflink (or hardlinks) instead of actually having to copy data.

We are unlikely to accidentally return a path on a tiny ramdisk, under the
assumption your checkout or uv cache are already on a largish disk.
"""

import os
import os.path
import tempfile
from contextlib import contextmanager
from pathlib import Path

import appdirs

HARDCODED_DEFAULTS = [
    os.getenv("TMPDIR") or "/tmp",
    # these are presumed to be relative to repo root
    ".tox",
    ".git",
]


class NoValidTempDir(Exception):
    pass


@contextmanager
def in_tmpdir(near: Path):
    d = find_tmpdir(near)
    old = os.getcwd()
    try:
        with tempfile.TemporaryDirectory(dir=d) as td:
            os.chdir(td)
            yield
    finally:
        os.chdir(old)


# These two exist to make mocking easier.
def _access_ok(p: Path) -> bool:
    return os.access(p, os.W_OK)


def _get_device(p: Path) -> int:
    return p.stat().st_dev


def find_tmpdir(near: Path) -> Path:
    desired_dev = _get_device(near)
    user_cache = Path(appdirs.user_cache_dir("ick", "advice-animal"))
    user_cache.mkdir(exist_ok=True, parents=True)
    if _get_device(user_cache) == desired_dev and _access_ok(user_cache):
        return user_cache

    # Try some others before giving up
    for other in HARDCODED_DEFAULTS:
        if not other:
            continue
        path = Path(other)
        try:
            if _get_device(path) == desired_dev and _access_ok(path):
                return path
        except FileNotFoundError:
            pass
    raise NoValidTempDir


if __name__ == "__main__":
    print(find_tmpdir(Path()))
