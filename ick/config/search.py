import os
from logging import getLogger
from pathlib import Path
from typing import Iterable

import platformdirs
from vmodule import VLOG_1, VLOG_2

from ..git import find_repo_root

LOG = getLogger(__name__)


def possible_config_files(cur: Path, isolated_repo: bool) -> Iterable[tuple[str, Path, str | None]]:
    """
    Produce a sequence of possible config files to try to read.

    Each item is a triple: (description, path, key). The description is for log
    messages to help describe why we are using that path. The key is only set
    for YAML files specified via ICK_CONFIG with the "file:key" syntax.
    """
    if ick_config := os.environ.get("ICK_CONFIG"):
        parts = ick_config.split(":", 1)
        path = Path(parts[0])
        key = parts[1] if len(parts) > 1 else None
        if key is not None and path.suffix.lower() not in (".yaml", ".yml"):
            raise ValueError(f"ICK_CONFIG key syntax is only supported for YAML files: {ick_config!r}")
        yield "ICK_CONFIG", path, key

    # TODO revisit whether defining rules in pyproject.toml is a good idea
    yield "current directory", Path(cur, "ick.toml"), None
    yield "current directory", Path(cur, "pyproject.toml"), None

    repo_root = find_repo_root(cur)
    if cur.resolve() != repo_root.resolve():
        LOG.log(VLOG_2, f"Repo root is above current directory: {repo_root.resolve()}")
        yield "repo root", Path(repo_root, "ick.toml"), None
        yield "repo root", Path(repo_root, "pyproject.toml"), None

    if not isolated_repo:
        config_dir = platformdirs.user_config_dir("ick", "advice-animal")
        yield "user settings", Path(config_dir, "ick.toml.local"), None
        yield "user settings", Path(config_dir, "ick.toml"), None

    # TODO: what was this log message meant to convey?
    LOG.log(VLOG_1, "Loading workspace config near %s", cur)


def config_files(cur: Path, isolated_repo: bool) -> Iterable[tuple[Path, str | None]]:
    """Produce a sequence of existing config files to read, with optional key."""
    for kind, config_path, key in possible_config_files(cur, isolated_repo):
        config_path = config_path.resolve()
        LOG.log(VLOG_2, "Looking for %s config at %s", kind, config_path)
        if config_path.exists():
            LOG.log(VLOG_1, "Config from %s found at %s", kind, config_path)
            yield config_path, key
