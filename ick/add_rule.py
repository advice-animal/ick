import inspect
import json
from pathlib import Path
from typing import Optional, Sequence


def create_rule_file(rule_name: str, target_path: Path, impl: str) -> None:
    """Create a Python implementation file for the rule."""
    match impl:
        case "python":
            rule_file = target_path / f"{rule_name}.py"
            template = inspect.cleandoc(f'''
                def main():
                    """
                    Main function for the {rule_name} rule.
                    This is a template implementation. Replace this with your actual rule logic.
                    See how to write a rule at
                    https://ick.readthedocs.io/en/latest/writing-rules/overview.html
                    """


                if __name__ == "__main__":
                    main()
                ''')

        case "shell":  # pragma: nocover
            # Unreachable right now but will be accessible soon
            pass

        case _:
            raise ValueError(f"Invalid impl: {impl}")

    rule_file.write_text(template)
    print(f"Created rule implementation at {rule_file}")


def write_rule_config_table(
    target_path: Path,
    rule_name: str,
    impl: str,
    inputs: Sequence[str],
    urgency: str,
    scope: str,
    description: Optional[str] = None,
) -> None:
    ick_config_location = target_path / "ick.toml"

    # Build lines for the rule entry
    rule_lines = ["[[rule]]", f'name = "{rule_name}"', f'impl = "{impl}"', f'urgency = "{urgency}"', f'scope = "{scope}"']

    if inputs:
        rule_lines.append(f"inputs = {json.dumps(list(inputs))}")

    if description:
        rule_lines.append(f'description = "{description}"')

    ick_rule_template = "\n".join(rule_lines) + "\n"

    # The best way to preserve existing formatting in the ick.toml file is to never touch it
    preprend_newline = ick_config_location.exists() and not ick_config_location.read_text().endswith("\n\n")
    with open(ick_config_location, "a") as f:
        if preprend_newline:
            f.write("\n")

        f.write(ick_rule_template)

    print(f"Created rule config at {ick_config_location}")


def create_test_structure(target_path: Path, rule_name: str) -> None:
    """Create the test directory structure with two dummy tests (test1 and test2)."""
    for test_name in ["test1", "test2"]:
        test_dir = target_path / "tests" / rule_name / test_name
        input_dir = test_dir / "input"
        output_dir = test_dir / "output"

        # Create directories
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Created dummy tests test1 and test2 with input and output in {target_path / 'tests' / rule_name}")


def add_rule_structure(
    rule_name: str,
    target_path: Path,
    impl: str,
    inputs: Sequence[str],
    urgency: str,
    scope: str,
    description: Optional[str] = None,
) -> None:
    """
    Generate the file structure for a new rule in the given target directory.
    """
    target_path.mkdir(parents=True, exist_ok=True)

    write_rule_config_table(
        target_path,
        rule_name=rule_name,
        impl=impl,
        inputs=inputs,
        urgency=urgency,
        scope=scope,
        description=description,
    )
    create_test_structure(target_path=target_path, rule_name=rule_name)
    create_rule_file(rule_name=rule_name, impl=impl, target_path=target_path)

    print(f"\nRule '{rule_name}' has been created successfully!")
