# CLI Reference

The `ick` command-line tool is an applier of fine source code fixes. This page documents all available commands and their options.

## Global Options

These options are available for all commands:

| Option | Description |
|--------|-------------|
| `--version` | Show the version and exit |
| `-v` | Verbosity, specify once for INFO and repeat for more |
| `--verbose INTEGER` | Log verbosity (unset=WARNING, 0=INFO, 1=VLOG_1, 2=VLOG_2, ..., 10=DEBUG) |
| `--vmodule TEXT` | Comma-separated logger=level values, same scheme as --verbose |
| `--trace FILENAME` | Trace output filename |
| `--isolated-repo` | Isolate from user-level config |
| `--target TEXT` | Directory to modify |
| `--rules-repo TEXT` | Ad-hoc rules repo to use, either a URL or file path |
| `--help` | Show help message and exit |

## Commands

### Filter Support

The following commands support optional `FILTERS` arguments to narrow down which rules to work with:
- `list-rules` - Filter which rules to list
- `run` - Filter which rules to execute
- `test-rules` - Filter which rules to test

Filters can be:
- **Rule name** - Exact name of a specific rule
- **Rule prefix** - Partial name to match multiple rules
- **Urgency string** - Match rules with specific urgency such as "now"

### `find-projects`

Lists projects found in the current repository.

```bash
ick find-projects [OPTIONS]
```

### `list-rules`

Lists rules applicable to the current repository.

```bash
ick list-rules [OPTIONS] [FILTERS]...
```

**Specific Options:**
- `--json` - Outputs JSON with rules info

**Examples:**
```bash
# List all applicable rules
ick list-rules

# List rules in JSON format
ick list-rules --json

# List all rules with the prefix "python"
ick list-rules python
```

### `run`

Run the applicable rules on the current repository/path. By default, this performs a dry run that shows statistics of changes to files.

```bash
ick run [OPTIONS] [FILTERS]...
```

**Specific Options:**
- `-n, --dry-run` - Dry run mode, show counts of lines to change (default)
- `-p, --patch` - Show diff of what changes would be made
- `--apply` - Apply changes made by rule
- `--json` - JSON output of modifications made by rule (doesn't apply changes)
- `--skip-update` - When loading rules from a repo, don't pull if some version already exists locally

Note: Only one of the flags `--dryrun`, `--patch`, and `--apply` can be used at a time.

**Examples:**
```bash
# Dry run (default) - shows what would be changed
ick run

# Show patches of changes
ick run --patch

# Apply changes to files
ick run --apply

# Run specific rules
ick run python-formatting

# Run with urgency filter
ick run now

# Output results as JSON
ick run --json
```

### `test-rules`

Run rule self-tests. With no filters, runs tests in all rules.

```bash
ick test-rules [OPTIONS] [FILTERS]...
```

**Examples:**
```bash
# Test all rules
ick test-rules

# Test specific rules
ick test-rules python-formatting
```
