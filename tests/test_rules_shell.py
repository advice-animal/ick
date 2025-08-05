from pathlib import Path

import pytest

from ick.config import RuleConfig
from ick.rules.shell import Rule
from ick.types_project import Project

from helpers import FakeRun


@pytest.mark.parametrize(
    "cmd",
    [
        "sed-like -e 's/hello/HELLO/g'",
        ["sed-like", "-e", "s/hello/HELLO/g"],
    ],
)
def test_smoke_single_file(cmd: str | list[str], tmp_path: Path) -> None:
    conf = RuleConfig(
        name="hello",
        impl="shell",
        command=cmd,
        inputs=["*.md"],
    )
    rule = Rule(conf)

    run = FakeRun()
    projects = [Project(None, "my_subdir", "shell", "bash.sh")]
    rule.add_steps_to_run(projects, {}, run)

    assert len(run.steps) == 1
    assert run.steps[0].cmdline == ["sed-like", "-e", "s/hello/HELLO/g"]
