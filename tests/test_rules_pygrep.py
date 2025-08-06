from pathlib import Path

from feedforward import Notification, State
from helpers import FakeRun

from ick.config import RuleConfig
from ick.rules.pygrep import Rule
from ick.types_project import BaseRepo, Project


def test_pygrep_works(tmp_path: Path) -> None:
    conf = RuleConfig(
        name="foo",
        impl="pygrep",
        search="hello",
        replace="bar",
        inputs=["*.sh"],
    )
    rule = Rule(conf)

    run = FakeRun()
    projects = [Project(BaseRepo(Path("/tmp")), "my_subdir/", "shell", "bash.sh")]
    rule.add_steps_to_run(projects, {}, run)

    assert len(run.steps) == 1

    run.steps[0].index = 0
    rv = list(run.steps[0].process(1, [Notification(key="my_subdir/demo.sh", state=State(gens=(0,), value=b"xhello\n"))]))
    assert len(rv) == 1
    assert rv[0] == Notification(
        key="my_subdir/demo.sh",
        state=State(
            gens=(1,),
            value=b"xbar\n",
        ),
    )
