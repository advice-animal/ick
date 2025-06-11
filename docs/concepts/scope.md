# Scope

## Single-File Scope

```toml
[[rule]]
# ...
scope = "single-file"
```

This is the default scope, and behaves closest to pre-commit. Rules with this
scope operate in parallel on single files and presumably don't have any other
files as input that would cause complex dependencies.  If you do need some other
files, for example you know you'll need to read `pyproject.toml` at the root of
the project, you can add that:

```toml
[[hook]]
...
scope = "single-file"
extra_inputs = ["pyproject.toml"]
```

If `extra_inputs` are not present, the rules still runs.

## Repo

```toml
[[rule]]
# ...
scope = "repo"
```

This rule runs once per repo, with the working dir as the root of the repo.
Intended mainly for editing dotfiles like `.gitignore`, `.mailmap`, etc.

## Project

This rule runs once per detected [project](project.md) (see `ick list-projects`)
and is the typical way you'll want to edit project metadata if you need to edit
multiple files at once.

You should only read the files you specify as `input=` -- even specifying
inefficient globs like `*.py` or `**/scripts/*` is better than leaving it unset
which assumes every file gets read.

One example of a project-scoped rule would be ensuring that type stubs contain
all the public names.  If there's a project in a subdir that is uv-installable
(has a `pyproject.toml` with `name` and `version` at least), then you can do
something like this:

```toml
[[rule]]

name = "stubs-should-match"
impl = "python"
deps = ["./stubchecker"]
command = ["stubchecker"]
inputs = ["*.py", "*.pyi"]
```
