import subprocess
import sys
from pathlib import Path

from feedforward import Notification, State
import pytest

from ick.config import RuleConfig
from ick.rules.docker import Rule
from ick.types_project import Project

from helpers import FakeRun


#@pytest.mark.skipif(sys.platform == "darwin", reason="GHA can't test docker")
def test_basic_docker(tmp_path: Path) -> None:
    docker_rule = Rule(
        RuleConfig(
            name="append",
            impl="docker",
            scope="repo",  # type: ignore[arg-type] # FIX ME
            command="alpine:3.14 /bin/sh -c 'echo dist >> .gitignore'",
        ),
    )

    run = FakeRun()
    projects = [Project(None, "my_subdir/", "shell", "bash.sh")]
    docker_rule.add_steps_to_run(projects, {}, run)

    assert len(run.steps) == 1

    run.steps[0].index = 0
    rv = list(run.steps[0].process(1, [Notification(key="my_subdir/demo.sh", state=State(gens=(0,), value=b"xhello\n"))]))
    assert len(rv) == 1
    assert rv[0] == 17
