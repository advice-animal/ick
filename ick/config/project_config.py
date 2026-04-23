"""
Per-project configuration, read from the project directory.

This is distinct from the "main" config (which controls how ick finds rules
and projects) and from the rule-repo config (which defines rules).  This
config lives inside a target repo and lets a project say things like
"don't run rule X here" or "don't show rule Y the files matching Z*".
"""

from __future__ import annotations

from logging import getLogger
from pathlib import Path

from msgspec import Struct, ValidationError, field
from msgspec.toml import decode as decode_toml

from ..util import merge

LOG = getLogger(__name__)


class PerRuleProjectConfig(Struct):
    """Per-rule overrides within a project."""

    exclude_filenames: list[str] = field(default_factory=list)

    def inherit(self, less_specific_defaults):  # type: ignore[no-untyped-def] # FIX ME
        self.exclude_filenames = merge(self.exclude_filenames, less_specific_defaults.exclude_filenames)  # type: ignore[no-untyped-call] # FIX ME


class ProjectConfig(Struct):
    """
    Per-project configuration loaded from the project directory.

    Can be set in ``ick.toml`` or in ``[tool.ick]`` inside ``pyproject.toml``.

    Rule names are ``subdir/name`` within the rule repo — everything after the
    prefix.  For example, if ``ick --list`` shows
    ``advice-animal:python/move_isort_cfg``, the key to use here is
    ``python/move_isort_cfg`` (the prefix ``advice-animal`` is omitted because
    it is user-controlled and can vary).  For rules at the root of their repo
    there is no subdir, so just the bare name is used.

    Example ``pyproject.toml``::

        [tool.ick]
        ignore_rules = ["python/move_isort_cfg"]
        ignore_filenames = ["generated/**"]  # skipped by all rules

        [tool.ick.rules."python/move_isort_cfg"]
        exclude_filenames = ["tests/**", "generated/**"]

    Example ``ick.toml``::

        ignore_rules = ["python/move_isort_cfg"]
        ignore_filenames = ["generated/**"]

        [rules."python/move_isort_cfg"]
        exclude_filenames = ["tests/**"]
    """

    ignore_rules: list[str] = field(default_factory=list)
    ignore_filenames: list[str] = field(default_factory=list)
    rules: dict[str, PerRuleProjectConfig] = field(default_factory=dict)

    def inherit(self, less_specific_defaults):  # type: ignore[no-untyped-def] # FIX ME
        self.ignore_rules = merge(self.ignore_rules, less_specific_defaults.ignore_rules)  # type: ignore[no-untyped-call] # FIX ME
        self.ignore_filenames = merge(self.ignore_filenames, less_specific_defaults.ignore_filenames)  # type: ignore[no-untyped-call] # FIX ME

        merged_rules = dict(less_specific_defaults.rules)
        for rule_name, rule_config in self.rules.items():
            if rule_name in merged_rules:
                rule_config.inherit(merged_rules[rule_name])
            merged_rules[rule_name] = rule_config
        self.rules = merged_rules


class _PyprojectToolConfig(Struct):
    ick: ProjectConfig


class _PyprojectConfig(Struct):
    tool: _PyprojectToolConfig


def load_project_config(project_dir: Path) -> ProjectConfig:
    """Load per-project ick config from a project directory.

    Reads both of these locations when present:
    - ``pyproject.toml`` → ``[tool.ick]`` section
    - ``ick.toml`` at the top level of the project directory

    If both files exist, their settings are combined with ``ick.toml``
    taking precedence for conflicting values.

    Returns an empty ``ProjectConfig`` if neither file exists or neither
    contains an ick section.
    """
    conf = ProjectConfig()
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        data = pyproject.read_bytes()
        try:
            conf = decode_toml(data, type=_PyprojectConfig).tool.ick
        except ValidationError as e:
            msg = str(e)
            if "Object missing required field `ick`" in msg or "Object missing required field `tool`" in msg:
                pass  # No [tool.ick] section — fall through
            else:
                raise

    ick_toml = project_dir / "ick.toml"
    if ick_toml.exists():
        ick_conf = decode_toml(ick_toml.read_bytes(), type=ProjectConfig)
        ick_conf.inherit(conf)
        conf = ick_conf

    return conf
