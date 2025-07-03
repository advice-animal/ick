# This file is /tmp/foo/move_isort_cfg.py

from pathlib import Path

import imperfect
import tomlkit

if __name__ == "__main__":
    cfg = Path("isort.cfg")
    toml = Path("pyproject.toml")
    if cfg.exists() and toml.exists():
        # The main aim is to reduce the number of files by one
        with open(cfg) as f:
            cfg_data = imperfect.parse_string(f.read())
        with open(toml) as f:
            toml_data = tomlkit.load(f)
        isort_table = toml_data.setdefault("tool", {}).setdefault("isort", {})
        isort_table.update(cfg_data["settings"])
        toml.write_text(tomlkit.dumps(toml_data))
        cfg.unlink()
