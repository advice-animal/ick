# Norms

Because rules are source code or shell commands, they don't come with a lot of
inbuilt guardrails.  Rules are expected to behave themselves, which in a nutshell means:

* Rules should generally be idempotent
* Only modify (or create or delete) files under the working dir they're started in
* Only read the files they declare as inputs (regardless of scope)
* Only write the files they declare as outputs (regardless of scope)
* Read whatever **external** (that is, outside the repo) state you want
* Write **external** state only when the env var `YOLO` is set -- this disables
  much of the parallelism in the name of getting the semantics right, because
  we don't know if there's a way to undo.

Ick promises that once a rule starts running, the working copy won't be further
modified **by ick**.  You might have multiple simultaneous runs of the same
scope=single-file rule in the same working copy, if there's reason to.

For avoidance of doubt:

You can read the git config of that working copy, or (for example) cache things
in $HOME or use credentials found there in standard locations.  But rules
aren't intended to add remotes (it probably will do nothing) or configure a
machine (there are better tools including dotfiles and etcd to do that).

## Exit Status

Rules are generally run in a child process, and have three ways to communicate
back the results.

An exit code of 0 means you ran to completion, and we should suppress the
output.  An exit code of 99 means you ran to completion, and we should show the
output.

In either case, the description from the config will be used as the beginning
of the message if making a commit for you.

