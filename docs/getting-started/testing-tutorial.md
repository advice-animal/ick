<!-- splitme -->

## Testing tutorial

This continues right where the previous [Tutorial](tutorial.html) left off.

One of the chief problems with writing codemods is being able to succinctly test
them.  Because `ick` is built around *modifying* *sets* of files, the tests for
a rule are files showing the before and after states expected.

The `ick test-rules` command will run tests for your rules.  We haven't written
any tests yet, so it has nothing to do:

<!-- [[[cog show_cmd("ick test-rules") ]]] -->
```console
$ ick test-rules
testing...
  move_isort_cfg: <no-test> PASS

DETAILS
move_isort_cfg: no tests in /tmp/foo/move_isort_cfg/tests

```
<!-- [[[end]]] (sum: 6h77V1w+fR) -->

In your `move_isort_cfg` rule directory, create a `tests` subdirectory.  There
each directory will be a test.  Create a `move_isort_cfg/tests/no_isort`
directory.  In there, the `input` directory will be the "before" state of the files,
and the `output` directory will be the expected "after" state of the files.  Running
the test checks that the files in `input` are transformed to match the files in `output`
when the rule runs.

Create two files `input/pyproject.toml` and `output/pyproject.toml` with the same
contents:

<!-- [[[cog show_file("move_isort_cfg/tests/no_isort/input/pyproject.toml") ]]] -->
```toml
[project]
name = "foo"
```
<!-- [[[end]]] (sum: cl1LTCokhc) -->


<!-- [[[cog copy_tree("move_isort_cfg/tests/no_isort") ]]] -->
<!-- [[[end]]] (sum: 1B2M2Y8Asg) -->

Your directory structure should look like this:

<!-- [[[cog show_cmd("find . -print | sort | sed -e 's;[^/]*/;|-- ;g;s;-- |;   |;g;'", hide_command=True) ]]] -->
```console
.
|-- ick.toml
|-- isort.cfg
|-- move_isort_cfg
|   |-- move_isort_cfg.py
|   |-- tests
|   |   |-- no_isort
|   |   |   |-- input
|   |   |   |   |-- pyproject.toml
|   |   |   |-- output
|   |   |   |   |-- pyproject.toml
|-- pyproject.toml
```
<!-- [[[end]]] (sum: 6fTx3KuD7w) -->

This is a simple test that checks that if there is no `isort.cfg` file, the
`pyproject.toml` file will be unchanged.  Run `ick test-rules`:

<!-- [[[cog show_cmd("ick test-rules") ]]] -->
```console
$ ick test-rules
testing...
  move_isort_cfg: . PASS
```
<!-- [[[end]]] (sum: OyKYc1mCka) -->

Now make a more realistic test. Create a `change_made`
directory in the `tests` directory. Create these files:

`change_made/a/isort.cfg`:
<!-- [[[cog show_file("move_isort_cfg/tests/change_made/input/isort.cfg") ]]] -->
```ini
[settings]
line_length = 88
multi_line_output = 3
```
<!-- [[[end]]] (sum: CXcy2s50F3) -->

`change_made/a/pyproject.toml`:
<!-- [[[cog show_file("move_isort_cfg/tests/change_made/input/pyproject.toml") ]]] -->
```toml
[project]
name = "foo"
```
<!-- [[[end]]] (sum: cl1LTCokhc) -->

`change_made/b/pyproject.toml`:
<!-- [[[cog show_file("move_isort_cfg/tests/change_made/output/pyproject.toml") ]]] -->
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
```console
$ ick test-rules
testing...
  move_isort_cfg: .. PASS
```
<!-- [[[end]]] (sum: 0QwW4JWipi) -->
