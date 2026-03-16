import os
import tempfile
from pathlib import Path


def check_writable_dirs() -> str | None:
    """
    Returns an error message if ick's required writable dirs are not writable,
    otherwise returns None.
    """
    import platformdirs

    for dir_path_str in (
        platformdirs.user_cache_dir("ick", "advice-animal"),
        tempfile.gettempdir(),
    ):
        dir_path = Path(dir_path_str)
        # Walk up to the first existing ancestor and check writability
        check = dir_path
        while not check.exists():
            check = check.parent
        if not os.access(check, os.W_OK):
            return f"{dir_path} is not writable (checked {check})"

    return None
