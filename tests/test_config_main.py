import textwrap
from pathlib import Path

import pytest

from ick.config.main import MainConfig, RepoSettings, _load_repo_settings, load_main_config, load_pyproject


def test_load_main() -> None:
    assert "pyproject.toml" in load_main_config(Path.cwd(), isolated_repo=True).project_root_markers["python"]  # type: ignore[index] # FIX ME


def test_load_pyproject_errors() -> None:
    assert load_pyproject(Path(), b"") == MainConfig()
    assert load_pyproject(Path(), b"[tool]") == MainConfig()
    assert load_pyproject(Path(), b"[tool.ick]") == MainConfig()
    assert load_pyproject(Path(), b"[tool.ick.baz]") == MainConfig()


def test_repo_settings_defaults() -> None:
    rs = RepoSettings()
    assert rs.file == "pyproject.toml"
    assert rs.key == "tool.ick"


def test_load_repo_settings_missing_file(tmp_path: Path) -> None:
    assert _load_repo_settings(tmp_path, RepoSettings(file="nonexistent.yaml", key="ick")) is None


def test_load_repo_settings_missing_key(tmp_path: Path) -> None:
    (tmp_path / "settings.yaml").write_text(
        textwrap.dedent("""\
            other:
              key: value\n
        """)
    )
    assert _load_repo_settings(tmp_path, RepoSettings(file="settings.yaml", key="ick")) is None


def test_load_repo_settings_nested_key(tmp_path: Path) -> None:
    (tmp_path / "settings.yaml").write_text(
        textwrap.dedent("""\
            tools:
              ick:
                skip_project_root_in_repo_root: true
        """)
    )
    result = _load_repo_settings(tmp_path, RepoSettings(file="settings.yaml", key="tools.ick"))
    assert result is not None
    assert result.skip_project_root_in_repo_root is True


def test_load_repo_settings_values_loaded(tmp_path: Path) -> None:
    (tmp_path / "settings.yaml").write_text(
        textwrap.dedent("""\
            ick:
              explicit_project_dirs:
                - services/
                - tools/
        """)
    )
    result = _load_repo_settings(tmp_path, RepoSettings(file="settings.yaml", key="ick"))
    assert result is not None
    assert result.explicit_project_dirs == ["services/", "tools/"]


def test_load_repo_settings_toml_file(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""\
            [tool.ick]
            skip_project_root_in_repo_root = true
        """)
    )
    result = _load_repo_settings(tmp_path, RepoSettings())
    assert result is not None
    assert result.skip_project_root_in_repo_root is True


def test_repo_settings_higher_priority_than_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Repo settings override local TOML config."""
    (tmp_path / "ick.toml").write_text(
        textwrap.dedent("""\
            skip_project_root_in_repo_root = true
            [repo_settings]
            file = "settings.yaml"
            key = "ick"
        """)
    )
    (tmp_path / "settings.yaml").write_text(
        textwrap.dedent("""\
            ick:
              skip_project_root_in_repo_root: false
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.skip_project_root_in_repo_root is False


def test_yaml_settings_used_when_no_toml_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """YAML settings fill in values not set in TOML."""
    (tmp_path / "ick.toml").write_text(
        textwrap.dedent("""\
            [repo_settings]
            file = "settings.yaml"
            key = "ick"
        """)
    )
    (tmp_path / "settings.yaml").write_text(
        textwrap.dedent("""\
            ick:
              explicit_project_dirs:
                - src/
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.explicit_project_dirs == ["src/"]


def test_pyproject_repo_settings_read_without_explicit_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """pyproject.toml:tool.ick is read as repo settings even without explicit repo_settings config."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""\
            [tool.ick]
            skip_project_root_in_repo_root = true
        """)
    )
    monkeypatch.chdir(tmp_path)
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.skip_project_root_in_repo_root is True
