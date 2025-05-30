import subprocess
from contextlib import ExitStack
from pathlib import Path

from ..device_tmpdir import find_tmpdir
from ..sh import run_cmd


class GitWorkdirFactory:
    def __init__(self, parent: Path, exit_stack: ExitStack) -> None:
        self._parent = parent
        self._clones_dir = find_tmpdir(near=parent)
        self._wc_patch = self._clones_dir / "wc.patch"

        with open(self._wc_patch, "wb") as f:
            subprocess.check_call(["git", "diff", "--no-renames", "--binary"], cwd=self._parent, stdout=f)
            # git ls-files --others --exclude-standard -z | xargs -0 -n 1 git --no-pager diff /dev/null

        # exit_stack.enter_context(in_tmpdir(near=parent))

    def __call__(self):
        return GitWorkdir(self, self._clones_dir, self._wc_patch)


class GitWorkdir:
    def __init__(self, clones_dir: Path, wc_patch: Path) -> None:
        self._clones_dir = clones_dir
        self._wc_patch = wc_patch

    def __enter__(self):
        # come up with a temp name in clones_dir
        this_dir = self._clones_dir / "abc"
        run_cmd(["git", "apply", "--index", self._wc_patch], cwd=this_dir)

        run_cmd(["git", "clone", self._parent, self._clone_dir])
        ...
        run_cmd(["git", "diff", "--binary"], cwd=self._parent)
