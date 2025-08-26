# Ick TOML reference

The following attributes can be set in an `ick.toml` or `pyproject.toml`.

## `[[ruleset]]` attributes

### Required (only one can be present)

- `url` (str): A URL to an external repository containing rules
- `path` (str): A local path to a directory containing rules

### Optional attributes

- `prefix` (str): A prefix to use for the rules from this ruleset. If not
  specified, it will be derived from the last component of the URL or path.


## `[[rule]]` attributes

A single `[[rule]]` in an ick.toml can be configured with the following attributes:

### Required attributes

- `name` (str): The name of the rule
- `impl` (str): The language in which the rule will be written, see [Rule
    implementation languages](impls.html).

### Optional attributes

#### Execution control

- `scope` (str): The scope of the rule's execution. Available options:
  - `"file"`: Runs the rule on a single file (default).
  - `"project"`: Runs the rule on the whole project.
  - `"repo"`: Runs the rule on the whole repository.
- `command` (str | list[str]): The command to execute for this rule.
- `data` (str): Direct data for the rule, such as Python or shell source.
- `success` (str): How to determine if the rule execution was successful.
  Defaults to `"exit-status"`. Available options:
  - `"exit-status"`: Success is determined by the command's exit status
  - `"no-output"`: Success is determined by the absence of output

#### Risk and timing

- `risk` (str): The risk level of running this rule. In other words, how likely
  it is to break something. Available options:
  - `"high"`: Highest risk level (default)
  - `"med"`: Medium risk level
  - `"low"`: Lowest risk level
- `urgency` (str): The urgency level of the rule. Defaults to `"later"`. Available options:
  - `"optional"`: The rule is optional and won't be run by default. You can
      choose to run it by specifying the rule explicitly
  - `"later"`: Can be addressed later
  - `"soon"`: Should be addressed soon
  - `"now"`: Don't put this off
  - `"urgent"`: The rule has identified your software is out of support
- `order` (int): If a rule needs to run before another, define that here.
  Rules with lower orders will be run before rules with higher orders.
  Intended to be an integer from 0-100, and defaults to 50.
- `hours` (int): An estimate on how many hours of manual work will be required
  after running this codemod.

#### Content processing

- `search` (str): TODO
- `replace` (str): TODO

#### Dependencies and paths

- `deps` (list[str]): List of dependencies for the rule.

#### Input/output

These all follow `.gitignore`-like glob patterns, like `*.py`.
- `inputs` (Sequence[str]): List of input files/patterns.
- `outputs` (Sequence[str]): List of output files/patterns.
- `extra_inputs` (Sequence[str]): Additional input files/patterns.

#### Metadata

- `description` (str): Description of what the rule does. Will print with `ick list-rules`.
- `contact` (str): Contact information for the rule maintainer: email, Slack channel, etc.
