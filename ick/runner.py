from __future__ import annotations

from logging import getLogger
from typing import Any

from keke import ktrace

from .config import HookConfig
from .config.hook_repo import discover_hooks, get_impl

LOG = getLogger(__name__)


class Runner:
    def __init__(self, rtc):
        self.rtc = rtc
        self.hooks = discover_hooks(rtc)

    def run(self) -> Any:
        for hook in self.hooks:
            if isinstance(hook, HookConfig):
                if hook.urgency_enum < self.rtc.filter_config.urgency_filter:
                    continue
            i = get_impl(hook)(hook, self.rtc)
            print(i, list(i.list()))

    @ktrace()
    def echo_hooks(self) -> None:
        d = {}
        for config_hook in self.hooks:
            i = get_impl(config_hook)(config_hook, self.rtc)
            for hook in i.list().hook_names:
                d.setdefault(config_hook.urgency, []).append(hook)

        first = True
        for u in sorted(d.keys()):
            if not first:
                print()
            else:
                first = False

            print(u.name)
            print("=" * len(str(u.name)))
            for v in d[u]:
                print(f"* {v}")
