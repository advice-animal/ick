from pathlib import Path

import appdirs

from ..base_language import BaseHook
from ..venv import PythonEnv


class Language(BaseHook):
    def __init__(self, hook_config, repo_config):
        super().__init__(hook_config, repo_config)
        # TODO validate path / hook.name ".py" exists
        venv_key = hook_config.qualname
        venv_path = Path(appdirs.user_cache_dir("advice-animal", "ick"), "envs", venv_key)
        self.venv = PythonEnv(venv_path, self.hook_config.deps)

    def prepare(self):
        self.venv.prepare()
