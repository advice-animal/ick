# Protocol

This example might read .py and .pyi files where both exist, and ensure that
their exported names match.  Since there's not an obvious way to bundle these
two as a dependency up front (conditionally when both exist), you can use the
protocol to report results where the additional input is mentioned.

```json
{
    "t": "M",
    "filename": "demo/api.pyi",
    "additional_inputs": ["demo/api.py"],
    "new_bytes": null,
    "diffstat": null,
    "diff": null,
    "msg": "demo/api.pyi is missing the exported name 'Foo'"
}
```

## Intent (and other flags)




## Additional flags

The default way things are run operates on copies, so is pretty similar to a
dry run.  The big exception is if something relies on *changing* external
state; these should be protected with `external_state = true` which requires
either specifying one rule exactly by name, or passing the `--yolo` flag which
is appended to the rule command.


