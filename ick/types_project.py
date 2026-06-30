from __future__ import annotations

from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Callable, ContextManager, Iterable, Optional, Sequence, TypeVar

from msgspec import Struct, field

from .config.project_config import ProjectConfig
from .sh import run_cmd, run_cmd_status

_T = TypeVar("_T")


class Project(Struct):
    repo: BaseRepo
    subdir: str
    typ: str
    marker_filename: str
    config: ProjectConfig = field(default_factory=ProjectConfig)

    def relative_filenames(self) -> Iterable[str]:
        zfiles = self.repo.zfiles
        if zfiles is None:
            return []
        filenames = zfiles.rstrip("\0").split("\0")
        assert "" not in filenames
        if self.subdir:
            filenames = [f[len(self.subdir) :] for f in filenames if f.startswith(self.subdir)]
        return filenames


def root_project(projects: Sequence[Project]) -> Optional[Project]:
    """
    Return the project whose subdir is the repo root (``""``), or ``None``.

    Used by REPO-scoped rules to look up a project config.  The choice of the
    root project is somewhat arbitrary: if the repo contains multiple
    top-level projects (e.g. a Python project at ``""`` and another at
    ``lib/``), they all share the repo root but only the one with
    ``subdir == ""`` is consulted.

    Two draft behaviors interact here and are subject to change:

    * ``skip_project_root_in_repo_root`` (main config): when set, the root
      project is excluded from ``find_projects`` entirely, so this returns
      ``None`` and REPO rules get no project config at all.
    * How intermediate project configs (for nested projects) should merge with
      the root config for the purposes of REPO-scoped rules is not yet defined.
    """
    return next((p for p in projects if p.subdir == ""), None)


class BaseRepo(Struct):
    root: Path
    projects: Sequence[Project] = ()
    zfiles: str = ""
    upstream_url: str = ""


class Repo(BaseRepo):
    # TODO restrict to a subdir

    def __post_init__(self) -> None:
        self.zfiles = run_cmd(["git", "ls-files", "-z"], cwd=self.root)
        url, rc = run_cmd_status(["git", "config", "--get", "remote.upstream.url"], check=False, cwd=self.root)
        if rc != 0:
            url, rc = run_cmd_status(["git", "config", "--get", "remote.origin.url"], check=False, cwd=self.root)
        self.upstream_url = url.strip() if rc == 0 else ""


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
