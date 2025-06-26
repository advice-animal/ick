from __future__ import annotations

import os
import shlex

from ..base_rule import BaseRule, ExecWork


class Rule(BaseRule):
    work_cls = ExecWork

    def __init__(self, rule_config, repo_config) -> None:  # type: ignore[no-untyped-def] # FIX ME
        super().__init__(rule_config, repo_config)  # type: ignore[no-untyped-call] # FIX ME
        if rule_config.command:
            self.command_parts = shlex.split(rule_config.command)
        else:
            assert rule_config.data
            self.command_parts = ["/bin/bash", "-c", rule_config.data.strip(), "placeholder"]

        # TODO
        self.command_env = os.environ.copy()

    def prepare(self) -> None:
        pass
