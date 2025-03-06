from pathlib import Path

from ick.config import HookConfig, HookRepoConfig, HooksConfig, MainConfig, Mount, RuntimeConfig, Settings
from ick.config.hook_repo import discover_hooks, get_impl, load_hook_repo, load_pyproject
from ick_protocol import Scope


def test_load_hook_repo():
    m = Mount(base_path=Path.cwd(), path="tests/fixture_hooks")
    rc = load_hook_repo(m)
    assert len(rc.hook) == 3

    assert rc.hook[0].name == "hello"
    assert rc.hook[0].language == "shell"
    assert rc.hook[0].scope == Scope.REPO
    assert rc.hook[0].command == "echo hi"
    assert rc.hook[0].test_path == Path("tests/fixture_hooks/tests/hello").resolve()

    # load_hook_repo doesn't sort yet, so these are in discovered order
    assert rc.hook[1].name == "shouty"

    assert rc.hook[2].name == "goodbye"
    assert rc.hook[2].language == "shell"
    assert rc.hook[2].command == "exit 1"
    assert rc.hook[2].scope == Scope.SINGLE_FILE
    assert rc.hook[2].test_path == Path("tests/fixture_hooks/tests/goodbye").resolve()


def test_load_pyproject_errors():
    assert load_pyproject(Path(), b"") == HookRepoConfig()
    assert load_pyproject(Path(), b"[tool]") == HookRepoConfig()
    assert load_pyproject(Path(), b"[tool.ick]") == HookRepoConfig()
    assert load_pyproject(Path(), b"[tool.ick.baz]") == HookRepoConfig()


def test_get_impl():
    assert get_impl(HookConfig(name="foo", language="shell"))


def test_discover():
    m = Mount(base_path=Path.cwd(), path="tests/fixture_hooks")
    h = HooksConfig(mount=[m])
    hooks = discover_hooks(rtc=RuntimeConfig(main_config=MainConfig(), hooks_config=h, settings=Settings()))
    assert len(hooks) == 3
