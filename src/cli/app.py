import typer

from cli.decode_cmd import decode_command
from cli.devices_cmd import devices_command
from cli.encode_cmd import encode_command
from cli.print_cmd import print_command
from cli.scan_cmd import scan_command

app = typer.Typer(
    name="paper-clip",
    help="Serialize data to physical paper using color-coded dot grids.",
    invoke_without_command=True,
)


@app.callback()
def main_callback(ctx: typer.Context) -> None:
    """Launch interactive TUI when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        from cli.tui.app import run_tui
        run_tui()


app.command("encode")(encode_command)
app.command("decode")(decode_command)
app.command("devices")(devices_command)
app.command("print")(print_command)
app.command("scan")(scan_command)
