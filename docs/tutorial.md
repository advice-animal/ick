# Tutorial

Let's say you have a situation you want to improve, like moving config
incrementally from individual files into one big file, like `isort.ini` ->
`pyproject.toml`.

First, decide what language your rule is going to be written in.  I happen to
know that you could do this in Python, but maybe you've got something else.

## Setting up a local development mount

To avoid getting into the weeds on the many ways to configure it, let's assume
you have an empty directory `/tmp/foo` (adjust command lines as needed) that you
want to put your rule in.

First you'll need to create a user/repo-type config in `ick.toml` in your Python project's root:

```toml
[[mount]]

path = "."
```

This tells `ick` to look in subdirectories of that for rules, which
coincidentally can also be put in `ick.toml` in the next step.

In this step though, if you run `ick list-rules` it shouldn't find any.

## Creating a rule definition

Next, we can append to this file and treat it as a rule-type config:

```toml
[[rule]]

language = "python"
name = "move_isort_ini"
scope = "project"
project_types = ["python"]
```

This would now run once for each Python project.  This isn't very efficient
though -- the runner will think this needs to be rerun when *any* file in the
project changes, when in reality there are just two we care about.  We might read
both, and might write one and delete the other, so we specify them as both input
and output:

```toml
inputs = ["pyproject.toml", "isort.ini"]
outputs = ["pyproject.toml", "isort.ini"]
```

Leaving this at the default (*any* files) is safer, but waaay slower.

<!-- TODO: list-rules doesn't error here: it shows the name of the rule. -->

If you run the `list-rules` again, it should error because it can't find the
code backing this rule.  For that, we need to create a subdir matching the rule
name with an `__init__.py`.  The reason it's a subdir will be more obvious
later, when we add tests.  For now, just roll with it.

```py
# This file is /tmp/foo/move_isort_ini/__init__.py
import imperfect
import tomlkit

if __name__ == "__main__":
    ini = Path("isort.ini")
    toml = Path("pyproject.toml")
    if ini.exists() and toml.exists():
        # The main aim is to reduce the number of files by one
        ini_data = imperfect.load(ini)
        toml_data = tomlkit.load(toml)
        isort_table = toml_data.setdefault("tool", {}).setdefault("isort", {})
        isort_table.update(ini_data)
        toml.write_text(toml_data.dump())
        ini.unlink()
```

Note in particular that there's no special protocol, flags, or output this
needs.  It can just modify files.  The order of modification/delete also doesn't
matter.  If we encounter an error (say, "permission denied") some exception will
be raised and the user will be alerted without actually changing their "real"
checkout.

If you want to provide more context for why this change is useful, simply
`print(...)` it to stdout.

```
print("You can move the isort config into pyproject.toml to have fewer")
print("files in the root of your repo.  See http://go/unified-config")
```

N.b. If you don't modify files, and exit 0, anything you print is ignored.

You should now be able to run `list-rules` and have it show the name at least.
However if you change the verb to `run`, it will fail trying to import those
dependencies -- that's because you haven't told `ick` that you need them.

<!-- TODO: `ick run` at this point does nothing because there are no projects. -->

## Configuring dependencies

Python rules with no dependencies may run with the same interpreter that `ick`
itself does.  If you need anything in particular, you'll want it to create a
virtual environment and install some dependencies.

You can either declare those in the config:

```toml
[[rule]]

language = "python"
deps = ["imperfect", "tomlkit"]
# ...
```

or you could create `/tmp/foo/move_isort_ini/requirements.txt` (ideally with
your choice of dep locking program).

## Testing

One of the chief problems with writing codemods is being able to succinctly test
them.  Because `ick` is built around *modifying* *sets* of files, you can put
simple tests in the `tests/a` and `tests/b` subdir of your rule.

The files in `a` should be transformed to match the files in `b` when the rule
runs.  You'll want to include some minimal marker that makes it be treated as a
project, if you have a project-scope rule.
