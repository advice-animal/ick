from pathlib import Path

import appdirs

from ..base_language import BaseRule
from ..venv import PythonEnv


class Language(BaseRule):
    def __init__(self, rule_config, repo_config):
        super().__init__(rule_config, repo_config)
        # TODO validate path / rule.name ".py" exists
        venv_key = rule_config.qualname
        venv_path = Path(appdirs.user_cache_dir("ick", "advice-animal"), "envs", venv_key)
        self.venv = PythonEnv(venv_path, self.rule_config.deps)

    def prepare(self):
        self.venv.prepare()
