from __future__ import annotations

import sys
from logging import basicConfig, getLogger
from pathlib import Path

from vmodule import DEFAULT_FORMAT, VLOG_1, VLOG_2

from ._regex_translate import zfilename_re
from .config import MainConfig, load_main_config
from .types_project import Project, Repo

LOG = getLogger(__name__)


def find_projects(repo: Repo, zstr: str, conf: MainConfig) -> list[Project]:
    """
    Returns topmost projects
    """
    marker_to_type = {}
    for k, v in conf.project_root_markers.items():  # type: ignore[union-attr] # FIX ME
        for i in v:
            marker_to_type[i] = k
    pat = zfilename_re(marker_to_type)
    LOG.info("Looking for projects in %r", repo.root)
    LOG.log(VLOG_2, "Project root re is %r", pat.pattern)

    projects: dict[tuple[str, str], Project] = {}

    for match in pat.finditer(zstr):
        dirname, filename = match.groups()
        typ = marker_to_type[filename]
        if dirname == "" and conf.skip_project_root_in_repo_root:
            LOG.log(VLOG_1, "Skipping root project with marker %r because config says to", filename)
            continue
        elif conf.explicit_project_dirs and dirname not in conf.explicit_project_dirs:
            LOG.log(VLOG_1, "Skipping project with marker %r because it is not in explicit_project_dirs", dirname)
            continue
        elif conf.ignore_project_dirs and dirname in conf.ignore_project_dirs:
            LOG.log(VLOG_1, "Skipping project at %r because it is ignored by config", dirname)
            continue

        key = (dirname, typ)
        if key not in projects:
            LOG.log(VLOG_1, "Found new %r project at %r with marker %r", typ, dirname, filename)
            projects[key] = Project(repo, dirname, typ, filename)

    # this is a tuple to make .startswith happy
    final_project_names: tuple[str] = ()  # type: ignore[assignment] # FIX ME
    final_projects: list[Project] = []

    for project in sorted(projects.values(), key=lambda p: (p.subdir.count("/"), p.subdir)):
        if project.subdir.startswith(final_project_names) and project.subdir not in final_project_names:
            LOG.log(
                VLOG_1,
                "Skipping project at %r with marker %r because it is subordinate",
                project.subdir,
                project.marker_filename,
            )
            continue
        else:
            LOG.debug("Keeping project at %r", project.subdir)
        final_projects.append(project)
        final_project_names = (*final_project_names, project.subdir)  # type: ignore[assignment] # FIX ME

    return final_projects


if __name__ == "__main__":  # pragma: no cover
    from .main import repo_root  # type: ignore[import-not-found] # FIX ME

    basicConfig(level=VLOG_2, format=DEFAULT_FORMAT)
    cur = Path(sys.argv[1]) if len(sys.argv) > 1 else Path()
    repo = Repo(repo_root(cur))

    print(
        find_projects(  # type: ignore[call-arg] # FIX ME
            repo,
            load_main_config(cur, repo),  # type: ignore[arg-type] # FIX ME
        )
    )
