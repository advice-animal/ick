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
