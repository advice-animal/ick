# Ick Toml Reference
The following attributes can be set in an `ick.toml` or `pyproject.toml`.

## `[[ruleset]]` Attributes

### Required (at least one)
- `url` (str): A URL to an external repository containing rules
- `path` (str): A local path to a directory containing rules

### Optional Attributes
- `prefix` (str): A prefix to use for the rules from this mount. If not specified, it will be derived from the last component of the URL or path.
- `base_path` (Path): The directory of the config file that referenced this ruleset. We set this as the `ick.toml`'s parent path.
- `repo`: No clue how to best describe nor format this yet.

## `[[rule]]` Attributes

A `RuleConfig` (defined in `ick/config/rules.py`) defines the configuration for a single `[[rule]]` in the system. Here are all available attributes:

### Required Attributes

- `name` (str): The name of the rule
- `impl` (str): The language the rule will be 

### Optional Attributes

#### Execution Control
- `scope` (Scope): The scope of the rule's execution. Defaults to `SINGLE_FILE`. Available options:
  - `SINGLE_FILE`: Runs the rule on a single file.
  - `PROJECT`: Runs the rule on the whole project.
  - `REPO`: Runs the rule on the whole repository.
- `command` (str | list[str]): The command to execute for this rule. 
- `success` (Success): How to determine if the rule execution was successful. Defaults to `EXIT_STATUS`. Available options:
  - `EXIT_STATUS`: Success is determined by the command's exit status
  - `NO_OUTPUT`: Success is determined by the absence of output

#### Risk and Timing
- `risk` (Risk): The risk level of running this rule. In other words, how likely it is to break something. Defaults to `HIGH`. Available options:
  - `HIGH`: Highest risk level
  - `MED`: Medium risk level
  - `LOW`: Lowest risk level
- `urgency` (Urgency): The urgency level of the rule. Defaults to `LATER`. Available options:
  - `MANUAL`: Requires manual intervention
  - `LATER`: Can be addressed later
  - `SOON`: Should be addressed soon
  - `NOW`: Needs immediate attention
  - `NOT_SUPPORTED`: Not supported in the current context
- `order` (int): No clue.
- `hours` (int): An estimate on how many hours of manual work will be required after running this codemod.

#### Content Processing
- `data` (str): No clue
- `search` (str): No clue
- `replace` (str): No clue

#### Dependencies and Paths
- `deps` (list[str]): List of dependencies for the rule.
- `test_path` (Path): Path to the test file for the rule.
- `script_path` (Path): Path to the script file for the rule.
- `qualname` (str): The name of the rule within its respective repository. 

#### Input/Output
These all follow `.gitignore`-like glob patterns, like `*.py`.
- `inputs` (Sequence[str]): List of input files/patterns.
- `outputs` (Sequence[str]): List of output files/patterns. 
- `extra_inputs` (Sequence[str]): Additional input files/patterns.

#### Metadata
- `description` (str): Description of what the rule does. Will print with `ick list-rules`.
- `contact` (str): Contact information for the rule maintainer.