import os
from logging import getLogger
from pathlib import Path
from typing import Iterable

import platformdirs
from vmodule import VLOG_1, VLOG_2

from ..git import find_repo_root

LOG = getLogger(__name__)


def possible_config_files(cur: Path, isolated_repo: bool) -> Iterable[tuple[str, Path]]:
    """
    Produce a sequence of possible config files to try to read.

    Each item is a pair: (description, path). The description is for log
    messages to help describe why we are using that path.
    """
    if ick_config := os.environ.get("ICK_CONFIG"):
        # This isn't well documented because it's only intended for testing --
        # I don't have a reason people would want to ignore both repo and user
        # config.
        yield "ICK_CONFIG", Path(ick_config)
    else:
        # TODO revisit whether defining rules in pyproject.toml is a good idea
        yield "current directory", Path(cur, "ick.toml")
        yield "current directory", Path(cur, "pyproject.toml")

        repo_root = find_repo_root(cur)
        if cur.resolve() != repo_root.resolve():
            LOG.log(VLOG_2, f"Repo root is above current directory: {repo_root.resolve()}")
            yield "repo root", Path(repo_root, "ick.toml")
            yield "repo root", Path(repo_root, "pyproject.toml")

        if not isolated_repo:
            config_dir = platformdirs.user_config_dir("ick", "advice-animal")
            yield "user settings", Path(config_dir, "ick.toml.local")
            yield "user settings", Path(config_dir, "ick.toml")

        # TODO: what was this log message meant to convey?
        LOG.log(VLOG_1, "Loading workspace config near %s", cur)


def config_files(cur: Path, isolated_repo: bool) -> Iterable[Path]:
    """Produce a sequence of existing config files to read."""
    for kind, config_path in possible_config_files(cur, isolated_repo):
        config_path = config_path.resolve()
        LOG.log(VLOG_2, "Looking for %s config at %s", kind, config_path)
        if config_path.exists():
            LOG.log(VLOG_1, "Config from %s found at %s", kind, config_path)
            yield config_path
