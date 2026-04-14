from __future__ import annotations

import click


class FlexibleGroup(click.Group):
    """Click Group that accepts global options after the subcommand name."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        # Find position of a known subcommand in args (stop at --)
        cmd_pos = None
        for i, arg in enumerate(args):
            if arg == "--":
                break
            if not arg.startswith("-") and arg in self.commands:
                cmd_pos = i
                break

        if cmd_pos is None:
            return super().parse_args(ctx, args)

        # Build lookup of group option strings -> Option object
        group_params: dict[str, click.Option] = {}
        for param in self.params:
            if isinstance(param, click.Option):
                for opt in param.opts:
                    group_params[opt] = param

        pre_cmd = list(args[:cmd_pos])
        sub_and_rest = list(args[cmd_pos:])

        # Scan sub_and_rest (skip index 0 = subcommand name) and lift group options
        lifted: list[str] = []
        kept: list[str] = [sub_and_rest[0]]
        i = 1
        while i < len(sub_and_rest):
            arg = sub_and_rest[i]
            if arg == "--":
                # Stop lifting; keep everything from here onward as-is
                kept.extend(sub_and_rest[i:])
                break
            # Handle --opt=val form
            key, eq, _ = arg.partition("=")
            if key in group_params and eq == "=":
                lifted.append(arg)
                i += 1
                continue
            if arg in group_params:
                param = group_params[arg]
                lifted.append(arg)
                i += 1
                takes_value = not param.is_flag and not getattr(param, "count", False)
                nargs = param.nargs if takes_value else 0
                for _ in range(nargs):
                    if i < len(sub_and_rest):
                        lifted.append(sub_and_rest[i])
                        i += 1
                continue
            kept.append(arg)
            i += 1

        return super().parse_args(ctx, pre_cmd + lifted + kept)

    def resolve_command(self, ctx: click.Context, args: list[str]) -> tuple[str | None, click.Command | None, list[str]]:
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError as e:
            formatter = click.HelpFormatter()
            with formatter.section("Available commands"):
                formatter.write_dl([(name, self.get_command(ctx, name).get_short_help_str()) for name in sorted(self.list_commands(ctx))])
            raise click.UsageError(f"{e.format_message()}\n\n{formatter.getvalue().rstrip()}") from e
