from __future__ import annotations

import os
import sys
from pathlib import Path

from msgspec.json import decode as json_decode
from msgspec.json import encode as json_encode

from ..base_language import BaseHook, ExecWork


def main(filenames):
    config = json_decode(os.environ["HOOK_CONFIG"])
    name = config["name"]
    search = config["search"]
    replace = config["replace"]

    for f in filenames:
        current_contents = Path(f).read_text()
        if search in current_contents:
            if replace is None:
                print(f"{f}: found {name}")
            else:
                new_contents = current_contents.replace(search, replace)
                Path(f).write_text(new_contents)


class Language(BaseHook):
    work_cls = ExecWork

    def __init__(self, conf, repo_config) -> None:
        super().__init__(conf, repo_config)
        self.command_parts = [sys.executable, "-m", __name__]
        self.command_env = {
            "HOOK_CONFIG": json_encode(conf),
        }
        if "PYTHONPATH" in os.environ:
            self.command_env["PYTHONPATH"] = os.environ["PYTHONPATH"]


if __name__ == "__main__":
    main(sys.argv[1:])
