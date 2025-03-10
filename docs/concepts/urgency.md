# Urgency

We break with convention of most tools that have a clearly-defined concept of
"error" vs "warning" or other levels, in favor of the more human-focused,
actionable "urgency."

While people can choose to run hooks in any order, this allows grouping and
inferences of their priorities.

For example, a pending deprecation in 3 months might be `"now"` and once it's
actually deprecated might be `"not-supportable"`.

https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#diagnostic
https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html#_Toc34317648
