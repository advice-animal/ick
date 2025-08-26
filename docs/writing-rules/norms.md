# Norms for rules

Because rules are source code or shell commands, they don't come with a lot of
built-in guardrails.  Rules are expected to behave themselves, which in a nutshell means:

* Rules should be idempotent
* Regarding files in repo
  * Only modify (or create or delete) files under the working dir they're started in
  * Only read the files they declare as inputs (regardless of scope)
  * Only write the files they declare as outputs (regardless of scope)
* Regarding **external** state (that is, outside the repo including state held
  in other services or elsewhere on disk)
  * Read whatever external state you want
  * Write external state only when the env var `ICK_APPLY` is set -- this disables
    much of the parallelism in the name of getting the semantics right, because
    we don't know if there's a way to undo.

Ick promises that once a rule starts running, the working copy won't be further
modified **by ick**.  You might have multiple simultaneous runs of the same
`scope=file` rule in the same working copy, if there's reason to.
