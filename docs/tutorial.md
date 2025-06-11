<!--
    This file has embedded Python code that must be run to keep it up-to-date.
    Use `make prepdocs` to run it.

    [[[cog
        from cog_helpers import *
        set_source_root("docs/data/tutorial")
        cd_temp(pretend="/tmp/foo")
    ]]]
    [[[end]]] (sum: 1B2M2Y8Asg)
-->

# Tutorial

Ick coordinates the running of automated rules on your code and other files.
Rules can check for conformance, or can transform your files to apply needed
modifications.

Rules can be written in any language and use any tooling you want.  Rules can be
sourced from many places: your code's repo, a rules repo of your own, a rules
repo provided by someone else, or even a local directory.  Ick lets you use rules
from a number of sources at once.

## Setting up a local development ruleset

Let's say you have a situation you want to improve, like moving config
incrementally from individual files into one big file, like `isort.cfg` ->
`pyproject.toml`.

To start simply, create an empty directory at `/tmp/foo`.  This dir will hold
the rule and the code the rule is working on.  Of course you can use a different
path or an existing git repo, just adjust the path examples here.

NOTE: If you run this from within an existing git repo, it is possible that your
tutorial rule will make changes to its contents.  Although it defaults to a
dry-run mode (sometimes), you should still be careful and not do this in your
only copy of it.

<!-- [[[cog
    run_cmd("""
        touch pyproject.toml
    """)
]]] -->
<!-- [[[end]]] (sum: 1B2M2Y8Asg) -->

[BTW: it seems odd that this directory has to be a git repo. Why can't ick
work in a plain-old directory?]

Ick reads `ick.toml` files to find rules.  A ruleset is a location to find
rules.  In `/tmp/foo` create an `ick.toml` file to say that the current
directory has rules:

<!-- [[[cog copy_file("ick.toml", show=True) ]]] -->
```toml
[[ruleset]]
path = "."
```
<!-- [[[end]]] (sum: 6O1Kj+DdqE) -->

If you run `ick list-rules`, it won't find any yet:

<!-- [[[cog show_cmd("ick list-rules") ]]] -->
```shell
$ ick list-rules
```
<!-- [[[end]]] (sum: 9OnFCm6Zhc) -->


## Creating a rule definition

[TODO: why did we need a ruleset definition if we are going to put explicit rule
definitions in ick.toml anyway? Maybe `[[ruleset]] path = "."` should be a
default that always applies.]

Next, we can append to `ick.toml` to define a rule:

<!-- [[[cog copy_file("ick2.toml", "ick.toml", show=True) ]]] -->
```toml
[[ruleset]]
path = "."

[[rule]]
impl = "python"
name = "move_isort_cfg"
# scope = "project"
project_types = ["python"]
```
<!-- [[[end]]] (sum: oNIFtGdtuN) -->

The `language` setting means we will implement the rule with Python code.
Setting `scope` to `project` means the rule will be invoked at the project
level instead of on individual files (but that doesn't work yet, so it's
commented out).

Ick can look for projects of certain types.  Setting `project_types` here means
the rule will be invoked on projects that ick determines are Python projects.

If you run `list-rules` again, the rule appears, but with an indication that
there's no implementation:

<!-- [[[cog show_cmd("ick list-rules") ]]] -->
```shell
$ ick list-rules
LATER
=====
* ./move_isort_cfg  *** Couldn't find implementation /tmp/foo/move_isort_cfg.py
```
<!-- [[[end]]] (sum: Yyc8zk56gm) -->


## Implementing the rule

To implement the rule, create a subdirectory matching the rule name with a
file in it also matching the rule name:

<!-- [[[cog copy_file("move_isort_cfg/move_isort_cfg.py", show=True) ]]] -->
```python
# This file is /tmp/foo/move_isort_cfg/move_isort_cfg.py

from pathlib import Path

import imperfect
import tomlkit

if __name__ == "__main__":
    cfg = Path("isort.cfg")
    toml = Path("pyproject.toml")
    if cfg.exists() and toml.exists():
        # The main aim is to reduce the number of files by one
        with open(cfg) as f:
            cfg_data = imperfect.parse_string(f.read())
        with open(toml) as f:
            toml_data = tomlkit.load(f)
        isort_table = toml_data.setdefault("tool", {}).setdefault("isort", {})
        isort_table.update(cfg_data["settings"])
        toml.write_text(tomlkit.dumps(toml_data))
        cfg.unlink()
```
<!-- [[[end]]] (sum: kpNRLhmBlR) -->

The details of this implementation aren't important.  The key thing to note is
this is Python code that uses third-party packages to read the `isort.cfg` file
and write the `pyproject.toml` file.  When you write rules you can use any code
you want to accomplish your transformations.

Note in particular that there's no special protocol, flags, or output required.
The rule can just modify files.  The order of modification/delete also doesn't
matter.

Ick runs rules in a temporary copy of your repo working tree.  If the rule
raises an exception, the user will be alerted without actually changing their
real working tree.

If you want to provide more context for why this change is useful, simply
`print(...)` it to stdout.

```python
print("You can move the isort config into pyproject.toml to have fewer")
print("files in the root of your repo.  See http://go/unified-config")
```

If you don't modify files, and exit 0, anything you print is ignored.

The `ick run` command will run the rule. But if we try it now it will fail
trying to import those third-party dependencies:

<!-- [[[cog show_cmd("ick run") ]]] -->
```shell
$ ick run
-> ./move_isort_cfg on ERROR
     Traceback (most recent call last):
       File "/tmp/foo/move_isort_cfg/move_isort_cfg.py", line 5, in <module>
         import imperfect
     ModuleNotFoundError: No module named 'imperfect'
```
<!-- [[[end]]] (sum: ICFz6k3lD+) -->

We need to tell `ick` about the dependencies the rule needs.


## Configuring dependencies

Python rules can declare the dependencies they need.  Ick will create a
virtualenv for each rule and install the dependencies automatically.

You can declare those in the `ick.toml` config file. Update it with a `deps`
line like this:

<!-- [[[cog show_file("ick3.toml", start=r"\[\[rule\]\]", end="deps") ]]] -->
```toml
[[rule]]
impl = "python"
deps = ["imperfect", "tomlkit"]
```
<!-- [[[end]]] (sum: 8A2PIE+z09) -->
<!-- [[[cog copy_file("ick3.toml", "ick.toml") ]]] -->
<!-- [[[end]]] (sum: 1B2M2Y8Asg) -->


Now `ick run` shows that the rule ran:

<!-- [[[cog show_cmd("ick run") ]]] -->
```shell
$ ick run
-> ./move_isort_cfg on OK
```
<!-- [[[end]]] (sum: tQnt20T8T3) -->

But the rule did nothing because there is no `isort.cfg` file in `/tmp/foo`.
Create one:

<!-- [[[cog copy_file("isort.cfg", show=True) ]]] -->
```ini
[settings]
line_length = 88
multi_line_output = 3
```
<!-- [[[end]]] (sum: CXcy2s50F3) -->

Now `ick run` shows a dry-run summary of the changes that would be made:

<!-- [[[cog show_cmd("ick run") ]]] -->
```shell
$ ick run
-> ./move_isort_cfg on OK
     isort.cfg +0-3
     pyproject.toml +3-0
```
<!-- [[[end]]] (sum: uC0Myzw2b2) -->

Passing the `--patch` option displays the full patch of the changes that would
be made:

<!-- [[[cog show_cmd("ick run --patch") ]]] -->
```shell
$ ick run --patch
-> ./move_isort_cfg on OK
diff --git isort.cfg isort.cfg
deleted file mode 100644
index fbab120..0000000
--- isort.cfg
+++ /dev/null
@@ -1,3 +0,0 @@
-[settings]
-line_length = 88
-multi_line_output = 3
diff --git pyproject.toml pyproject.toml
index e69de29..089c824 100644
--- pyproject.toml
+++ pyproject.toml
@@ -0,0 +1,3 @@
+[tool.isort]
+line_length = "88"
+multi_line_output = "3"
```
<!-- [[[end]]] (sum: rZpo8/Pd6j) -->


## Reducing execution

As written, our rule would run for any Python project, but it will run when
*any* file in the project changes.  We can be smarter than this since there are
just two files we care about.  We might read both, and might write one and
delete the other, so we specify them as both input and output:

```toml
inputs = ["pyproject.toml", "isort.cfg"]
outputs = ["pyproject.toml", "isort.cfg"]
```

It's safe to omit `inputs` and `outputs`, but the rule will run more often than
it needs to.


## Testing

One of the chief problems with writing codemods is being able to succinctly test
them.  Because `ick` is built around *modifying* *sets* of files, the tests for
a rule are files showing the before and after states expected.

The `ick test-rules` command will run tests for your rules.  We haven't written
any tests yet, so it has nothing to do:

<!-- [[[cog show_cmd("ick test-rules") ]]] -->
```shell
$ ick test-rules
testing...
  ./move_isort_cfg: <no-test> PASS

FAILING INFO

./move_isort_cfg: no tests in /tmp/foo/move_isort_cfg/tests

(exited with 1)
```
<!-- [[[end]]] (sum: 209Eo7TRI+) -->

In your `move_isort_cfg` rule directory, create a `tests` subdirectory.  There
each directory will be a test.  Create a `move_isort_cfg/tests/no_isort`
directory.  In there, the `a` directory will be the "before" state of the files,
and the `b` directory will be the expected "after" state of the files.  Running
the test checks that the files in `a` are transformed to match the files in `b`
when the rule runs.

Create two files `a/pyproject.toml` and `b/pyproject.toml` with the same
contents:

<!-- [[[cog show_file("move_isort_cfg/tests/no_isort/a/pyproject.toml") ]]] -->
```toml
[project]
name = "foo"
```
<!-- [[[end]]] (sum: cl1LTCokhc) -->


<!-- [[[cog copy_tree("move_isort_cfg/tests/no_isort") ]]] -->
<!-- [[[end]]] (sum: 1B2M2Y8Asg) -->

Your directory structure should look like this:

<!-- [[[cog show_cmd("find . -print | sort | sed -e 's;[^/]*/;|-- ;g;s;-- |;   |;g;'", hide_command=True) ]]] -->
```shell
.
|-- ick.toml
|-- isort.cfg
|-- move_isort_cfg
|   |-- move_isort_cfg.py
|   |-- tests
|   |   |-- no_isort
|   |   |   |-- a
|   |   |   |   |-- pyproject.toml
|   |   |   |-- b
|   |   |   |   |-- pyproject.toml
|-- pyproject.toml
```
<!-- [[[end]]] (sum: /K9GxUkPCU) -->

This is a simple test that checks that if there is no `isort.cfg` file, the
`pyproject.toml` file will be unchanged.  Run `ick test-rules`:

<!-- [[[cog show_cmd("ick test-rules") ]]] -->
```shell
$ ick test-rules
testing...
  ./move_isort_cfg: . PASS
```
<!-- [[[end]]] (sum: aPmBG+QcQb) -->

Now make a more realistic test. Create a `change_made`
directory in the `tests` directory. Create these files:

`change_made/a/isort.cfg`:
<!-- [[[cog show_file("move_isort_cfg/tests/change_made/a/isort.cfg") ]]] -->
```ini
[settings]
line_length = 88
multi_line_output = 3
```
<!-- [[[end]]] (sum: CXcy2s50F3) -->

`change_made/a/pyproject.toml`:
<!-- [[[cog show_file("move_isort_cfg/tests/change_made/a/pyproject.toml") ]]] -->
```toml
[project]
name = "foo"
```
<!-- [[[end]]] (sum: cl1LTCokhc) -->

`change_made/b/pyproject.toml`:
<!-- [[[cog show_file("move_isort_cfg/tests/change_made/b/pyproject.toml") ]]] -->
```toml
[project]
name = "foo"

[tool.isort]
line_length = "88"
multi_line_output = "3"
```
<!-- [[[end]]] (sum: axp71Iu8bP) -->

<!-- [[[cog copy_tree("move_isort_cfg/tests/change_made") ]]] -->
<!-- [[[end]]] (sum: 1B2M2Y8Asg) -->

Now `ick test-rules` shows two tests passing:

<!-- [[[cog show_cmd("ick test-rules") ]]] -->
```shell
$ ick test-rules
testing...
  ./move_isort_cfg: .. PASS
```
<!-- [[[end]]] (sum: Q8fKoyhhcW) -->
