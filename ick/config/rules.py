"""
Rule definitions, merged from repo config and user config.
"""

from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import Optional, Sequence

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

    # This should really be called `rulesets`, but this name lets us use
    # `[[ruleset]]` syntax in the TOML files.
    ruleset: Sequence[Ruleset] = ()

    def inherit(self, less_specific_defaults):  # type: ignore[no-untyped-def] # FIX ME
        self.ruleset = merge(self.ruleset, less_specific_defaults.ruleset)  # type: ignore[no-untyped-call] # FIX ME


class Ruleset(Struct):
    url: Optional[str] = None
    path: Optional[str] = None

    prefix: Optional[str] = None
    base_path: Optional[Path] = None  # Dir of the config that referenced this

    repo: Optional[RuleRepoConfig] = None

    def __post_init__(self) -> None:
        if self.prefix is None:
            self.prefix = (self.url or self.path).rstrip("/").split("/")[-1]  # type: ignore[union-attr] # FIX ME


class PyprojectRulesConfig(Struct):
    tool: PyprojectToolConfig


class PyprojectToolConfig(Struct):
    ick: RuleRepoConfig


class RuleRepoConfig(Struct):
    rule: list[RuleConfig] = field(default_factory=list)
    repo_path: Optional[Path] = None

    def inherit(self, less_specific_defaults):  # type: ignore[no-untyped-def] # FIX ME
        self.rule = merge(self.rule, less_specific_defaults.rule)  # type: ignore[no-untyped-call] # FIX ME


class RuleConfig(Struct):
    """
    Configuration for a single rule
    """

    name: str
    impl: str

    scope: Scope = Scope.FILE
    success: Success = Success.EXIT_STATUS

    risk: Risk = Risk.HIGH
    urgency: Urgency = Urgency.LATER
    order: int = 50
    hours: int | None = None

    command: str | Sequence[str] | None = None
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
    project_types: Optional[Sequence[str]] = None

    description: Optional[str] = None
    contact: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.qualname:
            self.qualname = self.name


@ktrace()
def load_rules_config(cur: Path, isolated_repo: bool) -> RulesConfig:
    conf = RulesConfig()
    for config_path in config_files(cur, isolated_repo):
        if config_path.name == "pyproject.toml":
            try:
                c = decode_toml(config_path.read_bytes(), type=PyprojectToolConfig).tool.ick  # type: ignore[attr-defined] # FIX ME
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

        for ruleset in c.ruleset:
            ruleset.base_path = config_path.parent

        # TODO finalize ruleset paths so relative works
        try:
            conf.inherit(c)  # type: ignore[no-untyped-call] # FIX ME
        except Exception as e:
            raise Exception(f"While merging {config_path}: {e!r}")

    return conf


def one_repo_config(repo: str) -> RulesConfig:
    """Create a configuration for just one repo.

    `repo`: either a file path or a URL.
    """
    conf = RulesConfig()
    if Path(repo).exists():
        conf.ruleset = [Ruleset(path=repo)]
    else:
        conf.ruleset = [Ruleset(url=repo)]
    return conf
