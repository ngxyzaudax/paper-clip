import typer

from cli.calibrate_cmd import calibrate_app
from cli.decode_cmd import decode_command
from cli.devices_cmd import devices_command
from cli.encode_cmd import encode_command
from cli.health_cmd import health_app
from cli.print_cmd import print_command
from cli.scan_cmd import scan_command

app = typer.Typer(
    name="paper-clip",
    help="Serialize data to physical paper using color-coded dot grids.",
    invoke_without_command=True,
)


@app.callback()
def main_callback(ctx: typer.Context) -> None:
    """Open the web interface when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        from web.server import serve
        serve()


@app.command("serve")
def serve_command(
    port: int = typer.Option(8765, help="Port to bind, or the next free port."),
    host: str = typer.Option("127.0.0.1", help="Loopback by default. Any other host requires the printed token."),
    no_browser: bool = typer.Option(False, "--no-browser", help="Do not open a browser."),
) -> None:
    """Serve the web interface."""
    from web.server import serve
    serve(host, port, open_browser=not no_browser)


app.add_typer(calibrate_app, name="calibrate")
app.add_typer(health_app, name="health")
app.command("encode")(encode_command)
app.command("decode")(decode_command)
app.command("devices")(devices_command)
app.command("print")(print_command)
app.command("scan")(scan_command)
