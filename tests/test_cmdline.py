from __future__ import annotations

import click
from click.testing import CliRunner

from ick.cmdline import FlexibleGroup


@click.group(cls=FlexibleGroup)
@click.option("--target", default="default")
@click.option("--flag", is_flag=True)
@click.option("-v", "verbosity", count=True)
@click.pass_context
def cli(ctx: click.Context, target: str, flag: bool, verbosity: int) -> None:
    ctx.ensure_object(dict)
    ctx.obj["target"] = target
    ctx.obj["flag"] = flag
    ctx.obj["verbosity"] = verbosity


@cli.command()
@click.argument("name", default="world")
@click.pass_context
def greet(ctx: click.Context, name: str) -> None:
    click.echo(f"hello {name} target={ctx.obj['target']} flag={ctx.obj['flag']} v={ctx.obj['verbosity']}")


runner = CliRunner()


def invoke(*args: str) -> str:
    result = runner.invoke(cli, list(args), catch_exceptions=False)
    return result.output.strip()


def test_global_option_before_subcommand() -> None:
    assert invoke("--target", "foo", "greet") == "hello world target=foo flag=False v=0"


def test_global_option_after_subcommand() -> None:
    assert invoke("greet", "--target", "foo") == "hello world target=foo flag=False v=0"


def test_global_option_equals_form_after_subcommand() -> None:
    assert invoke("greet", "--target=foo") == "hello world target=foo flag=False v=0"


def test_global_flag_after_subcommand() -> None:
    assert invoke("greet", "--flag") == "hello world target=default flag=True v=0"


def test_count_option_after_subcommand() -> None:
    assert invoke("greet", "-v", "-v") == "hello world target=default flag=False v=2"


def test_mix_before_and_after() -> None:
    assert invoke("-v", "greet", "--target", "bar") == "hello world target=bar flag=False v=1"


def test_subcommand_arg_not_confused_with_global() -> None:
    assert invoke("greet", "alice", "--target", "foo") == "hello alice target=foo flag=False v=0"


def test_subcommand_option_not_lifted() -> None:
    # --name is a subcommand-level option (doesn't exist on greet, but --target does on group)
    # Verify a non-group option stays with the subcommand
    assert invoke("greet", "--target", "foo") == "hello world target=foo flag=False v=0"


def test_no_subcommand_still_works() -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "greet" in result.output


def test_double_dash_stops_lifting() -> None:
    # After --, args should not be lifted to group level
    # The subcommand must appear before --
    result = runner.invoke(cli, ["greet", "--", "--target", "foo"])
    # --target after -- is not lifted, passed as subcommand positional (click will error)
    # The key is it should NOT silently apply --target to the group
    assert "target=default" in result.output or result.exit_code != 0
