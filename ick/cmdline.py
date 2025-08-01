from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import IO, Optional

import click
import keke
from moreorless.click import echo_color_precomputed_diff
from rich import print
from vmodule import vmodule_init

from ick_protocol import Urgency

from ._regex_translate import advice_name_re
from .config import RuntimeConfig, Settings, load_main_config, load_rules_config, one_repo_config
from .git import find_repo_root
from .project_finder import find_projects as find_projects_fn
from .runner import Runner
from .types_project import maybe_repo


@click.group()
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

    # This takes a target because rules can be defined in the target repo too
    cur = Path(target)
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
@click.argument("filters", nargs=-1)
@click.pass_context
def list_rules(ctx: click.Context, json_flag: bool, filters: list[str]) -> None:
    """
    Lists rules applicable to the current repo
    """
    apply_filters(ctx, filters)
    r = Runner(ctx.obj, ctx.obj.repo)
    if json_flag:
        r.echo_rules_json()
    else:
        r.echo_rules()


@main.command()
@click.pass_context
@click.argument("filters", nargs=-1)
def test_rules(ctx: click.Context, filters: list[str]) -> None:
    """
    Run rule self-tests.

    With no filters, run tests in all rules.
    """
    apply_filters(ctx, filters)
    r = Runner(ctx.obj, ctx.obj.repo)
    sys.exit(r.test_rules())


@main.command()
@click.option("-n", "--dry-run", is_flag=True, help="Dry run mode, on by default sometimes")
@click.option("-p", "--patch", is_flag=True, help="Show patch instead of applying")
@click.option("--yolo", is_flag=True, help="Yolo mode enables modifying external state")
@click.option("--json", "json_flag", is_flag=True, help="Outputs modifications json by rule qualname (can be used with list-rules --json)")
@click.option("--skip-update", is_flag=True, help="When loading rules from a repo, don't pull if some version already exists locally")
@click.argument("filters", nargs=-1)
@click.pass_context
def run(
    ctx: click.Context,
    dry_run: bool,
    patch: bool,
    yolo: bool,
    json_flag: bool,
    skip_update: bool,
    filters: list[str],
) -> None:
    """
    Run the applicable rules to the current repo/path

    If you don't provide filters, the default is a dry-run style mode for all rules.

    Otherwise, pass either a rule name, rule prefix, or an urgency string like
    "now" to apply all necessary, successful ones in order.
    """

    ctx.obj.settings.dry_run = dry_run
    ctx.obj.settings.yolo = yolo
    ctx.obj.settings.skip_update = skip_update

    if len(filters) == 0:
        ctx.obj.settings.dry_run = True  # force it
    else:
        apply_filters(ctx, filters)

    # DO THE NEEDFUL

    results = {}

    r = Runner(ctx.obj, ctx.obj.repo)
    for result in r.run():
        if not json_flag:
            where = f"on {result.project} " if result.project else ""
            print(f"-> [bold]{result.rule}[/bold] {where}", end="")
            if result.finished.status is None:
                print("[red]ERROR[/red]")
                for line in result.finished.message.splitlines():
                    print("    ", line)
            elif result.finished.status is False:
                print("[yellow]FAIL[/yellow]")
                for line in result.finished.message.splitlines():
                    print("    ", line)
            else:
                print("[green]OK[/green]")

        if json_flag:
            modifications = []
            for mod in result.modifications:
                modifications.append({"file_name": mod.filename, "diff_stat": mod.diffstat})
            output = {
                "project_name": result.project,
                "status": result.finished.status,
                "modified": modifications,
                # The meaning of this field depends on the status field above
                "message": result.finished.message,
            }
            if result.rule not in results:
                results[result.rule] = [output]
            else:
                results[result.rule].append(output)

        elif patch:
            for mod in result.modifications:
                if mod.diff:
                    echo_color_precomputed_diff(mod.diff)
        elif ctx.obj.settings.dry_run:
            for mod in result.modifications:
                print("    ", mod.filename, mod.diffstat)
        else:
            for mod in result.modifications:
                path = Path(mod.filename)
                if mod.new_bytes is None:
                    path.unlink()
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(mod.new_bytes)

    if json_flag:
        print(json.dumps({"results": results}, indent=4))


def apply_filters(ctx: click.Context, filters: list[str]) -> None:
    if ctx.info_name in ("test-rules", "list-rules"):
        ctx.obj.filter_config.min_urgency = min(Urgency)  # Test and list rules from all urgencies unless specified by filters

    if not filters:
        pass
    elif len(filters) == 1 and getattr(Urgency, filters[0].upper(), None):
        # python 3.11 doesn't support __contains__ on enum, but also doesn't
        # support .get and the choices are [] catching the exception or getattr
        # which is what I can fit on one line.
        urgency = Urgency[filters[0].upper()]
        ctx.obj.filter_config.min_urgency = urgency

    else:
        ctx.obj.filter_config.name_filter_re = "|".join(advice_name_re(name) for name in filters)


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
