from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
import keke
from vmodule import vmodule_init

from ick_protocol import Urgency

from ._regex_translate import advice_name_re
from .config import RuntimeConfig, Settings, load_main_config, load_rules_config
from .git import find_repo_root
from .project_finder import find_projects as find_projects_fn
from .runner import Runner
from .types_project import NullRepo, Repo


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

    if (repo_path / ".git").exists():
        ctx.obj.repo = Repo(repo_path)
    else:
        ctx.obj.repo = NullRepo()


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
    r.test_rules()


@main.command()
@click.option("-n", "--dry-run", is_flag=True, help="Dry run mode, on by default sometimes")
@click.option("--yolo", is_flag=True, help="Yolo mode enables modifying external state")
@click.argument("filters", nargs=-1)
@click.pass_context
def run(ctx, dry_run: bool, yolo: bool, filters: list[str]):
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
    elif len(filters) == 1 and filters[0].upper() in Urgency:
        urgency = Urgency[filters[0].upper()]
        ctx.obj.filter_config.urgency_filter = urgency
    else:
        ctx.obj.filter_config.name_filter_re = "|".join(advice_name_re(name) for name in filters)

    # DO THE NEEDFUL

    r = Runner(ctx.obj, ctx.obj.repo, explicit_project=None)
    r.run()

    # PRINT THE OUTPUT


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
