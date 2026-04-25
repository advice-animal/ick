import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable

import pytest
from feedforward import Notification, Run, State
from feedforward.step import Step

from ick.base_rule import BaseRule, GenericPreparedStep
from ick.cmdline import apply_filters
from ick.config import MainConfig, RuleConfig, RulesConfig, RuntimeConfig, Settings
from ick.runner import Runner
from ick.types_project import BaseRepo
from ick_protocol import Finished


def _step(patterns: list[str], rule_prepare=None) -> GenericPreparedStep:
    return GenericPreparedStep(
        prefixed_name="test_rule",
        patterns=patterns,
        project_path="",
        cmdline=[sys.executable, "-c", "pass"],
        extra_env={},
        append_filenames=True,
        rule_prepare=rule_prepare,
    )


def test_timeout_in_prepare_cancels_step() -> None:
    """TimeoutExpired from rule_prepare cancels the step."""

    def failing_prepare() -> bool:
        raise subprocess.TimeoutExpired(cmd="uv", timeout=120)

    step = _step(["*.py"], rule_prepare=failing_prepare)
    step.index = 0
    step.notify(Notification(key="a.py", state=State(gens=(0,), value=b"hello")))

    result = step.run_next_batch()

    assert result is False
    assert step.cancelled
    assert "timed out" in step.cancel_reason


@pytest.mark.parametrize("parallelism", [1, 2])
def test_timeout_in_prepare_run_continues_with_next_step(parallelism: int) -> None:
    """When a step's prepare times out, the rest of the run still completes."""

    def failing_prepare() -> bool:
        raise subprocess.TimeoutExpired(cmd="uv", timeout=120)

    run = Run(parallelism=parallelism)
    step0 = _step(["*.py"], rule_prepare=failing_prepare)
    step1 = GenericPreparedStep(
        prefixed_name="test_rule_2",
        patterns=["*.txt"],
        project_path="",
        cmdline=[sys.executable, "-c", "import sys; [open(f, 'w').write('modified') for f in sys.argv[1:]]"],
        extra_env={},
        append_filenames=True,
    )

    run.add_step(step0)
    run.add_step(step1)

    result = run.run_to_completion({"a.py": b"hello", "b.txt": b"world"})

    assert step0.cancelled
    assert not step1.cancelled
    assert result["b.txt"].value == b"modified"


def test_default_parallelism_is_at_least_two() -> None:
    """Two items must be able to reach the barrier simultaneously."""
    barrier = threading.Barrier(2, timeout=5)

    class BarrierStep(Step[str, str]):
        def process(self, next_gen: int, notifications: Iterable[Notification[str, str]]) -> Iterable[Notification[str, str]]:
            list(notifications)
            barrier.wait()
            return []

    step = BarrierStep(batch_size=1)
    run: Run[str, str] = Run()
    run.add_step(step)

    run.run_to_completion({"a": "x", "b": "y"})
    assert not step.cancelled


def test_no_rules_found_mentions_legacy_flag_when_it_would_help(capsys) -> None:
    class DummyRule(BaseRule):
        def __init__(self, rule_config: RuleConfig) -> None:
            super().__init__(rule_config)

    rule = RuleConfig(
        name="rule",
        impl="dummy",
        full_name="subdir/rule",
        prefixed_name="prefix:subdir/rule",
    )
    rtc = RuntimeConfig(main_config=MainConfig.DEFAULT, rules_config=RulesConfig(), settings=Settings())
    runner = Runner(rtc, BaseRepo(root=Path.cwd()))
    runner.rules = [rule]
    runner.projects = []
    apply_filters(
        SimpleNamespace(obj=SimpleNamespace(filter_config=runner.rtc.filter_config)),
        ["prefix:subdir/rule"],
        "",
        allow_legacy_name_filter=False,
    )

    def fake_get_impl(_: RuleConfig) -> type[BaseRule]:
        return DummyRule

    from ick import runner as runner_module

    original_get_impl = runner_module.get_impl
    runner_module.get_impl = fake_get_impl
    try:
        assert list(runner.iter_rule_impl()) == []
    finally:
        runner_module.get_impl = original_get_impl

    out = capsys.readouterr().out
    assert "No rules found" in out
    assert "--allow-legacy-name-filter" in out


def _finished(results: list) -> Finished:
    return next(r for r in results if isinstance(r, Finished))


def test_stale_gen_metadata_is_dropped() -> None:
    """Metadata keyed to a superseded generation is silently dropped (last-writer-wins)."""
    step = _step(["*.py"])
    step.index = 0
    # Simulate file.py being processed in two batches: gen 1 was superseded by gen 2.
    step.accepted_state["file.py"] = State(gens=(1,), value=b"original")
    step.output_state["file.py"] = State(gens=(2,), value=b"original")
    step.batch_messages = {
        (("file.py", 1),): ("stale message\n", 99, {"findings": ["stale"]}),
        (("file.py", 2),): ("current message\n", 99, {"findings": ["current"]}),
    }
    step.outputs_final = True

    finished = _finished(step.compute_diff_messages())

    assert finished.metadata == {"findings": ["current"]}
    assert finished.message == "current message\n"


def test_current_gen_metadata_survives() -> None:
    """Metadata whose generation matches output_state is kept."""
    step = _step(["*.py"])
    step.index = 0
    step.accepted_state["file.py"] = State(gens=(3,), value=b"original")
    step.output_state["file.py"] = State(gens=(3,), value=b"original")
    step.batch_messages = {
        (("file.py", 3),): ("the message\n", 99, {"findings": ["kept"]}),
    }
    step.outputs_final = True

    finished = _finished(step.compute_diff_messages())

    assert finished.metadata == {"findings": ["kept"]}
    assert finished.message == "the message\n"
