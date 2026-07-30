from pathlib import Path

from ick.config.rule_repo import load_rule_repo
from ick.config.rules import Ruleset


def test_load_rule_repo_adds_prefixed_name_as_tag() -> None:
    r = Ruleset(base_path=Path.cwd(), path="tests/fixture_rules", prefix="demo")
    rc = load_rule_repo(r)
    assert rc.rule
    for rule in rc.rule:
        assert rule.prefixed_name.startswith("demo:")
        assert rule.prefixed_name in rule.tags


def test_load_rule_repo_preserves_existing_tags(tmp_path: Path) -> None:
    (tmp_path / "ick.toml").write_text(
        """\
[[rule]]
name = "tagged"
impl = "shell"
command = "true"
tags = ["security", "python"]
"""
    )
    r = Ruleset(path=tmp_path.as_posix(), prefix="myrules")
    rc = load_rule_repo(r)
    assert len(rc.rule) == 1
    assert list(rc.rule[0].tags) == ["security", "python", "myrules:tagged"]


def test_load_rule_repo_default_tag_without_prefix(tmp_path: Path) -> None:
    (tmp_path / "ick.toml").write_text(
        """\
[[rule]]
name = "hello"
impl = "shell"
command = "true"
"""
    )
    r = Ruleset(path=tmp_path.as_posix(), prefix="")
    rc = load_rule_repo(r)
    assert list(rc.rule[0].tags) == ["hello"]
    assert rc.rule[0].prefixed_name == "hello"
