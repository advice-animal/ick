from __future__ import annotations

import sys
from glob import glob
from logging import getLogger
from pathlib import Path
from posixpath import dirname
from typing import Sequence, Type

from keke import ktrace
from msgspec import ValidationError
from msgspec.json import encode as encode_json
from msgspec.toml import decode as decode_toml
from vmodule import VLOG_1, VLOG_2

from ..base_language import BaseCollection
from ..git import update_local_cache
from . import CollectionConfig, HookConfig, HookRepoConfig, Mount, PyprojectHooksConfig, RuntimeConfig

LOG = getLogger(__name__)


@ktrace()
def discover_hooks(rtc: RuntimeConfig) -> Sequence[HookConfig | CollectionConfig]:
    """
    Returns list of hooks in the order that they would be applied.

    It is the responsibility of the caller to filter and handle things like
    project-level ignores.
    """
    hooks: list[HookConfig | CollectionConfig] = []

    mounts = {}
    for mount in rtc.hooks_config.mount:
        LOG.log(VLOG_1, "Processing %s", mount)
        # Prefixes should be unique; they override here
        mounts[mount.prefix] = load_hook_repo(mount)

    for k, v in mounts.items():
        # TODO handle mount prefix
        hooks.extend(v.hook)
        hooks.extend(v.collection)

    hooks.sort(key=lambda h: (h.order, h.name))

    return hooks


@ktrace("mount.url", "mount.path")
def load_hook_repo(mount: Mount) -> HookRepoConfig:
    if mount.url:
        # TODO config for a subdir within?
        repo_path = update_local_cache(mount.url, skip_update=False)  # TODO
    else:
        repo_path = Path(mount.base_path, mount.path).resolve()

    rc = HookRepoConfig(repo_path=repo_path)

    LOG.log(VLOG_1, "Loading hooks from %s", repo_path)
    # We use a regular glob here because it might not be from a git repo, or
    # that repo might be modified.  It also will let us more easily refer to a
    # subdir in the future.
    potential_configs = glob("**/ick.toml", root_dir=repo_path, recursive=True)
    potential_configs.extend(glob("**/pyproject.toml", root_dir=repo_path, recursive=True))
    for filename in potential_configs:
        p = Path(repo_path, filename)
        LOG.log(VLOG_1, "Config found at %s", filename)
        if p.name == "pyproject.toml":
            c = load_pyproject(p, p.read_bytes())
        else:
            c = load_regular(p, p.read_bytes())

        if not c.hook and not c.collection:
            continue

        LOG.log(VLOG_2, "Loaded %s", encode_json(c).decode("utf-8"))
        base = dirname(filename).lstrip("/")
        if base:
            base += "/"
        for hook in c.hook:
            hook.qualname = base + hook.name
            if (p.parent / hook.name).exists():
                hook.test_path = repo_path / base / hook.name / "tests"
            else:
                hook.test_path = repo_path / base / "tests" / hook.name
        for collection in c.collection:
            collection.collection_path = p.parent

        rc.inherit(c)

    return rc


def load_pyproject(p: Path, data: bytes) -> HookRepoConfig:
    try:
        c = decode_toml(data, type=PyprojectHooksConfig).tool.ick
    except ValidationError as e:
        # TODO surely there's a cleaner way to validate _inside_
        # but not care if [tool.other] is present...
        if "Object missing required field `ick` - at `$.tool`" in e.args[0]:
            return HookRepoConfig()
        if "Object missing required field `tool`" in e.args[0]:
            return HookRepoConfig()
        raise
    return c


def load_regular(p: Path, data: bytes) -> HookRepoConfig:
    return decode_toml(data, type=HookRepoConfig)


@ktrace("hook.language")
def get_impl(hook: HookConfig | CollectionConfig) -> Type[BaseCollection]:
    name = f"ick.languages.{hook.language}"
    if isinstance(hook, CollectionConfig):
        name += "_collection"
    name = name.replace("-", "_")
    __import__(name)
    impl: Type[BaseCollection] = sys.modules[name].Language  # type: ignore[assignment]
    return impl
