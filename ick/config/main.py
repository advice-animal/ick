"""
The "main" config, which is merged from several locations.

This controls where we look for rules and how we find projects.
"""

from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import Any, Optional

import msgspec
import tomllib
import yaml
from keke import ktrace
from msgspec import Struct, ValidationError, field
from msgspec.structs import replace as replace
from msgspec.toml import decode as decode_toml
from parse_errors import ParseContext
from vmodule import VLOG_1, VLOG_2

from ..git import find_repo_root
from ..util import merge
from .search import config_files
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
    "go": [
        "go.mod",
    ],
    # Since autodetected projects can't contain other projects, this caused
    # problems (docker-compose.yml at the root of the repo is fairly common).
    # "docker": [
    #     "docker-compose.yml",
    #     "Dockerfile",
    # ],
}


class RepoSettings(Struct):
    """Specifies a file and dotted key path to read per-repo config from."""

    file: str
    key: str


class MainConfig(Struct):
    # These are all loaded and their names merged to become available

    # Intended to be set either in the "user" config or the "repo" config, not
    # a subdir.
    project_root_markers: Optional[dict[str, list[str]]] = None
    # TODO extra_project_root_markers
    skip_project_root_in_repo_root: Optional[bool] = None

    # Intended to be set in a "repo" config
    explicit_project_dirs: Optional[list] = None  # type: ignore[type-arg] # FIX ME
    ignore_project_dirs: Optional[list] = None  # type: ignore[type-arg] # FIX ME

    # A file name and key used to read additional per-repo settings. Typically
    # set in user settings.
    repo_settings: Optional[RepoSettings] = None

    def inherit(self, less_specific_defaults):  # type: ignore[no-untyped-def] # FIX ME
        # TODO this is way more verbose than I'd like.
        # "union" semantics
        self.project_root_markers = merge(self.project_root_markers, less_specific_defaults.project_root_markers)  # type: ignore[no-untyped-call] # FIX ME
        self.skip_project_root_in_repo_root = (
            self.skip_project_root_in_repo_root
            if self.skip_project_root_in_repo_root is not None
            else less_specific_defaults.skip_project_root_in_repo_root
        )

        # "override" semantics
        self.explicit_project_dirs = (
            self.explicit_project_dirs if self.explicit_project_dirs is not None else less_specific_defaults.explicit_project_dirs
        )
        self.ignore_project_dirs = (
            self.ignore_project_dirs if self.ignore_project_dirs is not None else less_specific_defaults.ignore_project_dirs
        )
        self.repo_settings = self.repo_settings if self.repo_settings is not None else less_specific_defaults.repo_settings


MainConfig.DEFAULT = MainConfig(  # type: ignore[attr-defined] # FIX ME
    project_root_markers=DEFAULT_PROJECT_MARKERS,
    explicit_project_dirs=False,  # type: ignore[arg-type] # FIX ME
    skip_project_root_in_repo_root=False,
)


class PyprojectConfig(Struct):
    tool: ToolConfig


class ToolConfig(Struct):
    ick: MainConfig


def _load_repo_settings(repo_root: Path, repo_settings: RepoSettings) -> Optional[MainConfig]:
    """Read per-repo config from a file at the dotted key path.

    Supports TOML and YAML files. Returns None if the file or key is missing;
    other errors propagate.
    """
    settings_path = (repo_root / repo_settings.file).resolve()
    if not settings_path.exists():
        LOG.log(VLOG_1, "repo_settings file not found: %s", settings_path)
        return None
    if settings_path.suffix == ".toml":
        data = tomllib.loads(settings_path.read_text())
    elif settings_path.suffix in [".yml", ".yaml"]:
        data = yaml.safe_load(settings_path.read_bytes())
    else:
        LOG.warning("unknown file type for repo settings: %s", settings_path)
        return None
    if not isinstance(data, dict):
        # The file was empty.
        return None
    for k in repo_settings.key.split("."):
        data = data.get(k)
        if not isinstance(data, dict):
            if data is None:
                LOG.log(VLOG_1, "repo_settings key %r not found in %s", repo_settings.key, settings_path)
            else:
                LOG.warning("unexpected type %r found for key %r in %s", type(data).__name__, repo_settings.key, settings_path)
            return None
    LOG.log(VLOG_1, "Loaded repo_settings from %s key %r", settings_path, repo_settings.key)
    return msgspec.convert(data, MainConfig)


@ktrace()
def load_main_config(cur: Path, isolated_repo: bool) -> MainConfig:
    conf = MainConfig()
    for config_path in config_files(cur, isolated_repo):
        if config_path.name == "pyproject.toml":
            c = load_pyproject(config_path, config_path.read_bytes())
        else:
            c = load_regular(config_path, config_path.read_bytes())
        LOG.log(VLOG_2, "Loaded %s of %r", config_path, c)
        conf.inherit(c)  # type: ignore[no-untyped-call] # FIX ME

    # If `repo_settings` has been set by one of the defaults config files,
    # go read those repo settings.
    if conf.repo_settings:
        repo_config = _load_repo_settings(find_repo_root(cur), conf.repo_settings)
        if repo_config is not None:
            repo_config.inherit(conf)  # type: ignore[no-untyped-call] # FIX ME
            conf = repo_config

    conf.inherit(MainConfig.DEFAULT)  # type: ignore[attr-defined, no-untyped-call] # FIX ME

    return conf


def load_pyproject(p: Path, data: bytes) -> MainConfig:
    with ParseContext(p, data=data):
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
    with ParseContext(p, data=data):
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
