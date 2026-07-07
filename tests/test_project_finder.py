from pathlib import Path

from msgspec import to_builtins
from msgspec.structs import replace

from ick.config import DEFAULT_MAIN_CONFIG
from ick.project_finder import find_projects
from ick.types_project import Repo


def test_project_finder() -> None:
    sample_string = "a/pyproject.toml\0a/tests/pyproject.toml\0b/pyproject.toml\0"
    assert [p.subdir for p in find_projects(Repo(Path()), sample_string, DEFAULT_MAIN_CONFIG)] == ["a/", "b/"]

    sample_string = "pyproject.toml\0tests/pyproject.toml\0b/pyproject.toml\0"
    assert [p.subdir for p in find_projects(Repo(Path()), sample_string, DEFAULT_MAIN_CONFIG)] == [""]

    sample_string = "readme.txt\0"
    assert [p.subdir for p in find_projects(Repo(Path()), sample_string, DEFAULT_MAIN_CONFIG)] == []


def test_project_finder_skip_root() -> None:
    skip_root_config = replace(DEFAULT_MAIN_CONFIG, skip_project_root_in_repo_root=True)

    sample_string = "a/pyproject.toml\0a/tests/pyproject.toml\0b/pyproject.toml\0"
    assert [p.subdir for p in find_projects(Repo(Path()), sample_string, skip_root_config)] == ["a/", "b/"]

    sample_string = "pyproject.toml\0tests/pyproject.toml\0b/pyproject.toml\0"
    # N.b. sorted
    assert [p.subdir for p in find_projects(Repo(Path()), sample_string, skip_root_config)] == ["b/", "tests/"]

    sample_string = "readme.txt\0"
    assert list(find_projects(Repo(Path()), sample_string, skip_root_config)) == []


def test_project_finder_explicit_dirs() -> None:
    sample_string = "a/pyproject.toml\0b/pyproject.toml\0c/pyproject.toml\0"
    explicit_config = replace(DEFAULT_MAIN_CONFIG, explicit_project_dirs=["a", "c/"])
    assert [p.subdir for p in find_projects(Repo(Path()), sample_string, explicit_config)] == ["a/", "c/"]


def test_project_finder_explicit_dirs_keep_nested_projects() -> None:
    sample_string = "services/pyproject.toml\0services/api/pyproject.toml\0services/api/tests/pyproject.toml\0"
    explicit_config = replace(DEFAULT_MAIN_CONFIG, explicit_project_dirs=["services/", "services/api/"])

    assert [p.subdir for p in find_projects(Repo(Path()), sample_string, explicit_config)] == ["services/", "services/api/"]


def test_project_finder_outer_dirs() -> None:
    sample_string = "pyproject.toml\0services/pyproject.toml\0services/api/pyproject.toml\0tools/pyproject.toml\0"
    nested_config = replace(DEFAULT_MAIN_CONFIG, outer_project_dirs=["services/"])

    assert [p.subdir for p in find_projects(Repo(Path()), sample_string, nested_config)] == ["", "services/", "services/api/"]


def test_project_finder_marker_can_have_slashes() -> None:
    custom_config = replace(DEFAULT_MAIN_CONFIG, project_root_markers={"shell": ["scripts/make.sh"]})

    sample_string = "foo/scripts/make.sh\0"
    assert [p.subdir for p in find_projects(Repo(Path()), sample_string, custom_config)] == ["foo/"]


def test_project_finder_types() -> None:
    sample_string = "a/pyproject.toml\0a/tests/pyproject.toml\0b/build.gradle\0c/go.mod\0"
    projects = find_projects(Repo(Path()), sample_string, DEFAULT_MAIN_CONFIG)

    # These three make the assertion failures easier to read
    projects[0].repo = "FAKE"  # type: ignore[assignment]
    projects[1].repo = "FAKE"  # type: ignore[assignment]
    projects[2].repo = "FAKE"  # type: ignore[assignment]

    assert to_builtins(projects[0]) == {
        "subdir": "a/",
        "marker_filename": "pyproject.toml",
        "typ": "python",
        "repo": "FAKE",
    }
    assert to_builtins(projects[1]) == {
        "subdir": "b/",
        "marker_filename": "build.gradle",
        "typ": "java",
        "repo": "FAKE",
    }
    assert to_builtins(projects[2]) == {
        "subdir": "c/",
        "marker_filename": "go.mod",
        "typ": "go",
        "repo": "FAKE",
    }
