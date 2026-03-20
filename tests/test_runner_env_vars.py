from __future__ import annotations

from pathlib import Path

from ick.config import MainConfig, RulesConfig, RuntimeConfig, Settings
from ick.runner import Runner
from ick.sh import run_cmd
from ick.types_project import Repo


def _init_repo(path: Path) -> None:
    run_cmd(["git", "init"], cwd=path)
    run_cmd(["git", "commit", "--allow-empty", "-m", "init"], cwd=path)


def _make_runner(repo: Repo) -> Runner:
    rtc = RuntimeConfig(
        main_config=MainConfig.DEFAULT,  # type: ignore[attr-defined]
        rules_config=RulesConfig(ruleset=[]),
        settings=Settings(),
    )
    return Runner(rtc, repo)


def test_upstream_url_prefers_upstream_remote(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    run_cmd(["git", "remote", "add", "origin", "https://example.com/origin.git"], cwd=tmp_path)
    run_cmd(["git", "remote", "add", "upstream", "https://example.com/upstream.git"], cwd=tmp_path)
    repo = Repo(tmp_path)
    assert repo.upstream_url == "https://example.com/upstream.git"


def test_upstream_url_falls_back_to_origin(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    run_cmd(["git", "remote", "add", "origin", "https://example.com/origin.git"], cwd=tmp_path)
    repo = Repo(tmp_path)
    assert repo.upstream_url == "https://example.com/origin.git"


def test_upstream_url_empty_when_no_remotes(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    repo = Repo(tmp_path)
    assert repo.upstream_url == ""


def test_runner_sets_ick_repo_path(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    runner = _make_runner(Repo(tmp_path))
    assert runner.ick_env_vars["ICK_REPO_PATH"] == str(tmp_path)


def test_runner_sets_ick_repo_upstream(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    run_cmd(["git", "remote", "add", "origin", "https://example.com/origin.git"], cwd=tmp_path)
    runner = _make_runner(Repo(tmp_path))
    assert runner.ick_env_vars["ICK_REPO_UPSTREAM"] == "https://example.com/origin.git"


def test_runner_omits_ick_repo_upstream_when_no_remotes(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    runner = _make_runner(Repo(tmp_path))
    assert "ICK_REPO_UPSTREAM" not in runner.ick_env_vars
