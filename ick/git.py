from __future__ import annotations

import posixpath
from hashlib import sha256
from logging import getLogger
from pathlib import Path
from urllib.parse import urlparse

from click import ClickException

from .sh import run_cmd

LOG = getLogger(__name__)


def _get_local_cache_name(url: str) -> str:
    # this isn't intended to be "secure" and we could just as easily use crc32
    # but starting with a secure hash keeps linters quiet.
    url_hash = sha256(url.encode()).hexdigest()

    path = urlparse(url).path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    repo_name = posixpath.basename(path)
    return f"{repo_name}-{url_hash[:8]}"


def update_local_cache(url: str, skip_update: bool, freeze: bool = False) -> Path:
    import appdirs

    cache_dir = Path(appdirs.user_cache_dir("ick", "advice-animal")).expanduser()
    local_checkout = cache_dir / _get_local_cache_name(url)
    freeze_name = local_checkout / ".git" / "freeze"
    if not local_checkout.exists():
        run_cmd(["git", "clone", url, local_checkout])
    elif not skip_update:
        if not freeze_name.exists():
            run_cmd(["git", "pull"], cwd=local_checkout)
    if freeze:
        freeze_name.touch()
    return local_checkout


# This function is verbatim from https://github.com/omnilib/trailrunner/blob/main/trailrunner/core.py
def find_repo_root(path: Path) -> Path:
    """
    Find the project root, looking upward from the given path.

    Looks through all parent paths until either the root is reached, or a directory
    is found that contains any of :attr:`ROOT_MARKERS`.

    If one is not found, return the original path.
    """
    real_path = path.resolve()

    parents = list(real_path.parents)
    if real_path.is_dir():
        parents.insert(0, real_path)

    for parent in parents:
        if (parent / ".git").exists():
            return parent

    # TODO what's the right fallback here?  I'd almost rather an exception.
    return path


def head(path: Path) -> str:
    """
    Returns the current head (branch)
    """
    git_head_path = path / ".git" / "HEAD"
    if not git_head_path.exists():
        raise ClickException(f"Not a git repo: {path}")
    return git_head_path.read_text().strip().split("/")[-1]
