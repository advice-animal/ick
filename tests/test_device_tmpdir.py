from pathlib import Path

from ick.device_tmpdir import find_tmpdir


def get_device(fn, follow_symlinks=False):
    fn = str(fn)
    if fn == "/home/user/.cache/uv":
        return 1
    elif fn == "/home/user/.cache/ick":
        return 2
    elif fn == "/tmp":
        return 1
    elif fn == "/root":
        return 1
    elif fn == ".tox":
        return 3
    elif fn == ".git":
        return 3
    else:
        raise NotImplementedError(fn)


def expanduser(p):
    if p.startswith("~"):
        return "/home/user" + p[1:]
    else:
        return p


def test_device_tmpdir(mocker):
    mocker.patch("ick.device_tmpdir._get_device", get_device)
    mocker.patch("ick.device_tmpdir._access_ok", lambda _: True)
    mocker.patch("os.path.expanduser", expanduser)
    mocker.patch("os.makedirs", lambda *x, **y: None)
    mocker.patch("os.mkdir", lambda *x, **y: None)
    mocker.patch("ick.device_tmpdir.HARDCODED_DEFAULTS", ["/tmp", ".tox", ".git"])
    mocker.patch("appdirs.user_cache_dir", lambda *x: Path("/home/user/.cache/ick"))
    assert find_tmpdir(Path("/root")) == Path("/tmp")
    assert find_tmpdir(Path(".git")) == Path(".tox")
