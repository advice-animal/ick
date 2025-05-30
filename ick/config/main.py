"""
The "main" config, which is merged from several locations.

This controls where we look for rules and how we find projects.
"""

from __future__ import annotations

import os
from logging import getLogger
from pathlib import Path
from typing import Any, List, Optional

import appdirs
from keke import ktrace
from msgspec import Struct, ValidationError, field
from msgspec.structs import replace as replace
from msgspec.toml import decode as decode_toml
from vmodule import VLOG_1, VLOG_2

from ..git import find_repo_root
from ..util import merge
from .settings import FilterConfig, Settings

LOG = getLogger(__name__)

# TODO consider just having a .toml file in the source that we load last

DEFAULT_PROJECT_MARKERS = {
    "python": [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
    ],
    "js": [
        "package-lock.json",
        "yarn.lock",
    ],
    "java": [
        "build.gradle",
    ],
    # Since autodetected projects can't contain other projects, this caused
    # problems (docker-compose.yml at the root of the repo is fairly common).
    # "docker": [
    #     "docker-compose.yml",
    #     "Dockerfile",
    # ],
}


class MainConfig(Struct):
    # These are all loaded and their names merged to become available

    # Intended to be set either in the "user" config or the "repo" config, not
    # a subdir.
    project_root_markers: Optional[dict[str, list[str]]] = None
    # TODO extra_project_root_markers
    skip_project_root_in_repo_root: Optional[bool] = None

    # Intended to be set in a "repo" config
    explicit_project_dirs: Optional[list] = None
    ignore_project_dirs: Optional[list] = None

    # Can be set in a "user", "repo", or "project"
    do_not_want: Optional[list[str]] = None

    def inherit(self, less_specific_defaults):
        # TODO this is way more verbose than I'd like.
        # "union" semantics
        self.project_root_markers = merge(self.project_root_markers, less_specific_defaults.project_root_markers)
        self.skip_project_root_in_repo_root = (
            self.skip_project_root_in_repo_root
            if self.skip_project_root_in_repo_root is not None
            else less_specific_defaults.skip_project_root_in_repo_root
        )

        # "override" semantics
        self.do_not_want = self.do_not_want if self.do_not_want is not None else less_specific_defaults.do_not_want
        self.explicit_project_dirs = (
            self.explicit_project_dirs if self.explicit_project_dirs is not None else less_specific_defaults.explicit_project_dirs
        )
        self.ignore_project_dirs = (
            self.ignore_project_dirs if self.ignore_project_dirs is not None else less_specific_defaults.ignore_project_dirs
        )


MainConfig.DEFAULT = MainConfig(
    project_root_markers=DEFAULT_PROJECT_MARKERS,
    explicit_project_dirs=False,
    skip_project_root_in_repo_root=False,
)


class PyprojectConfig(Struct):
    tool: ToolConfig


class ToolConfig(Struct):
    ick: MainConfig


@ktrace()
def load_main_config(cur: Path, isolated_repo: bool) -> MainConfig:
    conf = MainConfig()
    paths: List[Path] = []
    if os.environ.get("ICK_CONFIG"):
        # This isn't well documented because it's only intended for testing --
        # I don't have a reason people would want to ignore both repo and user
        # config.
        paths.append(Path(os.environ.get("ICK_CONFIG")))
    else:
        repo_root = find_repo_root(cur)
        config_dir = appdirs.user_config_dir("ick", "advice-animal")
        if cur.resolve() != repo_root.resolve():
            paths.extend(
                [
                    Path(cur, "ick.toml"),
                    Path(cur, "pyproject.toml"),
                ]
            )
        paths.extend(
            [
                Path(repo_root, "ick.toml"),
                Path(repo_root, "pyproject.toml"),
            ]
        )
        if not isolated_repo:
            paths.append(
                Path(config_dir, "ick.toml"),
            )

        LOG.log(VLOG_1, "Loading main config near %s", cur)

    for p in paths:
        LOG.debug("Looking for config at %s", p)
        if p.exists():
            LOG.log(VLOG_1, "Config found at %s", p)
            if p.name == "pyproject.toml":
                c = load_pyproject(p, p.read_bytes())
            else:
                c = load_regular(p, p.read_bytes())
            LOG.log(VLOG_2, "Loaded %s of %r", p, c)
            conf.inherit(c)

    conf.inherit(MainConfig.DEFAULT)

    return conf


def load_pyproject(p: Path, data: bytes) -> MainConfig:
    try:
        c = decode_toml(data, type=PyprojectConfig).tool.ick
    except ValidationError as e:
        # TODO surely there's a cleaner way to validate _inside_
        # but not care if [tool.other] is present...
        if "Object missing required field `ick` - at `$.tool`" in e.args[0]:
            return MainConfig()
        if "Object missing required field `tool`" in e.args[0]:
            return MainConfig()
        raise
    return c


def load_regular(p: Path, data: bytes) -> MainConfig:
    return decode_toml(data, type=MainConfig)


class RuntimeConfig(Struct):
    """
    One big object to be able to pass around that contains everything we need.
    """

    main_config: MainConfig
    rules_config: Any  # Avoiding possible circular reference
    settings: Settings
    filter_config: FilterConfig = field(default_factory=FilterConfig)
    repo: Any = None


__all__ = ["load_main_config", "MainConfig", "RuntimeConfig"]
