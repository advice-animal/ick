<!-- splitme1 -->

<!--
    [[[cog
        cd_temp(pretend="/tmp/foo")
    ]]]
    [[[end]]] (sum: 1B2M2Y8Asg)
-->

# Writing rules tutorial

This continues where the previous [Tutorial](tutorial.html) left off.

In this section we'll show how to write an ick rule.  Rules can be written in
any language and use any tooling you want.  A key idea of ick rules is that they
can be run without ick.  This can simplify the testing and development of rules,
and means that ick can run code that wasn't written specifically for ick.

Rules can modify files, or check if files need manual updating, or both.  We'll
start with a rule that modifies files.


## Setting up a local rule

Let's say you have a situation you want to improve, like moving config
incrementally from individual files into one big file, like `isort.cfg` ->
`pyproject.toml`.

To start simply, create an empty directory at `/tmp/foo` and run `git init` in
it.  This directory will hold the rule and the code the rule is working on.  Of
course you can use a different path or an existing git repo, just adjust the
path examples here.  (If this is your very first time using git, you will need
to set up `user.name` and `user.email` even if you don't intend to make commits
-- ick makes some internally).

<!-- [[[cog
    show_cmd(
        "git init -b main",
        "git config user.name Lester",
        "git config user.email tester@example.org",
    )
]]] -->
```console
$ git init -b main
Initialized empty Git repository in /tmp/foo/.git/
$ git config user.name Lester
$ git config user.email tester@example.org
```
<!-- [[[end]]] (sum: JwXvBR+v6j) -->

NOTE: If you run this from within an existing git repo, it is possible that your
tutorial rule will make changes to its contents.  Although it defaults to a
dry-run mode (sometimes), you should still be careful and not do this in your
only copy of it.

Ick currently needs to find "projects" to operate in. It identifies them by
well-known file names.  For this tutorial create an empty file named
"pyproject.toml" to convince ick this is a Python project.  This will also be a
file our rule will modify later:

<!-- [[[cog
    show_cmd(
        "touch pyproject.toml",
        "touch ick.toml",
    )
]]] -->
```console
$ touch pyproject.toml
$ touch ick.toml
```
<!-- [[[end]]] (sum: uwo5KWfZTZ) -->

Ick reads `ick.toml` files to find rules.  A ruleset is a location to find
rules.  In `/tmp/foo` create an `ick.toml` file to say that the current
directory has rules:

And make sure it is tracked by git and your repo has at least one commit.
Although most changes get replicated, we only trust the filenames that git
knows about when determining initial projects and rule locations.

<!-- [[[cog
    show_cmd(
        "git add *.toml",
        "git commit -q -m 'add marker files'",
    )
]]] -->
```console
$ git add *.toml
$ git commit -q -m 'add marker files'
```
<!-- [[[end]]] (sum: 6pox+ud36n) -->

(the contents don't have to be committed though)

<!-- [[[cog copy_file("ick.toml", show=True) ]]] -->
```toml
[[ruleset]]
path = "."
```
<!-- [[[end]]] (sum: 6O1Kj+DdqE) -->

If you run `ick list-rules`, it won't find any yet:

<!-- [[[cog show_cmd("ick list-rules") ]]] -->
```console
$ ick list-rules
```
<!-- [[[end]]] (sum: nCRewJbc+z) -->


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
scope = "project"
project_types = ["python"]
```
<!-- [[[end]]] (sum: 2R7CGqC2ZG) -->

The `impl` setting means we will implement the rule with Python code.
Setting `scope` to `project` means the rule will be invoked once at the project
level instead of on batches of individual files.

Ick can look for projects of certain types.  Setting `project_types` here means
the rule will be invoked on projects that ick considers Python projects based
on a set of well-known "marker" files.

If you run `list-rules` again, the rule appears, but with an indication that
there's no implementation:

<!-- [[[cog show_cmd("ick list-rules") ]]] -->
```console
$ ick list-rules
LATER
=====
* move_isort_cfg  *** Couldn't find implementation /tmp/foo/move_isort_cfg.py
```
<!-- [[[end]]] (sum: g4EOTtk/5/) -->


## Implementing the rule

To implement the rule, create a Python file matching the rule name:

<!-- [[[cog copy_file("move_isort_cfg.py", show=True) ]]] -->
```python
# This file is /tmp/foo/move_isort_cfg.py

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
<!-- [[[end]]] (sum: Tq3NfSIvon) -->

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
`print(...)` it to stdout:

```python
print("You can move the isort config into pyproject.toml to have fewer")
print("files in the root of your repo.  See http://go/unified-config")
```

If you don't modify files and exit 0, anything you print is ignored.

The `ick run` command will run the rule. But if we try it now it will fail
trying to import those third-party dependencies:

<!-- [[[cog show_cmd("ick run") ]]] -->
```console
$ ick run
-> move_isort_cfg: ERROR
     Traceback (most recent call last):
       File "/tmp/foo/move_isort_cfg.py", line 5, in <module>
         import imperfect
     ModuleNotFoundError: No module named 'imperfect'
```
<!-- [[[end]]] (sum: 3QANyCr4t7) -->

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
```console
$ ick run
-> move_isort_cfg: OK
```
<!-- [[[end]]] (sum: 0XhPie9wc9) -->

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
```console
$ ick run
-> move_isort_cfg: OK
```
<!-- [[[end]]] (sum: 0XhPie9wc9) -->

Passing the `--patch` option displays the full patch of the changes that would
be made:

<!-- [[[cog show_cmd("ick run --patch") ]]] -->
```console
$ ick run --patch
-> move_isort_cfg: OK
```
<!-- [[[end]]] (sum: ot5t65k9t2) -->


## Reducing execution

As written, our rule would run for any Python project, but it will run when
*any* file in the project changes.  We can be smarter than this since there are
just two files we care about.  We might read both, and might write one and
delete the other, so we specify them as inputs:

```toml
inputs = ["pyproject.toml", "isort.cfg"]
```

On `project` and `repo` scoped rules, it's safe to omit `inputs`, since ick will pull in every file by default. However, the rule will run more often than
it needs to.

## Best Practices on How to Access Files in Rules

Under the hood, `ick` takes all the files in your `inputs`, puts them into a temporary directory, and passes their names to the command line. This means they are all accessible as command-line arguments and direct system paths like "Dockerfile". Thanks to this functionality, the best practices on which method to use are very flexible. They largely revolve around what your rule would like to do. 

If you want to perform the same function on many different types of files agnostic of filename, especially when you use globs, you can iterate over them like so:

```toml
[[rule]]
name = "find_and_replace_in_many_types_of_files"
inputs = ["*.py", "*.sh", "literally-anything"]
```

```python
import sys

from pathlib import Path
from typing import List

def main(filenames: List[str]):
    for filename in filenames:
        file = Path(filename)
        # Do something cool to the file! The rule could double-check the filename too, but here we don't care. 

if __name__ == "__main__":
    main(sys.argv[1:])
```

However, if your rule dives deeply into only a few files, your rule will be easier to read and debug if you access them using hardcoded paths.
Remember that these files will only be accessible if they're listed in your `inputs`!
```toml
[[rule]]
name = "check_tox_and_setup.py"
inputs = ["tox.ini", "setup.py"]
```

```python
from pathlib import Path

def main():
    tox_ini = Path("tox.ini").read_text()
    setup_py = Path("setup.py").read_text()
    # Do very specialized things on each file.

if __name__ == "__main__":
    main()
```

Clearly, this method is much cleaner than something like 
```python
def main(filenames: List[str]):
    for filename in filenames:
        if filename == "setup.py":
            # setup.py-specific behavior

        elif filename == "tox.ini":
            # tox.ini-specific behavior


if __name__ == "__main__":
    main(sys.argv[1:])
```
both work, but one looks much nicer!


## Checkers

Rules don't have to modify files, they can examine files to simply check if they
need updating.  If your rule finds problems, it can print messages providing
details, and then exit with a status code of 99.  If your rule exits with 99,
ick summarize the rule as "NEEDS_WORK", otherwise it's "OK".

Rules don't have to be pure codemods or pure checkers.  Your rule can make some
modifications, and can also print messages and exit with 99 if there is more
work to do.


## Testing

Be sure to continue the journey with the [Testing Tutorial](testing-tutorial.html),
which lets you ensure that your rules still work as time goes on.

<!-- splitme2 -->
