from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, Sequence

from msgspec import Struct


class Project(Struct):
    repo: Repo
    subdir: str
    typ: str
    marker_filename: str


class Repo(Struct):
    root: Path
    # TODO restrict to a subdir
    projects: Sequence[Project] = ()
    zfiles: Optional[str] = None

    def __post_init__(self):
        self.zfiles = subprocess.check_output(["git", "ls-files", "-z"], encoding="utf-8", cwd=self.root)


class NullRepo(Struct):
    projects: Sequence[Project] = ()
    zfiles: str = ""
