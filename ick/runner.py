from __future__ import annotations

import sys
from glob import glob
from logging import getLogger
from pathlib import Path
from typing import Sequence, Type

from msgspec import ValidationError
from msgspec.json import encode as encode_json
from msgspec.toml import decode as decode_toml
from vmodule import VLOG_1, VLOG_2

from .base_language import BaseCollection
from .config import RuntimeConfig
from .config_workspace import CollectionConfig, HookConfig, HookRepoConfig, WorkspaceHookConfig, WorkspaceMount
from .git import update_local_cache

LOG = getLogger(__name__)


class Runner:
    def __init__(self, rtc):
        self.rtc = rtc
        self.hooks = discover_hooks(rtc)

    def run(self) -> list[Result]:
        for hook in self.hooks:
            if isinstance(hook, HookConfig):
                if hook.urgency_enum < self.rtc.filter_config.urgency_filter:
                    continue
            i = get_impl(hook)(hook, self.rtc)
            print(i, list(i.iterate_hooks()))

    def echo_hooks(self) -> None:
        d = {}
        for config_hook in self.hooks:
            i = get_impl(config_hook)(config_hook, self.rtc)
            for hook in i.iterate_hooks():
                d.setdefault(hook.urgency, []).append(hook)

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


def discover_hooks(rtc: RuntimeConfig) -> Sequence[HookConfig | CollectionConfig]:
    """
    Update and populate our knowledge of hooks that are present.
    """
    hooks: list[HookConfig | CollectionConfig] = []

    mounts = {}
    for mount in rtc.main_config.mount:
        LOG.log(VLOG_1, "Processing %s", mount)
        # Prefixes should be unique; they override here
        mounts[mount.prefix] = load_hook_repo(mount)

    for k, v in mounts.items():
        # TODO handle mount prefix
        hooks.extend(v.hook)
        hooks.extend(v.collection)

    hooks.sort(key=lambda h: (h.order, h.name))

    return hooks


def load_hook_repo(mount: WorkspaceMount) -> HookRepoConfig:
    if mount.url:
        # TODO config for a subdir within?
        repo_path = update_local_cache(mount.url, skip_update=False)  # TODO
    else:
        repo_path = Path(mount.base_path, mount.path).resolve()

    rc = HookRepoConfig(repo_path=repo_path)

    LOG.log(VLOG_1, "Loading hooks from %s", repo_path)
    potential_configs = glob("**/ick.toml", root_dir=repo_path, recursive=True)
    potential_configs.extend(glob("**/pyproject.toml", root_dir=repo_path, recursive=True))
    for filename in potential_configs:
        p = Path(repo_path, filename)
        LOG.log(VLOG_1, "Config found at %s", filename)
        if filename.endswith("pyproject.toml"):
            try:
                c = decode_toml(p.read_bytes(), type=WorkspaceHookConfig).tool.ick
            except ValidationError as e:
                # TODO surely there's a cleaner way to validate _inside_
                # but not care if [tool.other] is present...
                if "Object missing required field `ick` - at `$.tool`" in e.args[0]:
                    continue
                if "Object missing required field `tool`" in e.args[0]:
                    continue
                raise
        else:
            c = decode_toml(p.read_bytes(), type=HookRepoConfig)

        # TODO make this prettyprint
        LOG.log(VLOG_2, "Loaded %s", encode_json(c).decode("utf-8"))
        for hook in c.hook:
            hook.hook_path = p.parent
        for collection in c.collection:
            collection.collection_path = p.parent

        # for mount in c.mount:
        #    mount.base_path = p.parent
        rc.inherit(c)

    return rc


def get_impl(hook: HookConfig | CollectionConfig) -> Type[BaseCollection]:
    name = f"ick.languages.{hook.language}"
    if isinstance(hook, CollectionConfig):
        name += "_collection"
    name = name.replace("-", "_")
    __import__(name)
    impl: Type[BaseCollection] = sys.modules[name].Hook  # type: ignore[assignment]
    return impl
