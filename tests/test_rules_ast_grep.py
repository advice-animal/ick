
from feedforward import Notification, State

from ick.config import RuleConfig
from ick.rules.ast_grep import Rule
from ick.types_project import Project


class FakeRun:
    def __init__(self):
        self.steps = []

    def add_step(self, step):
        self.steps.append(step)


def test_ast_grep_works() -> None:
    rule = Rule(
        RuleConfig(
            name="foo",
            impl="ast-grep",
            search="F($$$X)",
            replace="G($$$X)",
            inputs=["*.py"],
        ),
    )

    assert rule.prepare()

    run = FakeRun()
    projects = [Project(None, "my_subdir/", "python", "demo.py")]
    rule.add_steps_to_run(projects, {}, run)

    assert len(run.steps) == 1
    run.steps[0].index = 0
    rv = list(run.steps[0].process(1, [Notification(key="my_subdir/demo.py", state=State(gens=(0,), value=b"x = F(1)\n"))]))
    assert len(rv) == 1
    assert rv[0] == Notification(
        key="my_subdir/demo.py",
        state=State(gens=(1,), value=b"x = G(1)\n"),
    )
