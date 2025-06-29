from __future__ import annotations

import os
import sys
from pathlib import Path

from msgspec.json import decode as json_decode
from msgspec.json import encode as json_encode

from ..base_rule import BaseRule, ExecWork


def default(x):  # type: ignore[no-untyped-def] # FIX ME
    if isinstance(x, Path):
        return str(x)
    raise NotImplementedError


def main(filenames):  # type: ignore[no-untyped-def] # FIX ME
    config = json_decode(os.environ["RULE_CONFIG"])
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


class Rule(BaseRule):
    work_cls = ExecWork

    def __init__(self, conf, repo_config) -> None:  # type: ignore[no-untyped-def] # FIX ME
        super().__init__(conf, repo_config)  # type: ignore[no-untyped-call] # FIX ME
        self.command_parts = [sys.executable, "-m", __name__]
        self.command_env = {
            "RULE_CONFIG": json_encode(conf, enc_hook=default),
        }
        if "PYTHONPATH" in os.environ:
            self.command_env["PYTHONPATH"] = os.environ["PYTHONPATH"]  # type: ignore[assignment] # FIX ME

    def prepare(self):  # type: ignore[no-untyped-def] # FIX ME
        pass


if __name__ == "__main__":
    main(sys.argv[1:])  # type: ignore[no-untyped-call] # FIX ME
