from pathlib import Path

import pytest
from click.testing import CliRunner

from ick.cmdline import main


@pytest.mark.no_mock_platformdirs
def test_show_main_config_location() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["show-main-config-location"], catch_exceptions=False)
    assert result.exit_code == 0
    assert Path(result.output.strip()) in (
        Path("~/.config/ick/ick.toml").expanduser(),
        Path("~/Library/Application Support/ick/ick.toml").expanduser(),
    )
