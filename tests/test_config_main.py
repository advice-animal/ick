from pathlib import Path

from ick.config.main import load_main_config


def test_load_main():
    assert "pyproject.toml" in load_main_config(Path.cwd()).project_root_markers["python"]
