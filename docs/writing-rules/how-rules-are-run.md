# How rules are run

When ick runs a rule, it takes these steps:

- Files from your local directory are copied to a temporary directory.  For
    file-scoped rules, only the files in the rule's `input` setting will be
    copied.  For project- and repo-scoped rules, all files are copied.  Your
    rule doesn't run in your local directory, and will only have access.  Each
    rule gets its own temporary directory so they can run independently.

- The code of the rule is executed.  Different `impl` values use different
    execution engines.

    - Ick creates environment variables to provide extra information beyond the
        copied files:

        - `ICK_REPO_PATH` is the path to the original working directory. Use
          this if you need information that isn't in file content, such as git
          remote information.

- Two results of the rule are examined to determine what happened:

    - The temporary file copies are checked for files that have been modified,
        added, or deleted.

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
