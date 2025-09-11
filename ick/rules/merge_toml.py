from __future__ import annotations

import os
import sys
from pathlib import Path

import tomlkit
from msgspec.json import decode as json_decode
from msgspec.json import encode as json_encode

from ..base_rule import BaseRule
from ..config import RuleConfig


def default(x):  # type: ignore[no-untyped-def] # FIX ME
    if isinstance(x, Path):
        return str(x)
    raise NotImplementedError


def main(filenames):  # type: ignore[no-untyped-def] # FIX ME
    config = json_decode(os.environ["RULE_CONFIG"])
    desired = tomlkit.parse(config["data"])

    for f in filenames:
        current_contents = Path(f).read_text()
        doc = tomlkit.parse(current_contents)
        merge(doc, desired)  # type: ignore[no-untyped-call] # FIX ME
        new_contents = tomlkit.dumps(doc)
        if new_contents != current_contents:
            Path(f).write_text(new_contents)


def merge(d1, d2):  # type: ignore[no-untyped-def] # FIX ME
    """
    Recursive dictionary merge, preserving order and with a special case.
    """
    for k in d1:
        if k in d2:
            # merge
            if isinstance(d2[k], dict):
                merge(d1[k], d2[k])  # type: ignore[no-untyped-call] # FIX ME
            else:
                d1[k] = d2[k]

    for k in d2:
        if k not in d1:
            # append
            d1[k] = d2[k]


class Rule(BaseRule):
    def __init__(self, rule_config: RuleConfig) -> None:
        super().__init__(rule_config)
        self.command_parts = [sys.executable, "-m", __name__]
        self.command_env = {
            "RULE_CONFIG": json_encode(rule_config, enc_hook=default).decode(),
        }
        if "PYTHONPATH" in os.environ:
            self.command_env["PYTHONPATH"] = os.environ["PYTHONPATH"]


if __name__ == "__main__":
    main(sys.argv[1:])  # type: ignore[no-untyped-call] # FIX ME
