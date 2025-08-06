from pathlib import Path

import pytest
from helpers import FakeRun

from ick.config import RuleConfig
from ick.rules.shell import Rule
from ick.types_project import BaseRepo, Project


@pytest.mark.parametrize(
    "cmd",
    [
        "sed-like -e 's/hello/HELLO/g'",
        ["sed-like", "-e", "s/hello/HELLO/g"],
    ],
)
def test_smoke_single_file(cmd: str | list[str], tmp_path: Path) -> None:
    rule = Rule(
        RuleConfig(
            name="hello",
            impl="shell",
            command=cmd,
            inputs=["*.md"],
        )
    )

    run = FakeRun()
    projects = [Project(BaseRepo(Path("/tmp")), "my_subdir", "shell", "bash.sh")]
    rule.add_steps_to_run(projects, {}, run)

    assert len(run.steps) == 1
    assert run.steps[0].cmdline == ["sed-like", "-e", "s/hello/HELLO/g"]
