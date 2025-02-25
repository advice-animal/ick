"""
Hook definitions, merged from repo config and user config.
"""

from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import Optional, Sequence, Union

import appdirs
from keke import ktrace
from msgspec import Struct, ValidationError, field
from msgspec.structs import replace as replace
from msgspec.toml import decode as decode_toml
from vmodule import VLOG_1

from ick_protocol import Risk, Scope, Urgency

from ..git import find_repo_root
from ..util import merge

LOG = getLogger(__name__)


class HooksConfig(Struct):
    """ """

    mount: Sequence[Mount] = ()

    def inherit(self, less_specific_defaults):
        self.mount = merge(self.mount, less_specific_defaults.mount)


class Mount(Struct):
    url: Optional[str] = None
    path: Optional[str] = None

    prefix: Optional[str] = None
    base_path: Optional[Path] = None  # Dir of the config that referenced this

    repo: Optional[HookRepoConfig] = None


class PyprojectHooksConfig(Struct):
    tool: PyprojectToolConfig


class PyprojectToolConfig(Struct):
    ick: HookRepoConfig


class HookRepoConfig(Struct):
    hook: list[HookConfig] = field(default_factory=list)
    collection: list[CollectionConfig] = field(default_factory=list)
    repo_path: Optional[Path] = None

    def inherit(self, less_specific_defaults):
        self.hook = merge(self.hook, less_specific_defaults.hook)
        self.collection = merge(self.collection, less_specific_defaults.collection)


class HookConfig(Struct):
    """
    Configuration for a single hook
    """

    language: str
    name: str

    scope: Scope = Scope.SINGLE_FILE
    command: Optional[Union[str, list[str]]] = None

    # See post_init workaround because we can't seem to decode IntEnum from name
    # here.
    risk: str = "high"
    risk_enum: Optional[Risk] = None
    urgency: str = "later"
    urgency_enum: Optional[Risk] = None

    order: int = 50
    command: Optional[str] = None
    data: Optional[str] = None
    search: Optional[str] = None
    # ruff bug: https://github.com/astral-sh/ruff/issues/10874
    replace: Optional[str] = None  # noqa: F811

    deps: Optional[list[str]] = None
    hook_path: Optional[Path] = None  # set later, test dir is under this

    def __post_init__(self):
        self.urgency_enum = Urgency[self.urgency.upper()]
        self.risk_enum = Risk[self.risk.upper()]


class CollectionConfig(Struct):
    """
    Configuration for a collection (single process implementing multiple hooks)
    """

    language: str
    name: str

    scope: Scope = Scope.SINGLE_FILE
    order: int = 50
    subdir: str = "."

    deps: Optional[list[str]] = None
    collection_path: Optional[Path] = None  # set later, test dir is under this


@ktrace()
def load_hooks_config(cur: Path) -> HooksConfig:
    conf = HooksConfig()
    repo_root = find_repo_root(cur)
    config_dir = appdirs.user_config_dir("advice-animal", "ick")
    paths = []
    # TODO revisit whether defining hooks in pyproject.toml is a good idea
    if cur != repo_root:
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
            Path(config_dir, "ick.toml.local"),
            Path(config_dir, "ick.toml"),
        ]
    )

    LOG.log(VLOG_1, "Loading workspace config near %s", cur)

    for p in paths:
        if p.exists():
            LOG.log(VLOG_1, "Config found at %s", p)
            if p.name == "pyproject.toml":
                try:
                    c = decode_toml(p.read_bytes(), type=PyprojectToolConfig).tool.ick
                except ValidationError as e:
                    # TODO surely there's a cleaner way to validate _inside_
                    # but not care if [tool.other] is present...
                    if "Object missing required field `ick`" not in e.args[0]:
                        raise
            else:
                c = decode_toml(p.read_bytes(), type=HooksConfig)

            for mount in c.mount:
                mount.base_path = p.parent

            # TODO finalize mount paths so relative works
            conf.inherit(c)

    return conf
