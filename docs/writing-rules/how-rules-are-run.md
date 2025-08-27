# How rules are run

When ick runs a rule, it takes these steps:

- Files from your local directory are copied to a temporary directory.

    - For file-scoped rules, only the files in the rule's `input` setting will
        be copied.

    - For project- and repo-scoped rules, all files are copied.

- Your rule doesn't run in your local directory, and will only have access to
    files copied because of the `input` setting.  Each rule gets its own
    temporary directory so they can run independently.

- The code of the rule is executed as a separate process.  Different `impl`
    values use different execution engines, but all share common behavior:

    - File-scoped rules get file paths to operate on as command-line arguments.
        Their actions should be limited to those files.  Ick might run multiple
        processes for one rule, with different subsets of the requested files
        passed to each process.

    - Ick creates environment variables to provide extra information beyond the
        copied files:

        - `ICK_REPO_PATH` is the path to the original working directory. Use
          this if you need information that isn't in file content, such as git
          remote information.

        - `ICK_APPLY` exists (with a value of "1") if the rule is running with
          the `--apply` option.  Use this if your rule makes changes outside the
          files in the working tree.  Only make those changes if this variable
          indicates that the rule is being applied.

    - Rules can make changes to the local copies of files, delete files, or
        create new files.  Any file that might be modified, created, or deleted
        must be declared in the rule's `output` setting.

    - Rules can also make changes beyond the local copies of files.  They might
        change settings in an external service, update databases, or anything at
        all.  Rules should only make these changes if `ICK_APPLY` is set.

- When the rule has finished running, ick examines two results to determine what
    happened:

    - The temporary file copies are checked for files that have been modified,
        added, or deleted.

    - The exit status of the process is checked. 0 indicates success, 99 is a
        special signal that work needs to be done, and other statuses are
        failures of the rule.

- These are possible outcomes:

    - If files have been changed and the code exited successfully (status code
        0), then the rule is considered a successful code modification.  Ick
        will use the diffs of the changes in various ways: report on them,
        display them, copy the changes back to your working directory.

    - If files have been changed but the exit status is 99, then the rule has
        made a start on a change, but the user needs to finish it somehow.

    - If  the rule makes no changes and exits with 0, then nothing needed to be
        done and nothing was done.
