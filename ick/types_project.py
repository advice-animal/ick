from __future__ import annotations

from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Callable, ContextManager, Optional, Sequence, TypeVar

from msgspec import Struct

from .sh import run_cmd

_T = TypeVar("_T")


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


def maybe_repo(path: Path, enter_context: Callable[[ContextManager[_T]], _T]) -> Repo:
    # TODO subdir-as-a-project?
    if (path / ".git").exists():
        return Repo(path)
    else:
        td = enter_context(TemporaryDirectory())
        run_cmd(["git", "init"], cwd=td)
        copytree(path, td, dirs_exist_ok=True)
        run_cmd(["git", "add", "-N", "."], cwd=td)
        run_cmd(["git", "commit", "-a", "--allow-empty", "-m", "init"], cwd=td)
        return Repo(Path(td))
