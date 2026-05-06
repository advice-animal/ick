- Scenarios are in directories under tests/scenarios
- Each scenario is a text file:  tests/scenarios/*/*.txt
- The text file is like a terminal session
    - commands + output
    - the current directory (everything up through /repo) is replaced with `/CWD`
        - this also applies to the output of ick
- Next to the text files is a `repo` directory
    - it should be structured like a repo containing rules
    - it has ick.toml
    - it has tests
        - the tests will only be run if you use `$ ick test-rules` in your
            scenario
- Do not `cd` into a scenario's `repo` directory to run commands manually;
  always run from the project root
- If you've changed code and it will change existing scenarios:
    - you can run the scenarios to auto-update them:
        - `UPDATE_SCENARIOS=1 pytest -k scenario`
- To create a new scenario `.txt` file:
    - write a stub containing just the command line (for example: `$ ick test-rules\n`)
    - then run `UPDATE_SCENARIOS=1 pytest -k scenario` to fill in the expected output
