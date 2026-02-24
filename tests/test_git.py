from pathlib import Path

import pytest

from ick.git import _get_local_cache_name, _is_sha, _split_url_ref, find_repo_root, update_local_cache
from ick.sh import run_cmd


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


def test_is_sha() -> None:
    # Valid SHAs
    assert _is_sha("abc1234")  # 7 chars
    assert _is_sha("abc1234def567890abcdef1234567890abcdef12")  # 40 chars
    assert _is_sha("ABCDEF12")  # uppercase
    assert _is_sha("1234567890abcdef")  # mixed

    # Not SHAs
    assert not _is_sha("v1.2.3")  # tag with dots
    assert not _is_sha("develop")  # branch name
    assert not _is_sha("feature/my-branch")  # branch with slash
    assert not _is_sha("abc123")  # too short (6 chars)
    assert not _is_sha("g123456")  # contains non-hex char
    assert not _is_sha("abc1234" * 10)  # too long (>40 chars)


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
def test_update_local_cache_smoke(mocker) -> None:  # type: ignore[no-untyped-def] # FIX ME
    """Smoke test that update_local_cache returns correct paths."""
    mocker.patch("ick.git.run_cmd", autospec=True)

    # Main branch - no @ref suffix
    rv = update_local_cache("https://github.com/thatch/hobbyhorse", skip_update=False, freeze=False)
    assert rv in (
        Path("~/.cache/ick/hobbyhorse-7f3c0b13").expanduser(),
        Path("~/Library/Caches/ick/hobbyhorse-7f3c0b13").expanduser(),
    )

    # Branch with @ref suffix
    rv2 = update_local_cache("https://github.com/thatch/hobbyhorse@develop", skip_update=False, freeze=False)
    assert rv2 in (
        Path("~/.cache/ick/hobbyhorse-develop-7f3c0b13").expanduser(),
        Path("~/Library/Caches/ick/hobbyhorse-develop-7f3c0b13").expanduser(),
    )

    # SHA ref
    rv3 = update_local_cache("https://github.com/thatch/hobbyhorse@abc1234", skip_update=False, freeze=False)
    assert rv3 in (
        Path("~/.cache/ick/hobbyhorse-abc1234-7f3c0b13").expanduser(),
        Path("~/Library/Caches/ick/hobbyhorse-abc1234-7f3c0b13").expanduser(),
    )


def test_update_local_cache_main_clone(tmp_path, mocker) -> None:  # type: ignore[no-untyped-def] # FIX ME
    """Test cloning main branch."""
    mocker.patch("platformdirs.user_cache_dir", return_value=tmp_path)

    result = update_local_cache("https://github.com/thatch/hobbyhorse", skip_update=False, freeze=False)

    # Verify it cloned and checked out main
    branch = run_cmd(["git", "branch", "--show-current"], cwd=result).strip()
    assert branch == "main"


def test_update_local_cache_branch_clone(tmp_path, mocker) -> None:  # type: ignore[no-untyped-def] # FIX ME
    """Test cloning a non-main branch."""
    mocker.patch("platformdirs.user_cache_dir", return_value=tmp_path)

    result = update_local_cache("https://github.com/thatch/hobbyhorse@printf-repr", skip_update=False, freeze=False)

    # Verify it cloned and checked out the branch
    branch = run_cmd(["git", "branch", "--show-current"], cwd=result).strip()
    assert branch == "printf-repr"


def test_update_local_cache_sha_clone(tmp_path, mocker) -> None:  # type: ignore[no-untyped-def] # FIX ME
    """Test cloning a SHA ref."""
    mocker.patch("platformdirs.user_cache_dir", return_value=tmp_path)

    # Use a known commit SHA from hobbyhorse repo (main branch HEAD)
    sha = "aa395a0b1791bed8915dc280be807d6f7573490f"
    result = update_local_cache(f"https://github.com/thatch/hobbyhorse@{sha}", skip_update=False, freeze=False)

    # Verify it cloned and checked out the specific SHA
    head = run_cmd(["git", "rev-parse", "HEAD"], cwd=result).strip()
    assert head == sha
    # Should be in detached HEAD state (no branch)
    branch = run_cmd(["git", "branch", "--show-current"], cwd=result).strip()
    assert branch == ""


def test_update_local_cache_sha_immutable(tmp_path, mocker) -> None:  # type: ignore[no-untyped-def] # FIX ME
    """Test that SHA refs don't get updated (immutable)."""
    mocker.patch("platformdirs.user_cache_dir", return_value=tmp_path)

    # Clone once
    sha = "aa395a0b1791bed8915dc280be807d6f7573490f"
    result = update_local_cache(f"https://github.com/thatch/hobbyhorse@{sha}", skip_update=False, freeze=False)

    head_before = run_cmd(["git", "rev-parse", "HEAD"], cwd=result).strip()

    # Call again - should be a no-op
    result2 = update_local_cache(f"https://github.com/thatch/hobbyhorse@{sha}", skip_update=False, freeze=False)

    head_after = run_cmd(["git", "rev-parse", "HEAD"], cwd=result2).strip()
    assert head_before == head_after
    assert result == result2
