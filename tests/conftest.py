from typing import Iterable

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_loglevel() -> Iterable[None]:
    # logging.getLogger().level = vmodule.VLOG_2
    yield
