from __future__ import annotations

import textwrap
from pathlib import Path

from ick.config.project_config import load_project_config


def test_load_project_config_from_ick_toml(tmp_path: Path) -> None:
    (tmp_path / "ick.toml").write_text(
        textwrap.dedent(
            """\
            ignore_rules = ["subdir/rule"]
            ignore_filenames = ["generated/**"]

            [rules."subdir/rule"]
            exclude_filenames = ["tests/**"]
            """
        )
    )

    config = load_project_config(tmp_path)

    assert config.ignore_rules == ["subdir/rule"]
    assert config.ignore_filenames == ["generated/**"]
    assert config.rules["subdir/rule"].exclude_filenames == ["tests/**"]


def test_load_project_config_from_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(
            """\
            [tool.ick]
            ignore_rules = ["subdir/rule"]
            ignore_filenames = ["generated/**"]

            [tool.ick.rules."subdir/rule"]
            exclude_filenames = ["tests/**"]
            """
        )
    )

    config = load_project_config(tmp_path)

    assert config.ignore_rules == ["subdir/rule"]
    assert config.ignore_filenames == ["generated/**"]
    assert config.rules["subdir/rule"].exclude_filenames == ["tests/**"]


def test_load_project_config_merges_ick_toml_and_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(
            """\
            [tool.ick]
            ignore_rules = ["pyproject"]
            ignore_filenames = ["generated/**"]

            [tool.ick.rules."subdir/rule"]
            exclude_filenames = ["pyproject/**"]
            """
        )
    )
    (tmp_path / "ick.toml").write_text(
        textwrap.dedent(
            """\
            ignore_rules = ["ick"]
            ignore_filenames = ["local/**"]

            [rules."subdir/rule"]
            exclude_filenames = ["ick/**"]
            """
        )
    )

    config = load_project_config(tmp_path)

    assert config.ignore_rules == ["ick", "pyproject"]
    assert config.ignore_filenames == ["local/**", "generated/**"]
    assert config.rules["subdir/rule"].exclude_filenames == ["ick/**", "pyproject/**"]
