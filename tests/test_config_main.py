from pathlib import Path

import pytest

from ick.config.main import MainConfig, load_main_config, load_pyproject, load_yaml


def test_load_main() -> None:
    assert "pyproject.toml" in load_main_config(Path.cwd(), isolated_repo=True).project_root_markers["python"]  # type: ignore[index] # FIX ME


def test_load_pyproject_errors() -> None:
    assert load_pyproject(Path(), b"") == MainConfig()
    assert load_pyproject(Path(), b"[tool]") == MainConfig()
    assert load_pyproject(Path(), b"[tool.ick]") == MainConfig()
    assert load_pyproject(Path(), b"[tool.ick.baz]") == MainConfig()


def test_load_yaml_with_key() -> None:
    data = b"pave:\n  skip_project_root_in_repo_root: true\n"
    c = load_yaml(Path(), data, key="pave")
    assert c.skip_project_root_in_repo_root is True


def test_load_yaml_no_key() -> None:
    data = b"skip_project_root_in_repo_root: true\n"
    c = load_yaml(Path(), data)
    assert c.skip_project_root_in_repo_root is True


def test_load_yaml_missing_key() -> None:
    c = load_yaml(Path(), b"other_key: value\n", key="ick")
    assert c == MainConfig()


def test_load_yaml_empty() -> None:
    c = load_yaml(Path(), b"")
    assert c == MainConfig()


def test_ick_config_toml_with_key_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    toml_file = tmp_path / "config.toml"
    toml_file.write_text("")
    monkeypatch.setenv("ICK_CONFIG", f"{toml_file}:somekey")
    with pytest.raises(ValueError, match="ICK_CONFIG key syntax"):
        load_main_config(Path.cwd(), isolated_repo=True)


def test_ick_config_yaml_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("pave:\n  skip_project_root_in_repo_root: true\n")
    monkeypatch.setenv("ICK_CONFIG", f"{yaml_file}:pave")
    conf = load_main_config(Path.cwd(), isolated_repo=True)
    assert conf.skip_project_root_in_repo_root is True
