from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
import keke
from vmodule import vmodule_init

from ick_protocol import Urgency

from ._regex_translate import advice_name_re
from .config import RuntimeConfig, Settings, load_hooks_config, load_main_config
from .git import find_repo_root
from .project_finder import find_projects as find_projects_fn
from .runner import Runner
from .types_project import Repo


@click.group()
@click.version_option()
def main():
    """
    Applier of fine source code fixes since 2025
    """


@main.command()
@click.option("-v", count=True, default=0, help="Verbosity, specify once for INFO and repeat for more")
@click.option("--verbose", type=int, help="Log verbosity (unset = WARNING, 0 = INFO, 1 = VLOG_1, ..., 10 = DEBUG)")
@click.option("--vmodule", help="comma-separated logger:level values, same scheme as --verbose")
@click.option("--trace", type=click.File(mode="w"), help="Trace output filename")
@click.option("--target", default=".", help="Directory to modify")  # TODO path, existing
@click.pass_context
def find_projects(ctx, v, verbose, vmodule, trace, target):
    """
    Lists projects in the current repo, using current settings
    """
    verbose_init(v, verbose, vmodule)
    ctx.with_resource(keke.TraceOutput(file=trace))

    cur = Path(target)
    conf = load_main_config(cur)
    repo_path = find_repo_root(cur)
    repo = Repo(repo_path)
    for proj in find_projects_fn(repo, repo.zfiles, conf):
        print(f"{proj.subdir!r:20} ({proj.typ})")


@main.command()
@click.option("-v", count=True, default=0, help="Verbosity, specify once for INFO and repeat for more")
@click.option("--verbose", type=int, help="Log verbosity (unset = WARNING, 0 = INFO, 1 = VLOG_1, ..., 10 = DEBUG)")
@click.option("--vmodule", help="comma-separated logger:level values, same scheme as --verbose")
@click.option("--trace", type=click.File(mode="w"), help="Trace output filename")
@click.option("--target", default=".", help="Directory to modify")  # TODO path, existing
@click.pass_context
def list_hooks(ctx, v, verbose, vmodule, trace, target):
    """
    Lists projects in the current repo, using current settings
    """
    verbose_init(v, verbose, vmodule)
    ctx.with_resource(keke.TraceOutput(file=trace))

    # This takes a target because hooks can be defined in the target repo too
    conf = load_main_config(Path(target))
    hc = load_hooks_config(Path(target))
    ctx.obj = RuntimeConfig(conf, hc, Settings())

    r = Runner(ctx.obj)
    r.echo_hooks()


@main.command()
@click.option("-v", count=True, default=0, help="Verbosity, specify once for INFO and repeat for more")
@click.option("--verbose", type=int, help="Log verbosity (unset = WARNING, 0 = INFO, 1 = VLOG_1, ..., 10 = DEBUG)")
@click.option("--vmodule", help="comma-separated logger:level values, same scheme as --verbose")
@click.option("--trace", type=click.File(mode="w"), help="Trace output filename")
@click.option("--target", default=".", help="Directory to modify")  # TODO path, existing
@click.pass_context
def selftest(ctx, v, verbose, vmodule, trace, target):
    """ """
    verbose_init(v, verbose, vmodule)
    ctx.with_resource(keke.TraceOutput(file=trace))

    # This takes a target because hooks can be defined in the target repo too
    cur = Path(target)
    conf = load_main_config(cur)
    hc = load_hooks_config(cur)
    ctx.obj = RuntimeConfig(conf, hc, Settings())
    repo_path = find_repo_root(cur)
    repo = Repo(repo_path)

    r = Runner(ctx.obj, repo)
    r.selftest()


@main.command()
# These are ALL defined here (and repeated elsewhere) because click is picky
# about whether they come before or after the subcommand.
@click.option("-v", count=True, default=0, help="Verbosity, specify once for INFO and repeat for more")
@click.option("--verbose", type=int, help="Log verbosity (unset = WARNING, 0 = INFO, 1 = VLOG_1, ..., 10 = DEBUG)")
@click.option("--vmodule", help="comma-separated logger:level values, same scheme as --verbose")
@click.option("--trace", type=click.File(mode="w"), help="Trace output filename")
@click.option("-n", "--dry-run", is_flag=True, help="Dry run mode, on by default sometimes")
@click.option("--yolo", is_flag=True, help="Yolo mode enables modifying external state")
@click.option("--target", default=".", help="Directory to modify")  # TODO path, existing
@click.argument("filters", nargs=-1)
@click.pass_context
def run(ctx, v, verbose, vmodule, trace, dry_run: bool, yolo: bool, filters: list[str], target: str):
    """
    Run all (or explicitly specified) hooks, by default in a medium-dry-run
    mode, in their defined order.

    Otherwise, pass either a hook name, hook prefix, or an urgency string like
    "now" to apply all necessary, successful ones in order.
    """
    verbose_init(v, verbose, vmodule)
    ctx.with_resource(keke.TraceOutput(file=trace))

    cur = Path(target)
    conf = load_main_config(cur)
    repo_path = find_repo_root(cur)
    repo = Repo(repo_path)

    hc = load_hooks_config(cur)
    ctx.obj = RuntimeConfig(conf, hc, Settings())
    ctx.obj.settings.dry_run = dry_run
    ctx.obj.settings.yolo = yolo

    if len(filters) == 0:
        ctx.obj.settings.dry_run = True  # force it
    elif len(filters) == 1:
        urgency = Urgency[filters[0].upper()]
        ctx.obj.filter_config.urgency_filter = urgency
    else:
        ctx.obj.filter_config.name_filter_re = "|".join(advice_name_re(name) for name in filters)

    # DO THE NEEDFUL

    r = Runner(ctx.obj, repo, explicit_project=None)
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
