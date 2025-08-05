from __future__ import annotations

import shlex

from ..base_rule import BaseRule
from ..config import RuleConfig


class Rule(BaseRule):
    def __init__(self, rule_config: RuleConfig) -> None:
        super().__init__(rule_config)
        if rule_config.command:
            if isinstance(rule_config.command, str):
                self.command_parts = shlex.split(rule_config.command)
            else:
                self.command_parts = rule_config.command
        else:
            assert rule_config.data
            self.command_parts = ["/bin/bash", "-c", rule_config.data.strip()]
