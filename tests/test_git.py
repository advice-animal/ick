from pathlib import Path

import pytest

from ick.git import find_repo_root, update_local_cache


def test_find_repo_root() -> None:
    assert find_repo_root(Path.cwd()) == Path.cwd()
    assert find_repo_root(Path("tests")) == Path.cwd()
    # Doesn't have to really exist
    assert find_repo_root(Path("aaaaaaaaa")) == Path.cwd()
    # This is the fallthrough case
    assert find_repo_root(Path("/")) == Path("/")


@pytest.mark.no_mock_platformdirs
def test_update_local_cache(tmp_path, mocker) -> None:  # type: ignore[no-untyped-def] # FIX ME
    mock_run_cmd = mocker.patch("ick.git.run_cmd", autospec=True)

    rv = update_local_cache("https://github.com/thatch/hobbyhorse", skip_update=False, freeze=False)
    assert rv in (
        Path("~/.cache/ick/hobbyhorse-7f3c0b13").expanduser(),
        Path("~/Library/Caches/ick/hobbyhorse-7f3c0b13").expanduser(),
    )

    mock_run_cmd.assert_called()
