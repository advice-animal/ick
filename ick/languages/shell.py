from __future__ import annotations

import os
import shlex

from ick_protocol import Scope

from ..base_rule import BaseRule, ExecWork


class Rule(BaseRule):
    work_cls = ExecWork

    def __init__(self, rule_config, repo_config):
        super().__init__(rule_config, repo_config)
        if rule_config.command:
            parts = shlex.split(rule_config.command)
            if rule_config.scope == Scope.SINGLE_FILE:
                self.command_parts = ["xargs", "-n1", "-0"] + parts
            else:
                self.command_parts = parts
        else:
            assert rule_config.data
            self.command_parts = ["/bin/bash", "-c", rule_config.data.strip()]

        # TODO
        self.command_env = os.environ.copy()

    def prepare(self):
        pass
