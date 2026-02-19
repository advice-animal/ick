from pathlib import Path

import pytest

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


def test_ruleset_url_and_path_error() -> None:
    """Test that specifying both url and path raises a clear error."""
    with pytest.raises(ValueError, match="Can't specify both url and path"):
        Ruleset(url="https://github.com/example/rules.git", path=".")


def test_ruleset_merge_url_with_path() -> None:
    """Test that we can use merge to override a Ruleset with url with a Ruleset with path."""
    # Base config with a ruleset that has a URL
    base_config = RulesConfig(ruleset=[
        Ruleset(url="https://github.com/example/rules.git", prefix="prefix", base_path=Path.cwd())
    ])

    # More specific config with a ruleset that has a local path
    specific_config = RulesConfig(ruleset=[
        Ruleset(path="./local-rules", prefix="prefix", base_path=Path.cwd())
    ])

    # Merge: specific_config inherits from base_config
    specific_config.inherit(base_config)

    # After merging, we should have a single ruleset
    # The more specific (path) should override the base (url)
    assert len(specific_config.ruleset) == 1
    assert specific_config.ruleset[0].path == "./local-rules"
    assert specific_config.ruleset[0].url is None  # url from base is not kept
    assert specific_config.ruleset[0].prefix == "prefix"
