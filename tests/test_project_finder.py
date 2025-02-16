from pathlib import Path

from msgspec.structs import replace

from ick.config import MainConfig
from ick.project_finder import find_projects


def test_project_finder():
    sample_string = "a/pyproject.toml\0a/tests/pyproject.toml\0b/pyproject.toml\0"
    assert [p.subdir for p in find_projects(Path(), sample_string, MainConfig.DEFAULT)] == ["a/", "b/"]

    sample_string = "pyproject.toml\0tests/pyproject.toml\0b/pyproject.toml\0"
    assert [p.subdir for p in find_projects(Path(), sample_string, MainConfig.DEFAULT)] == [""]

    sample_string = "readme.txt\0"
    assert [p.subdir for p in find_projects(Path(), sample_string, MainConfig.DEFAULT)] == []


def test_project_finder_skip_root():
    skip_root_config = replace(MainConfig.DEFAULT, skip_project_root_in_repo_root=True)

    sample_string = "a/pyproject.toml\0a/tests/pyproject.toml\0b/pyproject.toml\0"
    assert [p.subdir for p in find_projects(Path(), sample_string, skip_root_config)] == ["a/", "b/"]

    sample_string = "pyproject.toml\0tests/pyproject.toml\0b/pyproject.toml\0"
    # N.b. sorted
    assert [p.subdir for p in find_projects(Path(), sample_string, skip_root_config)] == ["b/", "tests/"]

    sample_string = "readme.txt\0"
    assert list(find_projects(Path(), sample_string, skip_root_config)) == []


def test_project_finder_marker_can_have_slashes():
    custom_config = replace(MainConfig.DEFAULT, project_root_markers={"shell": ["scripts/make.sh"]})

    sample_string = "foo/scripts/make.sh\0"
    assert [p.subdir for p in find_projects(Path(), sample_string, custom_config)] == ["foo/"]
