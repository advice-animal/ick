import os
import shlex

from ..base_rule import BaseRule, ExecWork
from ..sh import run_cmd


class Rule(BaseRule):
    work_cls = ExecWork

    def __init__(self, rule_config, repo_config):
        super().__init__(rule_config, repo_config)
        if isinstance(self.rule_config.command, str):
            parts = shlex.split(self.rule_config.command)
        else:
            parts = self.rule_config.command

        # TODO we'd like to pull this (singly) ahead of time, so need to
        # extract it, but don't want to do full argument parsing.
        self.image_name = parts[0]

        # This is intended to allow passing through args like "." (for repo- or
        # project-scoped rules that don't take filenames)
        self.command_parts = ["docker", "run", "--rm", "-w", "/data", "-v", ".:/data", *parts]

        # TODO limit this to DOCKER_* and whatever it needs for finding config?
        self.command_env = os.environ.copy()

    def prepare(self):
        run_cmd(["docker", "pull", self.image_name], env=self.command_env)
