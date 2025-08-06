import os
import shlex

from ..base_rule import BaseRule
from ..config import RuleConfig
from ..sh import run_cmd


class Rule(BaseRule):
    def __init__(self, rule_config: RuleConfig) -> None:
        super().__init__(rule_config)
        if isinstance(self.rule_config.command, str):
            parts = shlex.split(self.rule_config.command)
        else:
            parts = self.rule_config.command  # type: ignore[assignment] # FIX ME

        # TODO we'd like to pull this (singly) ahead of time, so need to
        # extract it, but don't want to do full argument parsing.
        self.image_name = parts[0]

        # This is intended to allow passing through args like "." (for repo- or
        # project-scoped rules that don't take filenames)
        self.command_parts = ["docker", "run", "--rm", "-w", "/data", "-v", ".:/data", *parts]

        # TODO limit this to DOCKER_* and whatever it needs for finding config?
        self.command_env = os.environ.copy()

    def prepare(self) -> bool:
        run_cmd(["docker", "pull", self.image_name], env=self.command_env)
        return True
