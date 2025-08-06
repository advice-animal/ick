"""Helpers for tests."""

from typing import Any

from feedforward import Run, Step


class FakeRun(Run[Any, Any]):
    def __init__(self) -> None:
        self.steps: list[Step[Any, Any]] = []

    def add_step(self, step: Step[Any, Any]) -> None:
        self.steps.append(step)
