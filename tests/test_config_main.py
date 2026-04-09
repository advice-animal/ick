import textwrap
from pathlib import Path

from ick.config.main import MainConfig, RepoSettings, _load_repo_settings, load_main_config, load_pyproject


def test_load_main() -> None:
    assert "pyproject.toml" in load_main_config(Path.cwd(), isolated_repo=True).project_root_markers["python"]  # type: ignore[index] # FIX ME


def test_load_pyproject_errors() -> None:
    assert load_pyproject(Path(), b"") == MainConfig()
    assert load_pyproject(Path(), b"[tool]") == MainConfig()
    assert load_pyproject(Path(), b"[tool.ick]") == MainConfig()
    assert load_pyproject(Path(), b"[tool.ick.baz]") == MainConfig()


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


def test_load_repo_settings_from_default_file(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""\
            [tool.ick]
            skip_project_root_in_repo_root = true
        """)
    )
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result is not None
    assert result.skip_project_root_in_repo_root is True


def test_repo_settings_override_default_file(tmp_path: Path) -> None:
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
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.skip_project_root_in_repo_root is False


def test_repo_settings_file_empty(tmp_path: Path) -> None:
    """What if the repo settings file is empty?"""
    (tmp_path / "ick.toml").write_text(
        textwrap.dedent("""\
            skip_project_root_in_repo_root = true
            [repo_settings]
            file = "settings.yaml"
            key = "ick"
        """)
    )
    (tmp_path / "settings.yaml").write_text("")
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.skip_project_root_in_repo_root is True


def test_repo_settings_from_toml(tmp_path: Path) -> None:
    """Repo settings can be read from .toml files."""
    (tmp_path / "ick.toml").write_text(
        textwrap.dedent("""\
            skip_project_root_in_repo_root = true
            [repo_settings]
            file = "enterprise.toml"
            key = "ick"
        """)
    )
    (tmp_path / "enterprise.toml").write_text(
        textwrap.dedent("""\
            [ick]
            skip_project_root_in_repo_root = false
        """)
    )
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.skip_project_root_in_repo_root is False


def test_repo_settings_used_when_no_conflict(tmp_path: Path) -> None:
    """Repo settings fill in values not set in TOML."""
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
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.explicit_project_dirs == ["src/"]


def test_repo_settings_in_subdir(tmp_path: Path) -> None:
    """The repo_settings file can be in a subdirectory."""
    (tmp_path / "ick.toml").write_text(
        textwrap.dedent("""\
            [repo_settings]
            file = "enterprise/settings.yaml"
            key = "tool.ick"
        """)
    )
    (tmp_path / "enterprise").mkdir()
    (tmp_path / "enterprise/settings.yaml").write_text(
        textwrap.dedent("""\
            tool:
              ick:
                explicit_project_dirs:
                  - src/
        """)
    )
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.explicit_project_dirs == ["src/"]


def test_repo_settings_dont_exist(tmp_path: Path) -> None:
    """The repo_settings file can point to a non-existent file."""
    (tmp_path / "ick.toml").write_text(
        textwrap.dedent("""\
            [repo_settings]
            file = "settings.yaml"
            key = "ick"
        """)
    )
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.skip_project_root_in_repo_root is False


def test_repo_settings_key_doesnt_exist(tmp_path: Path) -> None:
    """The repo_settings file can point to an existing file, but without our key."""
    (tmp_path / "ick.toml").write_text(
        textwrap.dedent("""\
            [repo_settings]
            file = "settings.yaml"
            key = "ick"
        """)
    )
    (tmp_path / "settings.yaml").write_text(
        textwrap.dedent("""\
            some-other-tool:
              awesome: true
        """)
    )
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.skip_project_root_in_repo_root is False


def test_repo_settings_key_wrong_type(tmp_path: Path, caplog) -> None:
    """A warning is issued if the repo settings key gets to a non-dict."""
    (tmp_path / "ick.toml").write_text(
        textwrap.dedent("""\
            [repo_settings]
            file = "settings.yaml"
            key = "tool.ick"
        """)
    )
    (tmp_path / "settings.yaml").write_text(
        textwrap.dedent("""\
            tool:
              ick: 17
        """)
    )
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.skip_project_root_in_repo_root is False
    warning = caplog.records[0].message
    assert "unexpected type 'int' found for key 'tool.ick' in " in warning
    assert warning.endswith("settings.yaml")


def test_pyproject_repo_settings_read_without_explicit_config(tmp_path: Path) -> None:
    """pyproject.toml:tool.ick is read as repo settings even without explicit repo_settings config."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""\
            [tool.ick]
            skip_project_root_in_repo_root = true
        """)
    )
    result = load_main_config(tmp_path, isolated_repo=True)
    assert result.skip_project_root_in_repo_root is True
