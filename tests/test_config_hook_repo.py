from pathlib import Path

from ick.config import MainConfig, RuleConfig, RuleRepoConfig, RulesConfig, Ruleset, RuntimeConfig, Settings
from ick.config.rule_repo import discover_rules, get_impl, load_pyproject, load_rule_repo
from ick_protocol import Scope


def test_load_rule_repo() -> None:
    r = Ruleset(base_path=Path.cwd(), path="tests/fixture_rules")
    rc = load_rule_repo(r)
    assert len(rc.rule) == 3

    assert rc.rule[0].name == "hello"
    assert rc.rule[0].impl == "shell"
    assert rc.rule[0].scope == Scope.REPO
    assert rc.rule[0].command == "echo hi"
    assert rc.rule[0].test_path == Path("tests/fixture_rules/tests/hello").resolve()

    # load_rule_repo doesn't sort yet, so these are in discovered order
    assert rc.rule[1].name == "shouty"

    assert rc.rule[2].name == "goodbye"
    assert rc.rule[2].impl == "shell"
    assert rc.rule[2].command == "exit 1"
    assert rc.rule[2].scope == Scope.FILE
    assert rc.rule[2].test_path == Path("tests/fixture_rules/tests/goodbye").resolve()


def test_load_pyproject_errors() -> None:
    assert load_pyproject(Path(), b"") == RuleRepoConfig()
    assert load_pyproject(Path(), b"[tool]") == RuleRepoConfig()
    assert load_pyproject(Path(), b"[tool.ick]") == RuleRepoConfig()
    assert load_pyproject(Path(), b"[tool.ick.baz]") == RuleRepoConfig()


def test_get_impl() -> None:
    assert get_impl(RuleConfig(name="foo", impl="shell"))


def test_discover() -> None:
    r = Ruleset(base_path=Path.cwd(), path="tests/fixture_rules")
    h = RulesConfig(ruleset=[r])
    rules = discover_rules(rtc=RuntimeConfig(main_config=MainConfig(), rules_config=h, settings=Settings()))
    assert len(rules) == 3
