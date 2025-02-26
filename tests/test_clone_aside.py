from pathlib import Path

from ick.clone_aside import CloneAside, run_cmd


def test_no_modified_files(tmp_path):
    run_cmd(["git", "init"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("# Hello\n")
    run_cmd(["git", "add", "README.md"], cwd=tmp_path)
    run_cmd(["git", "commit", "-a", "-m", "root"], cwd=tmp_path)

    with CloneAside(tmp_path) as f:
        assert Path(f, "README.md").read_text() == "# Hello\n"


def test_untracked_files(tmp_path):
    run_cmd(["git", "init"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("# Hello\n")
    run_cmd(["git", "add", "README.md"], cwd=tmp_path)
    run_cmd(["git", "commit", "-a", "-m", "root"], cwd=tmp_path)
    (tmp_path / "misc.md").write_text("# foo\n")  # untracked

    with CloneAside(tmp_path) as f:
        assert Path(f, "README.md").read_text() == "# Hello\n"
        assert Path(f, "misc.md").read_text() == "# foo\n"


def test_modified_files(tmp_path):
    run_cmd(["git", "init"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("# Hello\n")
    run_cmd(["git", "add", "README.md"], cwd=tmp_path)
    run_cmd(["git", "commit", "-a", "-m", "root"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("# Hello Modified\n")

    with CloneAside(tmp_path) as f:
        assert Path(f, "README.md").read_text() == "# Hello Modified\n"


def test_staged_files(tmp_path):
    run_cmd(["git", "init"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("# Hello\n")
    run_cmd(["git", "add", "README.md"], cwd=tmp_path)
    run_cmd(["git", "commit", "-a", "-m", "root"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("# Hello Modified\n")
    run_cmd(["git", "add", "README.md"], cwd=tmp_path)

    with CloneAside(tmp_path) as f:
        assert Path(f, "README.md").read_text() == "# Hello Modified\n"
