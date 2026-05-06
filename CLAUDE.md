# ick

## Running tests

Use `make test` to run the test suite. The sandbox must be disabled because
tests write to the ick cache directory:

```
source .venv/bin/activate && make test
```

Run with `dangerouslyDisableSandbox: true`.

## Scenario tests

See `tests/scenarios/README.md` for how scenario tests work, including how to
update or create `.txt` files.
