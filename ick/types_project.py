from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

from msgspec import Struct

from .sh import run_cmd


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
        self.zfiles, _ = run_cmd(["git", "ls-files", "-z"], cwd=self.root)


class NullRepo(Struct):
    projects: Sequence[Project] = ()
    zfiles: str = ""
