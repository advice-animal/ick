from pathlib import Path

from feedforward import Notification, State
from helpers import FakeRun

from ick.config import RuleConfig
from ick.rules.python import Rule
from ick.types_project import BaseRepo, Project


def test_python_works(tmp_path: Path) -> None:
    rule = Rule(
        RuleConfig(
            name="foo",
            impl="python",
            inputs=["*.py"],
            data="""
                import sys
                import attrs
                for f in sys.argv[1:]:
                    with open(f, "w") as fo:
                        fo.write("new\\n")
                """,
            deps=["attrs"],
        ),
    )

    run = FakeRun()
    projects = [Project(BaseRepo(Path("/tmp")), "my_subdir/", "python", "demo.py")]
    rule.add_steps_to_run(projects, {}, run)
    rule.prepare()

    assert len(run.steps) == 1

    run.steps[0].index = 0
    rv = list(run.steps[0].process(1, [Notification(key="my_subdir/demo.py", state=State(gens=(0,), value=b"xhello\n"))]))
    assert len(rv) == 1
    assert rv[0] == Notification(
        key="my_subdir/demo.py",
        state=State(
            gens=(1,),
            value=b"new\n",
        ),
    )
