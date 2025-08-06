from pathlib import Path

from feedforward import Notification, State
from helpers import FakeRun

from ick.config import RuleConfig
from ick.rules.merge_toml import Rule
from ick.types_project import BaseRepo, Project


def test_merge_toml_works() -> None:
    rule = Rule(
        RuleConfig(
            name="foo",
            impl="merge_toml",
            data="""\
[foo]
baz = 99
""",
            inputs=["*.toml"],
        ),
    )
    assert rule.prepare()

    run = FakeRun()
    projects = [Project(BaseRepo(Path("/tmp")), "my_subdir/", "python", "demo.py")]
    rule.add_steps_to_run(projects, {}, run)

    assert len(run.steps) == 1
    run.steps[0].index = 0
    rv = list(
        run.steps[0].process(
            1,
            [Notification(key="my_subdir/demo.toml", state=State(gens=(0,), value=b"# doc comment\n[foo]\nbar = 0\nbaz = 1\nfloof = 2\n"))],
        )
    )
    assert len(rv) == 1
    assert rv[0] == Notification(
        key="my_subdir/demo.toml",
        state=State(gens=(1,), value=b"# doc comment\n[foo]\nbar = 0\nbaz = 99\nfloof = 2\n"),
    )
