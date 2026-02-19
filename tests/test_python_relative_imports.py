"""Test that Python rules can use relative imports."""

from pathlib import Path

import pytest

from ick.config import RuleConfig
from ick.rules.python import Rule, path_to_module


def test_python_relative_imports(tmp_path: Path) -> None:
    """Test that Python rules can import from their own repo using relative imports."""
    # Create a simple repo structure with a helper module and a rule that imports it
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Create __init__.py to make it a package
    (repo_path / "__init__.py").write_text("")

    # Create helper module
    (repo_path / "helper.py").write_text("""
def greet():
    return "Hello from helper!"
""")

    # Create the main script that uses relative import
    script_path = repo_path / "main.py"
    script_path.write_text("""
from .helper import greet
print(greet())
""")

    rule = Rule(
        RuleConfig(
            name="main",
            impl="python",
            script_path=script_path.with_suffix(""),  # without .py
            repo_path=repo_path,
            qualname="test/main",
        ),
    )

    # Verify the command uses -m flag for module execution
    assert "-m" in rule.command_parts
    assert "main" in rule.command_parts

    # Verify PYTHONPATH includes repo_path
    assert str(repo_path) in rule.command_env["PYTHONPATH"]


def test_python_module_path_conversion() -> None:
    """Test that script paths are correctly converted to module paths."""
    repo_path = Path("/tmp/repo")
    script_path = repo_path / "subdir" / "myscript"

    rule = Rule(
        RuleConfig(
            name="myscript",
            impl="python",
            script_path=script_path,
            repo_path=repo_path,
            qualname="test/subdir/myscript",
        ),
    )

    # Should use -m with dotted module path
    assert "-m" in rule.command_parts
    # The module path should be subdir.myscript
    assert "subdir.myscript" in rule.command_parts


def test_path_to_module_valid() -> None:
    """Test valid module path conversions."""
    assert path_to_module(Path("script.py")) == "script"
    assert path_to_module(Path("subdir/script.py")) == "subdir.script"
    assert path_to_module(Path("a/b/c.py")) == "a.b.c"
    assert path_to_module(Path("my_script.py")) == "my_script"
    assert path_to_module(Path("MyScript123.py")) == "MyScript123"


def test_path_to_module_invalid() -> None:
    """Test that invalid module names are rejected."""
    # Hyphens are not valid in Python identifiers
    with pytest.raises(AssertionError, match=r"Path.*my-script\.py.*contains invalid Python identifiers"):
        path_to_module(Path("my-script.py"))

    # Names starting with numbers are not valid
    with pytest.raises(AssertionError, match=r"Path.*123script\.py.*contains invalid Python identifiers"):
        path_to_module(Path("123script.py"))

    # Special characters are not valid
    with pytest.raises(AssertionError, match=r"Path.*my@script\.py.*contains invalid Python identifiers"):
        path_to_module(Path("my@script.py"))
