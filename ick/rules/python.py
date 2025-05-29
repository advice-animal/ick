from pathlib import Path

import appdirs

from ..base_rule import BaseRule, ExecWork
from ..venv import PythonEnv


class Rule(BaseRule):
    work_cls = ExecWork

    def __init__(self, rule_config, repo_config):
        super().__init__(rule_config, repo_config)
        # TODO validate path / rule.name ".py" exists
        venv_key = rule_config.qualname
        venv_path = Path(appdirs.user_cache_dir("ick", "advice-animal"), "envs", venv_key)
        self.venv = PythonEnv(venv_path, self.rule_config.deps)
        if rule_config.data:
            # We could write this to a temp path if necessary, maybe even within the venv dir, during prepare.
            self.command_parts = ["xargs", "-n1", "-P6", "-0", self.venv.bin("python"), "-c", rule_config.data]
        else:
            self.command_parts = ["xargs", "-n1", "-P6", "-0", self.venv.bin("python"), rule_config.script_path.with_suffix(".py")]
        self.command_env = {}

    def prepare(self):
        self.venv.prepare()
