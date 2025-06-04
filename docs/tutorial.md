<!--
    [[[cog
        from cog_helpers import *
        set_source_root("docs/data/tutorial")
        cd_temp(pretend="/tmp/foo")
    ]]]
    [[[end]]] (checksum: d41d8cd98f00b204e9800998ecf8427e)
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

To start simply, create an empty git repo at `/tmp/foo`.  This repo will hold
the rule and the code the rule is working on.  Of course you can use a different
path or an existing git repo, just adjust the path examples here.

To make the directory realistic enough for ick to run, create an empty
`pyproject.toml` file and commit it to git.

<!-- [[[cog
    run_cmd("""
        git init
        touch pyproject.toml
        git add pyproject.toml
        git commit -m 'first'
    """)
]]] -->
<!-- [[[end]]] (checksum: d41d8cd98f00b204e9800998ecf8427e) -->

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
<!-- [[[end]]] (checksum: e8ed4a8fe0dda845941b2a7e70a8e41c) -->

If you run `ick list-rules`, it won't find any yet:

<!-- [[[cog show_cmd("ick list-rules") ]]] -->
```shell
$ ick list-rules
```
<!-- [[[end]]] (checksum: f4e9c50a6e9985c8275f2e105e87dad3) -->


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
language = "python"
name = "move_isort_cfg"
# scope = "project"
project_types = ["python"]
```
<!-- [[[end]]] (checksum: 20e0d0d05c8c49ec3569b91ee6f03fd4) -->

The `language` setting means we will implement the rule with Python code.
Setting `scope` to `project` means the rule will be invoked at the project
level instead of on individual files (but that doesn't work yet, so it's
commented out).

Ick can look for projects of certain types.  Setting `project_types` here means
the rule will be invoked on projects that ick determines are Python projects.

[TODO: list-rules doesn't error here as the tutorial used to claim: it shows the
name of the rule. Do we want it to error? It could be helpful to list the rule,
but indicate that the code is missing.]

If you run `list-rules` again, the rule appears:

<!-- [[[cog show_cmd("ick list-rules") ]]] -->
```shell
$ ick list-rules
LATER
=====
* ./move_isort_cfg
```
<!-- [[[end]]] (checksum: 66e4d4a87e650110014fc2f510e329ad) -->


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
<!-- [[[end]]] (checksum: 9293512e1981951c901b816d77d4255d) -->

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
<!-- [[[end]]] (checksum: 202173ea4de50fe9c7c15418c3519450) -->

We need to tell `ick` about the dependencies the rule needs.


## Configuring dependencies

Python rules can declare the dependencies they need.  Ick will create a
virtualenv for each rule and install the dependencies automatically.

You can declare those in the `ick.toml` config file. Update it with a `deps`
line like this:

<!-- [[[cog show_file("ick3.toml", start=r"\[\[rule\]\]", end="deps") ]]] -->
```toml
[[rule]]
language = "python"
deps = ["imperfect", "tomlkit"]
```
<!-- [[[end]]] (checksum: 6677de2516065642c3ae47f685978cbd) -->
<!-- [[[cog copy_file("ick3.toml", "ick.toml") ]]] -->
<!-- [[[end]]] (checksum: d41d8cd98f00b204e9800998ecf8427e) -->


Now `ick run` shows that the rule ran:

<!-- [[[cog show_cmd("ick run") ]]] -->
```shell
$ ick run
-> ./move_isort_cfg on OK
```
<!-- [[[end]]] (checksum: b509eddb44fc4f79c0f0a54eac8eb037) -->

But the rule did nothing because there is no `isort.cfg` file in `/tmp/foo`.
Create one:

<!-- [[[cog copy_file("isort.cfg", show=True) ]]] -->
```ini
[settings]
line_length = 88
multi_line_output = 3
```
<!-- [[[end]]] (checksum: 097732dace74177fbdc2df187860767b) -->

Now `ick run` shows a dry-run summary of the changes that would be made:

<!-- [[[cog show_cmd("ick run") ]]] -->
```shell
$ ick run
-> ./move_isort_cfg on OK
     isort.cfg +0-3
     pyproject.toml +3-0
```
<!-- [[[end]]] (checksum: b82d0ccb3c366f6459ba77fb82d36b49) -->

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
<!-- [[[end]]] (checksum: ad9a68f3f3ddea38eb1632c996cdd281) -->


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
no tests for ./move_isort_cfg under /tmp/foo/move_isort_cfg/tests
Prepare ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   
```
<!-- [[[end]]] (checksum: 2924021064994618a602e3a178ab0f67) -->

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
<!-- [[[end]]] (checksum: 725d4b4c2a2485cae7690a21c0a6754b) -->


<!-- [[[cog copy_tree("move_isort_cfg/tests/no_isort") ]]] -->
<!-- [[[end]]] (checksum: d41d8cd98f00b204e9800998ecf8427e) -->

Your directory structure should look like this:

<!-- [[[cog show_cmd("tree --dirsfirst") ]]] -->
```shell
$ tree --dirsfirst
.
├── move_isort_cfg
│   ├── tests
│   │   └── no_isort
│   │       ├── a
│   │       │   └── pyproject.toml
│   │       └── b
│   │           └── pyproject.toml
│   └── move_isort_cfg.py
├── ick.toml
├── isort.cfg
└── pyproject.toml

6 directories, 6 files
```
<!-- [[[end]]] (checksum: fc1c69238f7367682fd6316dc5c2d30a) -->

This is a simple test that checks that if there is no `isort.cfg` file, the
`pyproject.toml` file will be unchanged.  Run `ick test-rules`:

<!-- [[[cog show_cmd("ick test-rules") ]]] -->
```shell
$ ick test-rules
1 ok
Prepare          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━             
./move_isort_cfg ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
```
<!-- [[[end]]] (checksum: a23216b8a388c7d962fb19964730368e) -->

Now make a more realistic test. Create a `change_made`
directory in the `tests` directory. Create these files:

`change_made/a/isort.cfg`:
<!-- [[[cog show_file("move_isort_cfg/tests/change_made/a/isort.cfg") ]]] -->
```ini
[settings]
line_length = 88
multi_line_output = 3
```
<!-- [[[end]]] (checksum: 097732dace74177fbdc2df187860767b) -->

`change_made/a/pyproject.toml`:
<!-- [[[cog show_file("move_isort_cfg/tests/change_made/a/pyproject.toml") ]]] -->
```toml
[project]
name = "foo"
```
<!-- [[[end]]] (checksum: 725d4b4c2a2485cae7690a21c0a6754b) -->

`change_made/b/pyproject.toml`:
<!-- [[[cog show_file("move_isort_cfg/tests/change_made/b/pyproject.toml") ]]] -->
```toml
[project]
name = "foo"

[tool.isort]
line_length = "88"
multi_line_output = "3"
```
<!-- [[[end]]] (checksum: 6b1a7bd48bbc6cfc34c39b9e720b7d80) -->

<!-- [[[cog copy_tree("move_isort_cfg/tests/change_made") ]]] -->
<!-- [[[end]]] (checksum: d41d8cd98f00b204e9800998ecf8427e) -->

Now `ick test-rules` shows two tests passing:

<!-- [[[cog show_cmd("ick test-rules") ]]] -->
```shell
$ ick test-rules
1 ok
1 ok
Prepare          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━             
./move_isort_cfg ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
```
<!-- [[[end]]] (checksum: cea09823b30e560d213d92946a915ef5) -->


<!-- [[[cog clean_up() ]]] -->
<!-- [[[end]]] (checksum: d41d8cd98f00b204e9800998ecf8427e)  -->
