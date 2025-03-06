from __future__ import annotations

from fnmatch import fnmatch
from logging import getLogger
from typing import Any

from keke import ktrace

from ick_protocol import Finished, Modified

from .clone_aside import CloneAside
from .config import HookConfig
from .config.hook_repo import discover_hooks, get_impl
from .project_finder import find_projects

LOG = getLogger(__name__)


class Runner:
    def __init__(self, rtc, repo, explicit_project=None):
        self.rtc = rtc
        self.hooks = discover_hooks(rtc)
        self.repo = repo
        # TODO there's a var on repo to store this...
        self.projects = find_projects(repo, repo.zfiles, self.rtc.main_config)
        assert explicit_project is None
        self.explicit_project = explicit_project

    def iter_hook_impl(self):
        for hook in self.hooks:
            # TODO the isinstance is here because of handling collections,
            # which may be overcomplicating things this early...
            if isinstance(hook, HookConfig):
                if hook.urgency < self.rtc.filter_config.min_urgency:
                    continue
            i = get_impl(hook)(hook, self.rtc)
            yield i

    def run(self) -> Any:
        for impl in self.iter_hook_impl():
            if hasattr(impl, "hook_config"):
                name = impl.hook_config.name
            else:
                name = repr(impl)
            print(name, "start")
            impl.prepare()
            print(name, "prepared")
            for p in self.projects:
                try:
                    resp = []
                    with CloneAside(self.repo.root) as tmp:
                        with impl.work_on_project(tmp) as work:
                            # TODO multiple hook names (in a collection) happen at once?
                            for h in impl.list().hook_names:
                                # TODO only if files exist
                                # TODO only if files have some contents
                                filenames = self.repo.zfiles.rstrip("\0").split("\0")
                                assert "" not in filenames
                                # TODO %.py different than *.py once we go parallel
                                if impl.hook_config.inputs:
                                    filenames = [f for f in filenames if any(fnmatch(f, x) for x in impl.hook_config.inputs)]

                                resp.extend(work.run("ZZZ", filenames))
                except Exception as e:
                    resp = [Finished("ZZZ", error=True, message=repr(e))]
                print("  ", p.subdir)
                for r in resp:
                    if isinstance(r, Modified):
                        print("    ", r.filename, r.diffstat)
                    else:
                        print("    ", r)

    @ktrace()
    def echo_hooks(self) -> None:
        d = {}
        for impl in self.iter_hook_impl():
            impl.prepare()
            for hook in impl.list().hook_names:
                d.setdefault(impl.hook_config.urgency, []).append(hook)

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
