# How rules are run

When ick runs a rule, it takes these steps:

- Your git repo is cloned to a new local working tree so that file modifications
    can be made by each rule independently of what other rules might be doing.

- The code of the rule is executed.  Different `impl` values use different
    execution engines.

- Two results of the rule are examined to determine what happened:

    - The local repo copy is checked for files that have been modified, added,
        or deleted.

    - The exit status of the code is checked. 0 indicates success, 99 is a
        special signal that work needs to be done, and other statuses are
        failures of the rule.

- If files have been changed and the code exited successfully (status code
    0), then the rule is considered a successful code modification.  Ick will
    use the diffs of the changes in various ways (report on them, display them,
    make pull requests).

- If files have been changed but the exit status is 99, then the rule has made a
    start on a change, but the user needs to finish it somehow.

- If the rule makes no changes and exits with 0, then nothing needed to be done
    and nothing was done.
