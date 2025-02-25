from glob import glob
from os.path import dirname

from ick_protocol import ListResponse

from ..base_language import BaseCollection


class Language(BaseCollection):
    def __init__(self, collection_config, repo_config):
        self.collection_config = collection_config
        self.repo_config = repo_config

    def list(self) -> ListResponse:
        names = glob(
            "*/__init__.py",
            root_dir=self.collection_config.collection_path,
        )
        return ListResponse(
            hook_names=[dirname(n) for n in names],
        )
