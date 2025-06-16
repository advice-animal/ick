import os
import shlex

from ..base_rule import BaseRule, ExecWork
from ..sh import run_cmd


class Rule(BaseRule):
    work_cls = ExecWork

    def __init__(self, rule_config, repo_config):
        super().__init__(rule_config, repo_config)
        # TODO we'd like to pull this (singly) ahead of time, so need to
        # extract it, but don't want to do full argument parsing.
        self.entry = shlex.split(self.rule_config.entry)
        self.image_name = self.entry[0]

        # This is intended to allow passing through args like "." (for repo- or
        # project-scoped rules that don't take filenames)
        self.command_parts = ["docker", "run", "-v", ".:/data", *self.entry]

        # TODO limit this to DOCKER_* and whatever it needs for finding config?
        self.command_env = os.environ.copy()

    def prepare(self):
        run_cmd(["docker", "pull", self.image_name], env=self.command_env)
