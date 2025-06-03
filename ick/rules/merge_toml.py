from __future__ import annotations

import os
import sys
from pathlib import Path

import tomlkit
from msgspec.json import decode as json_decode
from msgspec.json import encode as json_encode

from ..base_rule import BaseRule, ExecWork


def default(x):
    if isinstance(x, Path):
        return str(x)
    raise NotImplementedError


def main(filenames):
    config = json_decode(os.environ["RULE_CONFIG"])
    desired = tomlkit.parse(config["data"])

    for f in filenames:
        current_contents = Path(f).read_text()
        doc = tomlkit.parse(current_contents)
        merge(doc, desired)
        new_contents = tomlkit.dumps(doc)
        if new_contents != current_contents:
            Path(f).write_text(new_contents)


def merge(d1, d2):
    """
    Recursive dictionary merge, preserving order and with a special case.
    """
    for k in d1:
        if k in d2:
            # merge
            if isinstance(d2[k], dict):
                merge(d1[k], d2[k])
            else:
                d1[k] = d2[k]

    for k in d2:
        if k not in d1:
            # append
            d1[k] = d2[k]


class Rule(BaseRule):
    work_cls = ExecWork

    def __init__(self, conf, repo_config) -> None:
        super().__init__(conf, repo_config)
        self.command_parts = [sys.executable, "-m", __name__]
        self.command_env = {
            "RULE_CONFIG": json_encode(conf, enc_hook=default),
        }
        if "PYTHONPATH" in os.environ:
            self.command_env["PYTHONPATH"] = os.environ["PYTHONPATH"]

    def prepare(self):
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
