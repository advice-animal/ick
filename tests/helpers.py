"""Helpers for tests."""


class FakeRun:
    def __init__(self):
        self.steps = []

    def add_step(self, step):
        self.steps.append(step)
