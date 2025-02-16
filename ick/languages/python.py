from ..base_language import BaseHook


class Hook(BaseHook):
    def __init__(self, hook_config, repo_config):
        super().__init__(hook_config, repo_config)
        # TODO validate path / hook.name ".py" exists
