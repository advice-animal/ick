from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path
from typing import IO, Any, Callable, Optional

import click
import keke
from feedforward import Run
from moreorless.click import echo_color_precomputed_diff
from rich import print
from vmodule import vmodule_init

from ick._env_check import check_writable_dirs
from ick.add_rule import add_rule_structure
from ick.util import convert_path_to_python_identifiers
from ick_protocol import RuleStatus, Scope, Urgency

from ._regex_translate import rule_name_re
from .click_better import FlexibleGroup
from .config import RuntimeConfig, Settings, load_main_config, load_rules_config, one_repo_config
from .git import find_repo_root
from .project_finder import find_projects as find_projects_fn
from .runner import Runner, _demo_done_callback, _demo_status_callback, fmt_qualname
from .types_project import maybe_repo


@click.group(cls=FlexibleGroup)
@click.version_option()
@click.option("-v", count=True, default=0, help="Verbosity, specify once for INFO and repeat for more")
@click.option("--verbose", type=int, help="Log verbosity (unset=WARNING, 0=INFO, 1=VLOG_1, 2=VLOG_2, ..., 10=DEBUG)")
@click.option("--vmodule", help="comma-separated logger=level values, same scheme as --verbose")
@click.option("--trace", type=click.File(mode="w"), help="Trace output filename")
@click.option("--isolated-repo", is_flag=True, help="Isolate from user-level config", envvar="ICK_ISOLATED_REPO")
@click.option("--target", default=".", help="Directory to modify")  # TODO path, existing
@click.option("--rules-repo", help="ad-hoc rules repo to use, either a URL or directory")
@click.pass_context
def main(
    ctx: click.Context,
    v: int,
    verbose: int,
    vmodule: str,
    trace: IO[str] | None,
    isolated_repo: bool,
    target: str,
    rules_repo: str | None,
) -> None:
    """
    Applier of fine source code fixes since 2025
    """
    verbose_init(v, verbose, vmodule)
    ctx.with_resource(keke.TraceOutput(file=trace))

    if msg := check_writable_dirs():
        raise click.ClickException(f"{msg}; ick may hang or fail")

    # This takes a target because rules can be defined in the target repo too
    cur = Path(target).expanduser()
    conf = load_main_config(cur, isolated_repo=isolated_repo)
    if rules_repo is not None:
        rules_config = one_repo_config(rules_repo)
    else:
        rules_config = load_rules_config(cur, isolated_repo=isolated_repo)
    ctx.obj = RuntimeConfig(conf, rules_config, Settings(isolated_repo=isolated_repo))

    repo_path = find_repo_root(cur)
    ctx.obj.repo = maybe_repo(repo_path, ctx.with_resource)


@main.command()
@click.pass_context
def find_projects(ctx: click.Context) -> None:
    """
    Lists projects found in the current repo
    """
    for proj in find_projects_fn(ctx.obj.repo, ctx.obj.repo.zfiles, ctx.obj.main_config):
        print(f"{proj.subdir!r:20} ({proj.typ})")


@main.command()
@click.option("--json", "json_flag", is_flag=True, help="Outputs json with rules info by qualname (can be used with run --json)")
@click.option("-k", "substring", default="", help="Substring match on rule name (including prefix)")
@click.argument("filters", nargs=-1)
@click.pass_context
def list_rules(ctx: click.Context, json_flag: bool, substring: str, filters: list[str]) -> None:
    """
    Lists rules applicable to the current repo
    """
    ctx.obj.filter_config.min_urgency = min(Urgency)  # List all urgencies unless specified by filters
    apply_filters(ctx, filters, substring)
    r = Runner(ctx.obj, ctx.obj.repo)
    if json_flag:
        r.echo_rules_json()
    else:
        r.echo_rules()


@main.command()
@click.pass_context
@click.option("-k", "substring", default="", help="Substring match on rule name (including prefix)")
@click.option("--update", is_flag=True, help="Update expected test output with actual rule output")
@click.argument("filters", nargs=-1)
def test_rules(ctx: click.Context, substring: str, update: bool, filters: list[str]) -> None:
    """
    Run rule self-tests.

    With no filters, run tests in all rules.

    Use --update to overwrite expected output with the actual output from the
    current rule implementation. Review the changes before committing.
    """
    ctx.obj.filter_config.min_urgency = min(Urgency)  # Test all urgencies unless specified by filters
    apply_filters(ctx, filters, substring)
    r = Runner(ctx.obj, ctx.obj.repo)
    sys.exit(r.test_rules(update=update))


@main.command()
@click.pass_context
@click.argument("rule_name", metavar="rule-name")
@click.argument(
    "target_directory", type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=str), metavar="target-directory"
)
@click.option("--impl", default="python", help="The impl config for the rule. Defaults to python")
@click.option("--inputs", multiple=True, default=None, help="List of input files and glob patterns (recommended)")
@click.option(
    "--urgency",
    default=Urgency.LATER,
    type=click.Choice(Urgency, case_sensitive=False),
    help="Urgency level for the rule",
)
@click.option(
    "--scope",
    default=Scope.FILE,
    type=click.Choice(Scope, case_sensitive=False),
    help="Scope of the rule",
)
@click.option("--description", type=str, help="Description for the rule")
def add_rule(
    ctx: click.Context,
    rule_name: str,
    target_directory: str,
    impl: str,
    inputs: tuple[str, ...],
    urgency: Urgency,
    scope: Scope,
    description: str,
) -> None:
    """
    Generate the file structure for a new rule

    rule-name (TEXT): The name of the new rule\n
    target-directory (PATH): The desired directory of the new rule.
    """
    # TODO: Check if rule qualname already exists using ctx.obj
    if impl != "python":
        print("Rule structure initialization for non-python rules is not implemented yet")
        sys.exit(1)

    if scope == scope.FILE and not inputs:
        print("File-scoped rules (the default) require an `inputs` section to work!")
        sys.exit(1)

    # validate target_directory path
    target_directory_path = Path(target_directory)
    assert not target_directory_path.is_absolute(), "Please use a relative path from the repo root"

    target_directory_path = convert_path_to_python_identifiers(target_directory_path)

    add_rule_structure(
        rule_name=rule_name,
        target_path=target_directory_path,
        impl=impl,
        inputs=inputs,
        urgency=urgency.value,
        scope=scope.value,
        description=description,
    )


@main.command()
@click.option("-n", "--dry-run", is_flag=True, help="Dry run mode, show counts of lines to change (default)")
@click.option("-p", "--patch", is_flag=True, help="Show patches of changes to make")
@click.option("--apply", is_flag=True, help="Apply changes")
@click.option("--json", "json_flag", is_flag=True, help="Outputs modifications json by rule qualname (can be used with list-rules --json)")
@click.option("--skip-update", is_flag=True, help="When loading rules from a repo, don't pull if some version already exists locally")
@click.option("--emojis", is_flag=True, help="Show a waterfall of emojis as work is being done")
@click.option("--parallelism", type=int, default=0, help="Number of parallel workers (default: auto)")
@click.option("-k", "substring", default="", help="Substring match on rule name (including prefix)")
@click.argument("filters", nargs=-1)
@click.pass_context
def run(
    ctx: click.Context,
    dry_run: bool,
    patch: bool,
    apply: bool,
    json_flag: bool,
    skip_update: bool,
    emojis: bool,
    parallelism: int,
    substring: str,
    filters: list[str],
) -> None:
    """
    Run the applicable rules to the current repo/path

    The default is a dry run that shows stats of changes to files.

    Pass either a rule name, rule prefix, or an urgency string like
    "now" to filter the rules.

    Use --apply to apply rules' changes.
    """

    num_provided = sum([dry_run, patch, apply])
    if num_provided > 1:
        print("Only one of --dry-run, --patch, and --apply can be provided")
        sys.exit(1)
    elif num_provided == 0:
        dry_run = True

    ctx.obj.settings.dry_run = dry_run
    ctx.obj.settings.apply = apply
    ctx.obj.settings.skip_update = skip_update

    if filters:
        ctx.obj.filter_config.min_urgency = min(Urgency)
    else:
        ctx.obj.filter_config.min_urgency = Urgency.LATER

    apply_filters(ctx, filters, substring)

    # DO THE NEEDFUL

    # TODO boring progress bar default
    status_callback: Callable[[Run[Any, Any]], None] | None = None
    done_callback: Callable[[Run[Any, Any]], None] | None = None
    if emojis:
        status_callback = _demo_status_callback
        done_callback = _demo_done_callback
    elif not json_flag and sys.stderr.isatty():
        bar = None

        def progressbar_status(run: Run[Any, Any]) -> None:
            nonlocal bar
            if not bar:
                bar = click.progressbar(length=len(run._steps), label="Running...")
                ctx.with_resource(bar)
            bar.update(run._finalized_idx)

        status_callback = progressbar_status
        done_callback = lambda _: print("\n")  # noqa: E731

    r = Runner(ctx.obj, ctx.obj.repo, parallelism=parallelism)
    steps = r.build_steps_for_rules(
        status_callback=status_callback,
        done_callback=done_callback,
    )

    if json_flag:
        rule_hours: dict[str, int | None] = {impl.rule_config.qualname: impl.rule_config.hours for impl in r.iter_rule_impl()}

        results = collections.defaultdict(list)
        for result in r.run_steps(steps):
            modifications = []
            for mod in result.modifications:
                modifications.append({"file_name": mod.filename, "diff_stat": mod.diffstat})
            output = {
                "project_name": result.project,
                "status": result.finished.status,
                "modified": modifications,
                # The meaning of this field depends on the status field above
                "message": result.finished.message,
                "metadata": result.finished.metadata,
                "hours": rule_hours.get(result.rule),
            }
            results[result.rule].append(output)

        json.dump({"results": results}, sys.stdout, indent=4)
        sys.stdout.write("\n")

    else:
        for result in r.run_steps(steps):
            where = f" on {result.project}" if result.project else ""
            print(f"-> [bold]{fmt_qualname(result.rule, result.prefix)}[/bold]{where}: ", end="")
            match result.finished.status:
                case RuleStatus.ERROR:
                    print("[red]ERROR[/red]")
                    lines = result.finished.message.splitlines()
                    if ctx.parent.params.get("v", 0) > 0:
                        for line in lines:
                            print("    ", line)
                    elif lines:
                        print("    ", lines[0])
                        if len(lines) >= 3:
                            print("    ", "... (pass -v for complete message)")
                        if len(lines) > 1:
                            print("    ", lines[-1])
                case RuleStatus.NEEDS_WORK:
                    print("[yellow]NEEDS_WORK[/yellow]")
                    for line in result.finished.message.splitlines():
                        print("    ", line)
                case RuleStatus.SUCCESS:
                    print("[green]OK[/green]")
                case _:  # pragma: no cover
                    assert False, f"Unhandled status {result.finished.status}"

            if patch:
                for mod in result.modifications:
                    if mod.diff:
                        echo_color_precomputed_diff(mod.diff)
            elif dry_run:
                for mod in result.modifications:
                    print("    ", mod.filename, mod.diffstat)
            else:
                assert apply
                for mod in result.modifications:
                    path = ctx.obj.repo.root / mod.filename
                    if mod.new_bytes is None:
                        path.unlink()
                    else:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(mod.new_bytes)
                    print(f"   Change made: {mod.filename:30s} {mod.diffstat}")


main.add_command(
    click.Command(
        "run-rules",
        params=run.params,
        callback=run.callback,
        help="Alias for the `run` command.",
    )
)


@main.command()
@click.argument("before_ref")
@click.argument("after_ref", default="HEAD")
@click.option("--json", "json_flag", is_flag=True, help="Output comparison as JSON")
@click.option("--exit-code", is_flag=True, help="Exit non-zero if any regressions found")
@click.option("-k", "substring", default="", help="Substring match on rule name (including prefix)")
@click.argument("filters", nargs=-1)
@click.pass_context
def compare(
    ctx: click.Context,
    before_ref: str,
    after_ref: str,
    json_flag: bool,
    exit_code: bool,
    substring: str,
    filters: tuple[str, ...],
) -> None:
    """
    Compare ick results between two git refs.

    Checks out BEFORE_REF and AFTER_REF as worktrees, runs ick on each
    against the current target, and reports improvements and regressions.

    Summary metrics: rules flagging count and hours at risk (when the
    hours field is set on rules).
    """
    import dataclasses

    from .compare import compare_results, managed_worktree, run_ick_json, summarize
    from .git import find_repo_root

    ick_repo_root = find_repo_root(Path(__file__).parent)
    target = Path(ctx.parent.params["target"])  # type: ignore[union-attr]

    extra_args: list[str] = []
    if substring:
        extra_args += ["-k", substring]
    extra_args.extend(filters)

    print(f"Comparing [bold]{before_ref}[/bold]...[bold]{after_ref}[/bold] against {target}", file=sys.stderr)

    print(f"  Checking out {before_ref}...", file=sys.stderr)
    with managed_worktree(ick_repo_root, before_ref) as wt_before:
        print(f"  Running ick at {before_ref}...", file=sys.stderr)
        before_results = run_ick_json(wt_before, target, extra_args)

    print(f"  Checking out {after_ref}...", file=sys.stderr)
    with managed_worktree(ick_repo_root, after_ref) as wt_after:
        print(f"  Running ick at {after_ref}...", file=sys.stderr)
        after_results = run_ick_json(wt_after, target, extra_args)

    comparisons = compare_results(before_results, after_results)
    summary = summarize(comparisons)

    if json_flag:
        out = {
            "before_ref": before_ref,
            "after_ref": after_ref,
            "comparisons": [dataclasses.asdict(c) for c in comparisons],
            "summary": summary,
        }
        json.dump(out, sys.stdout, indent=4)
        sys.stdout.write("\n")
    else:
        _colors = {
            "improved": "green",
            "regressed": "red",
            "new": "cyan",
            "removed": "yellow",
            "unchanged": "dim",
        }
        for c in comparisons:
            color = _colors.get(c.verdict, "")
            h = f" ({c.hours}h)" if c.hours is not None else ""
            print(f"[{color}]{c.verdict.upper():10}[/{color}] {c.rule}{h}: {c.detail}")

        print()
        hrs_before = f"{summary['hours_before']}h" if summary["hours_before"] is not None else "?"
        hrs_after = f"{summary['hours_after']}h" if summary["hours_after"] is not None else "?"
        delta = summary["rules_delta"]
        print(f"Rules flagging: {summary['rules_flagging_before']} -> {summary['rules_flagging_after']} ({delta:+d})")
        if summary["hours_before"] is not None:
            h_delta = summary["hours_delta"]
            print(f"Hours at risk:  {hrs_before} -> {hrs_after} ({h_delta:+d}h)")

    if exit_code and any(c.verdict == "regressed" for c in comparisons):
        sys.exit(1)


def apply_filters(ctx: click.Context, filters: list[str], substring: str) -> None:
    if substring and filters:
        raise click.UsageError("Cannot use -k together with positional filters")

    if not substring and not filters:
        pass
    elif len(filters) == 1 and getattr(Urgency, filters[0].upper(), None):
        # python 3.11 doesn't support __contains__ on enum, but also doesn't
        # support .get and the choices are [] catching the exception or getattr
        # which is what I can fit on one line.
        urgency = Urgency[filters[0].upper()]
        ctx.obj.filter_config.min_urgency = urgency
    elif substring:
        ctx.obj.filter_config.name_filter_re = f".*{re.escape(substring)}.*"
    else:
        ctx.obj.filter_config.name_filter_re = "|".join(rule_name_re(name) for name in filters)


def verbose_init(v: int, verbose: Optional[int], vmodule: Optional[str]) -> None:
    if verbose is None:
        if v >= 4:
            verbose = 10  # DEBUG
        elif v >= 3:
            verbose = 2  # VLOG_2
        elif v >= 2:
            verbose = 1  # VLOG_1
        elif v >= 1:
            verbose = 0  # INFO
        else:
            verbose = None  # WARNING
    vmodule_init(verbose, vmodule)
