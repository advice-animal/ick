from glob import glob
from os.path import dirname
from pathlib import Path

import appdirs

from ick_protocol import ListResponse

from ..base_rule import BaseCollection
from ..venv import PythonEnv


class Rule(BaseCollection):
    def __init__(self, collection_config, repo_config):
        # TODO super?
        self.collection_config = collection_config
        self.repo_config = repo_config

        venv_key = "todo"  # collection_config.qualname
        venv_path = Path(appdirs.user_cache_dir("ick", "advice-animal"), "envs", venv_key)
        self.venv = PythonEnv(venv_path, self.collection_config.deps)

    def list(self) -> ListResponse:
        names = glob(
            "*/__init__.py",
            root_dir=self.collection_config.collection_path,
        )
        return ListResponse(
            rule_names=[dirname(n) for n in names],
        )

    def prepare(self):
        self.venv.prepare()
