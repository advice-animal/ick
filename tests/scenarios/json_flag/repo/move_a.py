from pathlib import Path

import imperfect  # type: ignore[import-not-found] # FIX ME
import tomlkit

if __name__ == "__main__":
    a = Path("file_a.cfg")
    b = Path("file_b.toml")
    if a.exists() and b.exists():
        # The main aim is to reduce the number of files by one
        with open(a) as f:
            cfg_data = imperfect.parse_string(f.read())
        with open(b) as f:
            toml_data = tomlkit.load(f)
        isort_table = toml_data.setdefault("tool", {}).setdefault("isort", {})
        isort_table.update(cfg_data["settings"])
        b.write_text(tomlkit.dumps(toml_data))
        a.unlink()
