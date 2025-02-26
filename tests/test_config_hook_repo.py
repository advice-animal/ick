from pathlib import Path

from ick.config.hook_repo import get_impl, load_hook_repo, load_pyproject
from ick.config.hooks import HookConfig, HookRepoConfig, Mount


def test_load_hook_repo():
    m = Mount(base_path=Path.cwd(), path="tests/fixture_hooks")
    rc = load_hook_repo(m)
    assert len(rc.hook) == 2

    assert rc.hook[0].name == "hello"
    assert rc.hook[0].language == "shell"
    assert rc.hook[0].hook_path == Path("tests/fixture_hooks").resolve()

    assert rc.hook[1].name == "goodbye"
    assert rc.hook[1].language == "shell"
    assert rc.hook[1].hook_path == Path("tests/fixture_hooks").resolve()


def test_load_pyproject_errors():
    assert load_pyproject(Path(), b"") == HookRepoConfig()
    assert load_pyproject(Path(), b"[tool]") == HookRepoConfig()
    assert load_pyproject(Path(), b"[tool.ick]") == HookRepoConfig()
    assert load_pyproject(Path(), b"[tool.ick.baz]") == HookRepoConfig()


def test_get_impl():
    assert get_impl(HookConfig(name="foo", language="shell"))
