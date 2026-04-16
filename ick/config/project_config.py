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

LOG = getLogger(__name__)


class PerRuleProjectConfig(Struct):
    """Per-rule overrides within a project."""

    exclude_filenames: list[str] = field(default_factory=list)


class ProjectConfig(Struct):
    """
    Per-project configuration loaded from the project directory.

    Can be set in ``[tool.ick]`` in a ``pyproject.toml`` (Python projects)
    or in a ``.ick.toml`` file (any project type).

    Rule names are ``subdir/name`` within the rule repo — everything after the
    prefix.  For example, if ``ick --list`` shows
    ``advice-animal/python/move_isort_cfg``, the key to use here is
    ``python/move_isort_cfg`` (the prefix ``advice-animal`` is omitted because
    it is user-controlled and can vary).  For rules at the root of their repo
    there is no subdir, so just the bare name is used.

    Example ``pyproject.toml``::

        [tool.ick]
        ignore_rules = ["python/move_isort_cfg"]
        ignore_filenames = ["generated/**"]  # skipped by all rules

        [tool.ick.rules."python/move_isort_cfg"]
        exclude_filenames = ["tests/**", "generated/**"]

    Example ``.ick.toml``::

        ignore_rules = ["python/move_isort_cfg"]
        ignore_filenames = ["generated/**"]

        [rules."python/move_isort_cfg"]
        exclude_filenames = ["tests/**"]
    """

    ignore_rules: list[str] = field(default_factory=list)
    ignore_filenames: list[str] = field(default_factory=list)
    rules: dict[str, PerRuleProjectConfig] = field(default_factory=dict)


class _PyprojectToolConfig(Struct):
    ick: ProjectConfig


class _PyprojectConfig(Struct):
    tool: _PyprojectToolConfig


def load_project_config(project_dir: Path) -> ProjectConfig:
    """Load per-project ick config from a project directory.

    Checks (in order):
    - ``pyproject.toml`` → ``[tool.ick]`` section
    - ``.ick.toml`` at the top level of the project directory

    Returns an empty ``ProjectConfig`` if neither file exists or neither
    contains an ick section.
    """
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        data = pyproject.read_bytes()
        try:
            return decode_toml(data, type=_PyprojectConfig).tool.ick
        except ValidationError as e:
            msg = str(e)
            if "Object missing required field `ick`" in msg or "Object missing required field `tool`" in msg:
                pass  # No [tool.ick] section — fall through
            else:
                raise

    ick_toml = project_dir / ".ick.toml"
    if ick_toml.exists():
        return decode_toml(ick_toml.read_bytes(), type=ProjectConfig)

    return ProjectConfig()
