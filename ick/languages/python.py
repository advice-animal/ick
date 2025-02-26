import sys
from pathlib import Path

from ..base_language import BaseHook


def find_uv() -> Path:
    uv_path = Path(sys.executable).parent / "uv"
    assert uv_path.exists()
    return uv_path


class Hook(BaseHook):
    def __init__(self, hook_config, repo_config):
        super().__init__(hook_config, repo_config)
        # TODO validate path / hook.name ".py" exists
