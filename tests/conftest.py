import pytest


@pytest.fixture(scope="session", autouse=True)
def set_loglevel():
    # logging.getLogger().level = vmodule.VLOG_2
    yield
