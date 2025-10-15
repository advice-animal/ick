import inspect
from pathlib import Path
from typing import Optional, Sequence

from tomlkit import aot, document, item


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
                    """
                    pass
                if __name__ == "__main__":
                    main()
                ''')

        case "shell":  # Unreachable right now but will be accessible soon
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
    description: Optional[str] = None,
) -> None:
    ick_config_location = target_path / "ick.toml"

    config_dict = {}
    config_dict["name"] = rule_name
    config_dict["impl"] = impl
    config_dict["urgency"] = urgency

    if inputs:  # This could be an empty tuple
        config_dict["inputs"] = inputs

    if description is not None:
        config_dict["description"] = description

    rule_table = aot()
    rule_doc = document()
    rule_table.append(item(config_dict))
    rule_doc.append("rule", rule_table)

    # The best way to preserve existing formatting in the ick.toml file is to never touch it 
    with open(ick_config_location, "a") as f:
        f.write("\n")
        f.write(rule_doc.as_string())

    print(f"Created rule config at {ick_config_location}")


def create_test_structure(target_path: Path, rule_name: str) -> None:
    """Create the test directory structure with a dummy test."""
    tests_dir = target_path / "tests"
    rule_test_dir = tests_dir / rule_name
    main_test_dir = rule_test_dir / "main"
    input_dir = main_test_dir / "input"
    output_dir = main_test_dir / "output"

    # Create directories
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Created dummy test with input and output in {main_test_dir}")


def add_rule_structure(
    rule_name: str,
    target_path: Path,
    impl: str,
    inputs: Sequence[str],
    urgency: str,
    description: Optional[str] = None,
) -> None:
    """
    Generate the file structure for a new rule in the given target directory.

    Parameters:
        rule_name (str): The name of the rule to create.
        target_dir (str): Path to the directory in which to create the rule.
        inputs (Optional[List[str]]): A list of input files (if any) that the rule will use.
        urgency (Optional[Urgency]): The urgency level for the rule.
        description (Optional[str]): An optional description for the rule.
    """
    target_path.mkdir(parents=True, exist_ok=True)

    write_rule_config_table(
        target_path,
        rule_name=rule_name,
        impl=impl,
        inputs=inputs,
        urgency=urgency,
        description=description,
    )
    create_test_structure(target_path=target_path, rule_name=rule_name)
    create_rule_file(rule_name=rule_name, impl=impl, target_path=target_path)

    print(f"\nRule '{rule_name}' has been created successfully!")
