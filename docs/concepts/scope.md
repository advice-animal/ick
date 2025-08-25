# Scopes

Rule scopes determine how rules are invoked on the repo content.

Regardless of the scope, rules are run in temporary directories with copies of
the files ick thinks it needs based on the scope and the `inputs` setting.  Your
rule cannot access files other than those.

You only have access to the files you specify as `input=` -- even specifying
inefficient globs like `*.py` or `**/scripts/*` is better than leaving it unset
which assumes every file gets read.


## File scope

```toml
[[rule]]
# ...
scope = "file"
```

This is the default scope. Rules with this scope can operate in parallel on
single files and presumably don't have any other files as input that would cause
complex dependencies.

Rules specify files of interest with their `inputs` setting.  The rule will be
run with a list of file paths as command-line arguments.  Ick decides how many
files to pass to each invocation of the rule.  Your rule may be run multiple
times, each passed a different list of files.


## Repo

```toml
[[rule]]
# ...
scope = "repo"
```

This rule runs once per repo, in a temporary directory with a copy of the repo.
Use this scope if your rule needs to work across a number of different files at
once.


## Project

This rule runs once per detected [project](projects.html) (see `ick
list-projects`) and is the typical way you'll want to edit project metadata if
you need to edit multiple files at once.

Project scope is different than repo scope in the case of repos with multiple
projects.
