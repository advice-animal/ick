from __future__ import annotations

from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Callable, ContextManager, Iterable, Sequence, TypeVar

from msgspec import Struct

from .sh import run_cmd

_T = TypeVar("_T")


class Project(Struct):
    repo: BaseRepo
    subdir: str
    typ: str
    marker_filename: str

    def relative_filenames(self) -> Iterable[str]:
        zfiles = self.repo.zfiles
        if zfiles is None:
            return []
        filenames = zfiles.rstrip("\0").split("\0")
        assert "" not in filenames
        if self.subdir:
            filenames = [f[len(self.subdir) :] for f in filenames if f.startswith(self.subdir)]
        return filenames


class BaseRepo(Struct):
    root: Path
    projects: Sequence[Project] = ()
    zfiles: str = ""


class Repo(BaseRepo):
    # TODO restrict to a subdir

    def __post_init__(self) -> None:
        self.zfiles = run_cmd(["git", "ls-files", "-z"], cwd=self.root)


def maybe_repo(path: Path, enter_context: Callable[[ContextManager[_T]], _T], for_testing: bool = False) -> BaseRepo:
    # TODO subdir-as-a-project?
    if (path / ".git").exists():
        return Repo(path)
    elif for_testing:
        td = enter_context(TemporaryDirectory())  # type: ignore[arg-type] # FIX ME
        run_cmd(["git", "init"], cwd=td)  # type: ignore[arg-type] # FIX ME
        copytree(path, td, dirs_exist_ok=True)  # type: ignore[arg-type] # FIX ME
        run_cmd(["git", "add", "-N", "."], cwd=td)  # type: ignore[arg-type] # FIX ME
        run_cmd(["git", "commit", "-a", "--allow-empty", "-m", "init"], cwd=td)  # type: ignore[arg-type] # FIX ME
        return Repo(Path(td))  # type: ignore[arg-type] # FIX ME
    else:
        # Basically pretends to be empty, but if you try to clone_aside it will raise
        return BaseRepo(path)
