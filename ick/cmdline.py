from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
import keke
from moreorless.click import echo_color_precomputed_diff
from rich import print
from vmodule import vmodule_init

from ick_protocol import Urgency

from ._regex_translate import advice_name_re
from .config import RuntimeConfig, Settings, load_main_config, load_rules_config
from .git import find_repo_root
from .project_finder import find_projects as find_projects_fn
from .runner import Runner
from .types_project import maybe_repo


@click.group()
@click.version_option()
@click.option("-v", count=True, default=0, help="Verbosity, specify once for INFO and repeat for more")
@click.option("--verbose", type=int, help="Log verbosity (unset = WARNING, 0 = INFO, 1 = VLOG_1, ..., 10 = DEBUG)")
@click.option("--vmodule", help="comma-separated logger:level values, same scheme as --verbose")
@click.option("--trace", type=click.File(mode="w"), help="Trace output filename")
@click.option("--isolated-repo", is_flag=True, help="Isolate from user-level config")
@click.option("--target", default=".", help="Directory to modify")  # TODO path, existing
@click.pass_context
def main(ctx, v, verbose, vmodule, trace, isolated_repo, target) -> None:
    """
    Applier of fine source code fixes since 2025
    """
    verbose_init(v, verbose, vmodule)
    ctx.with_resource(keke.TraceOutput(file=trace))

    # This takes a target because rules can be defined in the target repo too
    cur = Path(target)
    conf = load_main_config(cur, isolated_repo=isolated_repo)
    hc = load_rules_config(cur, isolated_repo=isolated_repo)
    ctx.obj = RuntimeConfig(conf, hc, Settings(isolated_repo=isolated_repo))

    repo_path = find_repo_root(cur)
    ctx.obj.repo = maybe_repo(repo_path, ctx.with_resource)


@main.command()
@click.pass_context
def find_projects(ctx):
    """
    Lists projects found in the current repo
    """
    for proj in find_projects_fn(ctx.obj.repo, ctx.obj.repo.zfiles, ctx.obj.main_config):
        print(f"{proj.subdir!r:20} ({proj.typ})")


@main.command()
@click.pass_context
def list_rules(ctx):
    """
    Lists rules applicable to the current repo
    """
    r = Runner(ctx.obj, ctx.obj.repo)
    r.echo_rules()


@main.command()
@click.pass_context
def test_rules(ctx):
    """
    Run self-tests against all rules.
    """
    r = Runner(ctx.obj, ctx.obj.repo)
    sys.exit(r.test_rules())


@main.command()
@click.option("-n", "--dry-run", is_flag=True, help="Dry run mode, on by default sometimes")
@click.option("-p", "--patch", is_flag=True, help="Show patch instead of applying")
@click.option("--yolo", is_flag=True, help="Yolo mode enables modifying external state")
@click.option("--json", "json_flag", is_flag=True, help="Outputs json indicating if a rule caused modifications")
@click.argument("filters", nargs=-1)
@click.pass_context
def run(ctx, dry_run: bool, patch: bool, yolo: bool, json_flag: bool, filters: list[str]):
    """
    Run the applicable rules to the current repo/path

    If you don't provide filters, the default is a dry-run style mode for all rules.

    Otherwise, pass either a rule name, rule prefix, or an urgency string like
    "now" to apply all necessary, successful ones in order.
    """

    ctx.obj.settings.dry_run = dry_run
    ctx.obj.settings.yolo = yolo

    if len(filters) == 0:
        ctx.obj.settings.dry_run = True  # force it
    elif len(filters) == 1 and getattr(Urgency, filters[0].upper(), None):
        # python 3.11 doesn't support __contains__ on enum, but also doesn't
        # support .get and the choices are [] catching the exception or getattr
        # which is what I can fit on one line.
        urgency = Urgency[filters[0].upper()]
        ctx.obj.filter_config.urgency_filter = urgency
    else:
        ctx.obj.filter_config.name_filter_re = "|".join(advice_name_re(name) for name in filters)

    # DO THE NEEDFUL

    results = {}

    r = Runner(ctx.obj, ctx.obj.repo, explicit_project=None)
    for result in r.run():
        if not json_flag:
            print(f"-> [bold]{result.rule}[/bold] on {result.project}", end="")
        if result.finished.error and not json_flag:
            print("[red]ERROR[/red]")
            for line in result.finished.message.splitlines():
                print("    ", line)
        else:
            if not json_flag:
                print("[green]OK[/green]")

        if json_flag:
            modifications = []
            for mod in result.modifications:
                modifications.append({"file_name": mod.filename, "diff_stat": mod.diffstat})
            ok_status = not result.finished.error
            error_message = result.finished.message if result.finished.error else None
            project = result.project
            modified = modifications
            output = {"project_name": project, "ok_status": ok_status, "modified": modified, "error_message": error_message}
            if result.rule not in results:
                results[result.rule] = [output]
            else:
                results[result.rule].append(output)

        elif patch:
            for mod in result.modifications:
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


def verbose_init(v: int, verbose: Optional[int], vmodule: Optional[str]) -> None:
    if verbose is None:
        if v >= 3:
            verbose = 10  # DEBUG
        elif v >= 2:
            verbose = 1  # VLOG_1
        elif v >= 1:
            verbose = 0  # INFO
        else:
            verbose = None  # WARNING
    vmodule_init(verbose, vmodule)
