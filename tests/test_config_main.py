from pathlib import Path

from ick.config.main import MainConfig, load_main_config, load_pyproject


def test_load_main() -> None:
    assert "pyproject.toml" in load_main_config(Path.cwd(), isolated_repo=True).project_root_markers["python"]  # type: ignore[index] # FIX ME


def test_load_pyproject_errors() -> None:
    assert load_pyproject(Path(), b"") == MainConfig()
    assert load_pyproject(Path(), b"[tool]") == MainConfig()
    assert load_pyproject(Path(), b"[tool.ick]") == MainConfig()
    assert load_pyproject(Path(), b"[tool.ick.baz]") == MainConfig()
