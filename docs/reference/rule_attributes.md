# Ick Toml Reference
The following attributes can be set in an `ick.toml` or `pyproject.toml`.

## `[[ruleset]]` Attributes

### Required (only one can be present)
- `url` (str): A URL to an external repository containing rules
- `path` (str): A local path to a directory containing rules

### Optional Attributes
- `prefix` (str): A prefix to use for the rules from this ruleset. If not specified, it will be derived from the last component of the URL or path.


## `[[rule]]` Attributes

A single `[[rule]]` in an an ick.toml can be configured with the following attributes:

### Required Attributes

- `name` (str): The name of the rule
- `impl` (str): The language in which the rule will be written, see [impls] (TODO)

### Optional Attributes

#### Execution Control
- `scope` (str): The scope of the rule's execution. Available options:
  - `"single-file"`: Runs the rule on a single file (default).
  - `"project"`: Runs the rule on the whole project.
  - `"repo"`: Runs the rule on the whole repository.
- `command` (str | list[str]): The command to execute for this rule. 
- `success` (str): How to determine if the rule execution was successful. Defaults to `"exit-status"`. Available options:
  - `"exit-status"`: Success is determined by the command's exit status
  - `"no-output"`: Success is determined by the absence of output

#### Risk and Timing
- `risk` (str): The risk level of running this rule. In other words, how likely it is to break something. Available options:
  - `"high"`: Highest risk level (default)
  - `"med"`: Medium risk level
  - `"low"`: Lowest risk level
- `urgency` (str): The urgency level of the rule. Defaults to `"later"`. Available options:
  - `"manual"`: The rule is not intended to be run automatically and should be run by choice.
  - `"later"`: Can be addressed later
  - `"soon"`: Should be addressed soon
  - `"now"`: Needs immediate attention
  - `"not_supported"`: This rule no longer applies to the current context.
- `order` (int): If a rule needs to run before another, define that here. Rules with lower orders will be run before rules with higher orders. Intended to be an integer from 0-100, and defaults to 50. 
- `hours` (int): An estimate on how many hours of manual work will be required after running this codemod.

#### Content Processing
- `data` (str): TODO
- `search` (str): TODO
- `replace` (str): TODO

#### Dependencies and Paths
- `deps` (list[str]): List of dependencies for the rule.

#### Input/Output
These all follow `.gitignore`-like glob patterns, like `*.py`.
- `inputs` (Sequence[str]): List of input files/patterns.
- `outputs` (Sequence[str]): List of output files/patterns. 
- `extra_inputs` (Sequence[str]): Additional input files/patterns.

#### Metadata
- `description` (str): Description of what the rule does. Will print with `ick list-rules`.
- `contact` (str): Contact information for the rule maintainer: email, Slack channel, etc.