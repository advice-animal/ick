import os

from ick.languages.python import find_uv


def test_find_uv():
    assert os.access(find_uv(), os.X_OK)
