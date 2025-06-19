"""
Rule definitions, merged from repo config and user config.
"""

from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import Optional, Sequence, Union

from keke import ktrace
from msgspec import Struct, ValidationError, field
from msgspec.structs import replace as replace
from msgspec.toml import decode as decode_toml
from vmodule import VLOG_1

from ick_protocol import Risk, Scope, Success, Urgency

from ..util import merge
from .search import config_files

LOG = getLogger(__name__)


class RulesConfig(Struct):
    """ """

    ruleset: Sequence[Mount] = ()

    def inherit(self, less_specific_defaults):
        self.ruleset = merge(self.ruleset, less_specific_defaults.ruleset)


class Mount(Struct):
    url: Optional[str] = None
    path: Optional[str] = None

    prefix: Optional[str] = None
    base_path: Optional[Path] = None  # Dir of the config that referenced this

    repo: Optional[RuleRepoConfig] = None

    def __post_init__(self):
        if self.prefix is None:
            self.prefix = (self.url or self.path).rstrip("/").split("/")[-1]


class PyprojectRulesConfig(Struct):
    tool: PyprojectToolConfig


class PyprojectToolConfig(Struct):
    ick: RuleRepoConfig


class RuleRepoConfig(Struct):
    rule: list[RuleConfig] = field(default_factory=list)
    repo_path: Optional[Path] = None

    def inherit(self, less_specific_defaults):
        self.rule = merge(self.rule, less_specific_defaults.rule)


class RuleConfig(Struct):
    """
    Configuration for a single rule
    """

    name: str
    impl: str

    scope: Scope = Scope.SINGLE_FILE
    command: Optional[Union[str, list[str]]] = None
    success: Success = Success.EXIT_STATUS

    risk: Optional[Risk] = Risk.HIGH
    urgency: Optional[Urgency] = Urgency.LATER
    order: int = 50
    hours: int = 1

    command: Optional[str] = None
    data: Optional[str] = None
    entry: Optional[str] = None

    search: Optional[str] = None
    # ruff bug: https://github.com/astral-sh/ruff/issues/10874
    replace: Optional[str] = None  # noqa: F811

    deps: Optional[list[str]] = None
    test_path: Optional[Path] = None
    script_path: Optional[Path] = None
    qualname: str = ""  # the name _within its respective repo_

    inputs: Optional[Sequence[str]] = None
    outputs: Optional[Sequence[str]] = None
    extra_inputs: Optional[Sequence[str]] = None

    description: Optional[str] = None
    contact: Optional[str] = None


@ktrace()
def load_rules_config(cur: Path, isolated_repo: bool) -> RulesConfig:
    conf = RulesConfig()
    for config_path in config_files(cur, isolated_repo):
        if config_path.name == "pyproject.toml":
            try:
                c = decode_toml(config_path.read_bytes(), type=PyprojectToolConfig).tool.ick
            except ValidationError as e:
                # TODO surely there's a cleaner way to validate _inside_
                # but not care if [tool.other] is present...
                if "Object missing required field `ick`" not in e.args[0]:
                    raise

                else:
                    LOG.log(VLOG_1, "No ick config found in %s", config_path)
                    continue
        else:
            c = decode_toml(config_path.read_bytes(), type=RulesConfig)

        for mount in c.ruleset:
            mount.base_path = config_path.parent

        # TODO finalize mount paths so relative works
        try:
            conf.inherit(c)
        except Exception as e:
            raise Exception(f"While merging {config_path}: {e!r}")

    return conf
