from pathlib import Path

from ick.config.rule_repo import load_rule_repo
from ick.config.rules import Ruleset


def test_load_rule_repo_propagates_ruleset_tags(tmp_path: Path) -> None:
    (tmp_path / "ick.toml").write_text(
        """\
[[rule]]
name = "hello"
impl = "shell"
command = "true"
tags = ["rule-tag"]
"""
    )
    r = Ruleset(path=tmp_path.as_posix(), prefix="demo", tags=["team", "mandatory"])
    rc = load_rule_repo(r)
    assert list(rc.rule[0].tags) == ["team", "mandatory", "rule-tag"]


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
    assert list(rc.rule[0].tags) == ["security", "python"]
