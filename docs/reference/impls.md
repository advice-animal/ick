# Rule implementation languages

Architecturally, ick can run rules written in many languages.  This pages
documents the currently supported languages.

## Python

Rules implemented in Python can be structured two ways: with code in a separate
.py file, or with code directly in the ick.toml file.

### Separate Python file

The usual approach is a separate .py file.  The file will be named after the
rule.  Your rule repo could look like this:

```text
webapps
├── async_routes.py
└── ick.toml
```

The ick.toml would look like:

```toml
[[rule]]
name = "async_routes"
impl = "python"
urgency = "now"
inputs = ["*.py"]
description = "Detects incorrect async route handlers"
```

The Python file has the same name as the rule itself and is found implicitly.
`webapps` is the sub-namespace of rules, so this rule's full name might be
`apps/webapps/async_routes`.

### Inline Python code

To provide code in the ick.toml file, add the Python code in the multi-line
`data` attribute:

```toml
[[rule]]
name = "find_todos"
impl = "python"
data = """
    import sys

    ok = True
    for fname in sys.argv[1:]:
        with open(fname) as f:
            for line in f:
                if "# TODO" in line:
                    print(line)
                    ok = False
    sys.exit(0 if ok else 99)
    """
```

### Dependencies

Ick creates and manages virtual environments for running your Python rule. You
can specify dependencies to install in the `deps` setting:

```toml
[[rule]]
name = "yaml_something"
impl = "python"
deps = ["PyYAML"]
```

## Shell

Shell rules can specify code two way: as a command line or as a full shell
script.

### Command line

The `command` setting of a shell rule can be either a single string, the
complete command line to run, or a list of strings to skip shell parsing.

[Do we really want both forms? What does it gain us?]

### Shell script

The `data` setting of a shell rule is a multi-line string, a complete shell
script.

[What is the advantage of having both command-line and script forms?]

## Adding another implementation language

We are interested in supporing other implementation languages.  Get in touch!
