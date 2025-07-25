<!-- splitme2 -->

# Testing tutorial

This continues where the previous [Writing rules
tutorial](writing-tutorial.html) left off.

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
move_isort_cfg: no tests in /tmp/foo/tests/move_isort_cfg

```
<!-- [[[end]]] (sum: f7Oez2GCKL) -->

The ick output shows where the tests should go.

In your rule directory, create a `tests` subdirectory with another subdirectory
named for your rule: `tests/move_isort_cfg`.  In there each additional directory
will be a test.  Create a `tests/move_isort_cfg/no_isort` directory.  In there,
the `input` directory will be the "before" state of the files, and the `output`
directory will be the expected "after" state of the files.  Running the test
checks that the files in `input` are transformed to match the files in `output`
when the rule runs.

Create two files `input/pyproject.toml` and `output/pyproject.toml` with the same
contents:

<!-- [[[cog show_file("tests/move_isort_cfg/no_isort/input/pyproject.toml") ]]] -->
```toml
[project]
name = "foo"
```
<!-- [[[end]]] (sum: cl1LTCokhc) -->


<!-- [[[cog copy_tree("tests/move_isort_cfg/no_isort") ]]] -->
<!-- [[[end]]] (sum: 1B2M2Y8Asg) -->

Your directory structure should look like this:

<!-- [[[cog show_tree(".") ]]]-->
```console
├── ick.toml
├── isort.cfg
├── move_isort_cfg.py
├── pyproject.toml
└── tests/
    └── move_isort_cfg/
        └── no_isort/
            ├── input/
            │   └── pyproject.toml
            └── output/
                └── pyproject.toml
```
<!-- [[[end]]] (sum: O+MN8yIAFo) -->

This is a simple test that checks that if there is no `isort.cfg` file, the
`pyproject.toml` file will be unchanged.  Run `ick test-rules`:

<!-- [[[cog show_cmd("ick test-rules") ]]] -->
```console
$ ick test-rules
testing...
  move_isort_cfg: . PASS
```
<!-- [[[end]]] (sum: OyKYc1mCka) -->

Now make a more realistic test. Create a `change_made` directory in the
`tests/move_isort_cfg` directory. Create these files:

`change_made/input/isort.cfg`:
<!-- [[[cog show_file("tests/move_isort_cfg/change_made/input/isort.cfg") ]]] -->
```ini
[settings]
line_length = 88
multi_line_output = 3
```
<!-- [[[end]]] (sum: CXcy2s50F3) -->

`change_made/input/pyproject.toml`:
<!-- [[[cog show_file("tests/move_isort_cfg/change_made/input/pyproject.toml") ]]] -->
```toml
[project]
name = "foo"
```
<!-- [[[end]]] (sum: cl1LTCokhc) -->

`change_made/output/pyproject.toml`:
<!-- [[[cog show_file("tests/move_isort_cfg/change_made/output/pyproject.toml") ]]] -->
```toml
[project]
name = "foo"

[tool.isort]
line_length = "88"
multi_line_output = "3"
```
<!-- [[[end]]] (sum: axp71Iu8bP) -->

<!-- [[[cog copy_tree("tests/move_isort_cfg/change_made") ]]] -->
<!-- [[[end]]] (sum: 1B2M2Y8Asg) -->

Now `ick test-rules` shows two tests passing:

<!-- [[[cog show_cmd("ick test-rules") ]]] -->
```console
$ ick test-rules
testing...
  move_isort_cfg: .. PASS
```
<!-- [[[end]]] (sum: 0QwW4JWipi) -->

Now that we have two tests, the full directory structure looks like this:

<!-- [[[cog show_tree(".") ]]]-->
```console
├── ick.toml
├── isort.cfg
├── move_isort_cfg.py
├── pyproject.toml
└── tests/
    └── move_isort_cfg/
        ├── change_made/
        │   ├── input/
        │   │   ├── isort.cfg
        │   │   └── pyproject.toml
        │   └── output/
        │       └── pyproject.toml
        └── no_isort/
            ├── input/
            │   └── pyproject.toml
            └── output/
                └── pyproject.toml
```
<!-- [[[end]]] (sum: 2OFdcYcxz6) -->

This can seem intricate, but it establishes a good structure: a directory can
have more than one rule, each rule can have more than one test.
