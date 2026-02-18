from __future__ import annotations

import posixpath
from hashlib import sha256
from logging import getLogger
from pathlib import Path
from urllib.parse import urlparse

from .sh import run_cmd

LOG = getLogger(__name__)

DEFAULT_BRANCH_NAME = "main"


def _split_url_ref(url: str) -> tuple[str, str]:
    """Split a URL of the form `url@ref` into (url, ref).

    Defaults to "main" when no @ref suffix is present.  Avoids splitting on
    the @ in SSH URLs like ``git@github.com:foo/bar`` by checking whether the
    text after the last @ looks like a hostname fragment (contains ':').
    """
    base, _, suffix = url.rpartition("@")
    if base and ":" not in suffix:
        return base, suffix
    return url, DEFAULT_BRANCH_NAME


def _get_local_cache_name(url: str, ref: str) -> str:
    # this isn't intended to be "secure" and we could just as easily use crc32
    # but starting with a secure hash keeps linters quiet.
    url_hash = sha256(url.encode()).hexdigest()

    path = urlparse(url).path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    repo_name = posixpath.basename(path)
    if ref == DEFAULT_BRANCH_NAME:
        return f"{repo_name}-{url_hash[:8]}"
    safe_ref = ref.replace("/", "-")
    return f"{repo_name}-{safe_ref}-{url_hash[:8]}"


def update_local_cache(url: str, *, skip_update: bool, freeze: bool = False) -> Path:
    import platformdirs
    from filelock import FileLock

    clean_url, ref = _split_url_ref(url)
    cache_dir = Path(platformdirs.user_cache_dir("ick", "advice-animal")).expanduser()
    local_checkout = cache_dir / _get_local_cache_name(clean_url, ref)
    freeze_name = local_checkout / ".git" / "freeze"
    with FileLock(local_checkout.with_suffix(".lock")):
        if not local_checkout.exists():
            # HEAD will be detached on subsequent updates (see below)
            # TODO: consider --depth 1 since we don't need full history.
            clone_cmd = ["git", "clone", "--single-branch", "--branch", ref]
            if ref != DEFAULT_BRANCH_NAME:
                # Reuse objects from the main cache dir to save bandwidth;
                # we assume git will silently continue if the dir doesn't exist.
                clone_cmd += ["--reference", str(cache_dir / _get_local_cache_name(clean_url, DEFAULT_BRANCH_NAME))]
            run_cmd(clone_cmd + [clean_url, local_checkout])
        elif not skip_update:
            if not freeze_name.exists():
                run_cmd(["git", "fetch", "origin"], cwd=local_checkout)
                # Detaches HEAD to the exact state of the remote ref
                run_cmd(["git", "checkout", "-f", f"origin/{ref}"], cwd=local_checkout)
        if freeze:
            freeze_name.touch()
    return local_checkout


def find_repo_root(path: Path) -> Path:
    """
    Find the project root, looking upward from the given path.

    Looks through parent paths until either the root is reached, or a .git
    directory is found.

    If one is not found, return the original path.
    """
    real_path = path.resolve()

    parents = list(real_path.parents)
    if real_path.is_dir():
        parents.insert(0, real_path)

    for parent in parents:
        if (parent / ".git").exists():
            LOG.debug(f"Found a git repo at {parent}/.git")
            return parent

    # TODO what's the right fallback here?  I'd almost rather an exception.
    return path
