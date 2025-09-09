# Testing rules

Testing your ick rules are a great way to make sure they work!

## Ick rules test directory structure

### Where to place your tests

To test your ick rules, create a `tests/` directory next to your rule file, and
then add a directory that matches the rule name. In there, each test case should
receive its own directory, with the directory name being the name of the test.

### Structure of a single test

Each test for an ick rule consists of two directories:
- `input/`: Contains the initial state of files before the rule runs
- `output/`: Contains the expected state of files after the rule runs

### Test for an expected exception using `error.txt`

If you want an error/exception to occur during your test, write the exception verbatim to
`output/error.txt`.

### Test for an expected stdout using `output.txt`

If you if you expect your rule to exit with return code 99 and write to stdout (e.g. "Work is still needed on file ..."),
write the expected stdout verbatim to `output/output.txt`.

### Test structure visualized

For two given ick rules, which we've creatively named `rule1` and `rule2`, the
following file structure will add tests called `test_rule1`,
`test_work_needed`, and `test_error` to `rule1` and `test_rule2` to `rule2`. These will be invoked
when you run `ick test-rules`.

```shell
.
|-- ick.toml
|-- some_dir
|   |-- ick.toml
|   |-- rule1.py
|   |-- rule2.py
|   |-- tests
|   |   |-- rule1
|   |   |   |-- test_rule1
|   |   |   |   |-- input
|   |   |   |   |   |-- foo.bar
|   |   |   |   |-- output
|   |   |   |   |   |-- foo.bar
|   |   |   |-- test_work_needed
|   |   |   |   |-- input
|   |   |   |   |   |-- foo.bar
|   |   |   |   |-- output
|   |   |   |   |   |-- foo.bar
|   |   |   |   |   |-- output.txt
|   |   |   |-- test_error
|   |   |   |   |-- input
|   |   |   |   |   |-- foo.bar
|   |   |   |   |-- output
|   |   |   |   |   |-- foo.bar
|   |   |   |   |   |-- error.txt
|   |   |-- rule2
|   |   |   |-- test_rule2
|   |   |   |   |-- input
|   |   |   |   |   |-- foo.bar
|   |   |   |   |-- output
|   |   |   |   |   |-- foo.bar
```

Each directory in `tests/rule1` is a different test for `rule1`. As long as
`tests/rule1` exists in the same directory as `rule1.py`, ick will find the
tests with no extra configuration.

## Running tests

Use the `ick test-rules` command to run all tests for your rules. The command will:

- Find all rules in all of the configured rulesets
- Look for test directories matching the rule names
- Run each test and report results

For each test, ick will:

1. Copy the contents of `input/` to a temporary directory
2. Run the rule on those files
3. Compare the results with the contents of `output/`, including any expected errors in `error.txt` and stdouts in `output.txt`.

If the files match exactly, the test passes. If there are any differences, the
test fails and prints the diff.

### Test output

When running tests, you'll see output like:

```shell
$ ick test-rules
testing...
  rule1: .. PASS
```

The two dots before `PASS` each represent a successful test for a given rule.
(So if `rule2` in the example above passes, we'd only see one dot) If a test
fails, you'll see an F instead like:

```shell
$ ick test-rules
testing...
  rule1: F. FAIL
```

In the case of a fail, ick will also tell you the following for each failed test:

- What differences were found between the expected and actual output
- Any exceptions that occurred during the test

If a test is not provided, `ick test-rules` will note that the rule has no test
and mark it as passed.
