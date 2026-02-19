from pathlib import Path

import pytest

from ick.git import _get_local_cache_name, _split_url_ref, find_repo_root, update_local_cache


def test_find_repo_root() -> None:
    assert find_repo_root(Path.cwd()) == Path.cwd()
    assert find_repo_root(Path("tests")) == Path.cwd()
    # Doesn't have to really exist
    assert find_repo_root(Path("aaaaaaaaa")) == Path.cwd()
    # This is the fallthrough case
    assert find_repo_root(Path("/")) == Path("/")


def test_get_local_cache_name_sanitizes_ref() -> None:
    # 'main' is omitted from the path
    assert _get_local_cache_name("https://github.com/thatch/hobbyhorse", "main") == "hobbyhorse-7f3c0b13"
    # slashes in ref names are replaced with dashes
    slashed = _get_local_cache_name("https://github.com/thatch/hobbyhorse", "feature/my-feature")
    assert "/" not in slashed
    assert "feature-my-feature" in slashed


def test_split_url_ref() -> None:
    # plain HTTPS URL defaults to main
    assert _split_url_ref("https://github.com/thatch/hobbyhorse") == ("https://github.com/thatch/hobbyhorse", "main")
    # explicit branch suffix
    assert _split_url_ref("https://github.com/thatch/hobbyhorse@develop") == ("https://github.com/thatch/hobbyhorse", "develop")
    # tag with dots
    assert _split_url_ref("https://github.com/thatch/hobbyhorse@v1.2.3") == ("https://github.com/thatch/hobbyhorse", "v1.2.3")
    # short commit hash
    assert _split_url_ref("https://github.com/thatch/hobbyhorse@abc1234") == ("https://github.com/thatch/hobbyhorse", "abc1234")
    # full commit hash
    assert _split_url_ref("https://github.com/thatch/hobbyhorse@abc1234def567890abcdef1234567890abcdef12") == (
        "https://github.com/thatch/hobbyhorse",
        "abc1234def567890abcdef1234567890abcdef12",
    )
    # SSH URL without ref — the @ belongs to the host, not a ref
    assert _split_url_ref("git@github.com:thatch/hobbyhorse") == ("git@github.com:thatch/hobbyhorse", "main")
    # SSH URL with ref
    assert _split_url_ref("git@github.com:thatch/hobbyhorse@develop") == ("git@github.com:thatch/hobbyhorse", "develop")
    # SSH URL with tag
    assert _split_url_ref("git@github.com:thatch/hobbyhorse@v1.2.3") == ("git@github.com:thatch/hobbyhorse", "v1.2.3")


@pytest.mark.no_mock_platformdirs
def test_update_local_cache(tmp_path, mocker) -> None:  # type: ignore[no-untyped-def] # FIX ME
    mock_run_cmd = mocker.patch("ick.git.run_cmd", autospec=True)

    # No @ref suffix — defaults to main, which is omitted from the path
    rv = update_local_cache("https://github.com/thatch/hobbyhorse", skip_update=False, freeze=False)
    assert rv in (
        Path("~/.cache/ick/hobbyhorse-7f3c0b13").expanduser(),
        Path("~/Library/Caches/ick/hobbyhorse-7f3c0b13").expanduser(),
    )

    # @ref suffix — uses that ref and different cache dir
    rv2 = update_local_cache("https://github.com/thatch/hobbyhorse@develop", skip_update=False, freeze=False)
    assert rv2 in (
        Path("~/.cache/ick/hobbyhorse-develop-7f3c0b13").expanduser(),
        Path("~/Library/Caches/ick/hobbyhorse-develop-7f3c0b13").expanduser(),
    )

    mock_run_cmd.assert_called()
