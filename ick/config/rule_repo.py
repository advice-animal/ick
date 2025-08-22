from __future__ import annotations

import sys
from glob import glob
from logging import getLogger
from pathlib import Path
from posixpath import dirname
from typing import Sequence, Type

from keke import ktrace
from msgspec import ValidationError
from msgspec.json import encode as encode_json
from msgspec.toml import decode as decode_toml
from vmodule import VLOG_1, VLOG_2

from ..base_rule import BaseRule
from ..git import update_local_cache
from . import PyprojectRulesConfig, RuleConfig, RuleRepoConfig, Ruleset, RuntimeConfig

LOG = getLogger(__name__)


@ktrace()
def discover_rules(rtc: RuntimeConfig) -> Sequence[RuleConfig]:
    """
    Returns list of rules in the order that they would be applied.

    It is the responsibility of the caller to filter and handle things like
    project-level ignores.
    """
    rules: list[RuleConfig] = []

    rulesets = {}
    for ruleset in rtc.rules_config.ruleset:
        LOG.log(VLOG_1, "Processing %s", ruleset)
        # Prefixes should be unique; they override here
        skip_update = rtc.settings.skip_update
        rulesets[ruleset.prefix] = load_rule_repo(ruleset, skip_update=skip_update)

    for k, v in rulesets.items():
        rules.extend(v.rule)

    rules.sort(key=lambda h: (h.order, h.qualname))

    return rules


@ktrace("ruleset.url", "ruleset.path")
def load_rule_repo(ruleset: Ruleset, *, skip_update: bool = False) -> RuleRepoConfig:
    if ruleset.url:
        # TODO config for a subdir within?
        repo_path = update_local_cache(ruleset.url, skip_update=skip_update)  # TODO
    else:
        assert isinstance(ruleset.path, str)
        repo_path = Path(ruleset.base_path or "", ruleset.path).resolve()

    rc = RuleRepoConfig(repo_path=repo_path)

    LOG.log(VLOG_1, "Loading rules from %s", repo_path)
    # We use a regular glob here because it might not be from a git repo, or
    # that repo might be modified.  It also will let us more easily refer to a
    # subdir in the future.
    potential_configs = glob("**/ick.toml", root_dir=repo_path, recursive=True)
    potential_configs.extend(glob("**/ick.toml.local", root_dir=repo_path, recursive=True))
    potential_configs.extend(glob("**/pyproject.toml", root_dir=repo_path, recursive=True))
    for filename in potential_configs:
        p = Path(repo_path, filename)
        LOG.log(VLOG_1, "Config found at %s", filename)
        if p.name == "pyproject.toml":
            c = load_pyproject(p, p.read_bytes())
        else:
            c = load_regular(p, p.read_bytes())

        if not c.rule:
            continue

        LOG.log(VLOG_2, "Loaded %s", encode_json(c).decode("utf-8"))
        base = dirname(filename).lstrip("/")
        if base:
            base += "/"
        prefix = ruleset.prefix + "/" if (ruleset.prefix not in ["", "."]) else ""  # type: ignore[operator] # FIX ME
        for rule in c.rule:
            rule.qualname = prefix + base + rule.name
            rule.test_path = repo_path / base / "tests" / rule.name
            rule.script_path = repo_path / base / rule.name

        rc.inherit(c)  # type: ignore[no-untyped-call] # FIX ME

    return rc


def load_pyproject(p: Path, data: bytes) -> RuleRepoConfig:
    try:
        c = decode_toml(data, type=PyprojectRulesConfig).tool.ick
    except ValidationError as e:
        # TODO surely there's a cleaner way to validate _inside_
        # but not care if [tool.other] is present...
        if "Object missing required field `ick` - at `$.tool`" in e.args[0]:
            return RuleRepoConfig()
        if "Object missing required field `tool`" in e.args[0]:
            return RuleRepoConfig()
        raise
    return c


def load_regular(p: Path, data: bytes) -> RuleRepoConfig:
    return decode_toml(data, type=RuleRepoConfig)


@ktrace("rule.impl")
def get_impl(rule: RuleConfig) -> Type[BaseRule]:
    name = f"ick.rules.{rule.impl}"
    name = name.replace("-", "_")
    __import__(name)
    impl: Type[BaseRule] = sys.modules[name].Rule
    assert issubclass(impl, BaseRule)
    return impl
