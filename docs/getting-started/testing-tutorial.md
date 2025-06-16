<!-- splitme -->

## Testing Tutorial

This continues right where the previous [Tutorial](tutorial.html) left off.

One of the chief problems with writing codemods is being able to succinctly test
them.  Because `ick` is built around *modifying* *sets* of files, the tests for
a rule are files showing the before and after states expected.

The `ick test-rules` command will run tests for your rules.  We haven't written
any tests yet, so it has nothing to do:

<!-- [[[cog show_cmd("ick test-rules") ]]] -->
```shell
$ ick test-rules
testing...
  move_isort_cfg: <no-test> PASS

FAILING INFO
move_isort_cfg: no tests in /tmp/foo/move_isort_cfg/tests

(exited with 1)
```
<!-- [[[end]]] (sum: HSz6QqBZaO) -->

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
  move_isort_cfg: . PASS
```
<!-- [[[end]]] (sum: UHnmBuZrZ1) -->

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
  move_isort_cfg: .. PASS
```
<!-- [[[end]]] (sum: WmmtiTDZw7) -->
