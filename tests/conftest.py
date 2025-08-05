from typing import Iterable

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_loglevel() -> Iterable[None]:
    # logging.getLogger().level = vmodule.VLOG_2
    yield


@pytest.fixture(autouse=True)
def isolated_user_directories(request, tmp_path, mocker) -> None:
    """Automatically mock platformdirs to isolate cache and config.

    Use `@pytest.mark.no_mock_platformdirs` for the rare test that needs the
    real platformdirs implementation.
    """
    if request.node.get_closest_marker("no_mock_platformdirs"):
        return

    def fake_platformdirs(kind):
        def faker(*parts):
            d = tmp_path / kind
            for part in parts:
                d = d / part
            return d

        return faker

    mocker.patch("platformdirs.user_cache_dir", fake_platformdirs("cache"))
    mocker.patch("platformdirs.user_config_dir", fake_platformdirs("config"))
