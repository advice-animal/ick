from glob import glob
from os.path import dirname

from ..base_language import BaseCollection


class Hook(BaseCollection):
    def __init__(self, collection_config, repo_config):
        self.collection_config = collection_config
        self.repo_config = repo_config

    def iterate_hooks(self):
        names = glob(
            "*/__init__.py",
            root_dir=self.collection_config.collection_path,
        )
        return [dirname(n) for n in names]
