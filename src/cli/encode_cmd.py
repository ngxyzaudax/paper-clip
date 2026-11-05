from pathlib import Path

import typer
from rich.console import Console

from cli.display import make_page_callback, make_page_progress, print_error, print_success
from cli.encode_plan import show_encoding_plan
from cli.encoding_cli import cli_encoding_config
from common.config import PaperClipConfig
from common.data_store import digital_dir
from serialization.encode.encoder import prepare_payload
from serialization.encode.fill_sheets import FILL_PRIORITIES, SheetPlan, plan_config
from serialization.encode.frame_payload import PreparedPayload
from serialization.encode.pipeline import encode
from workflows.encode_job import create_encode_job

console = Console()


def encode_command(
    input_file: Path = typer.Argument(..., help="File to encode"),
    num_symbols: int | None = typer.Option(
        None,
        "--num-symbols",
        help=(
            "Per-cell alphabet: 5=CMYK+blank, 8=+R/G/B overprints+blank, 11=+K-tints+blank; "
            "0 is always blank. Allowed values: 5, 8, 11."
        ),
    ),
    cell_size_px: int | None = typer.Option(
        None,
        help="Cell size in pixels. Saved calibration profile, otherwise 22. Must be at least 0.35 mm.",
    ),
    paper_size: str | None = typer.Option(None, help="Paper size (A3, A4, A5, Letter, Legal, etc.)"),
    print_dpi: int | None = typer.Option(None, help="Logical page DPI for layout and print hints"),
    ecc_sym: int | None = typer.Option(
        None, "--ecc-sym", help="Parity bytes per Reed–Solomon block (2–254). Default 50.",
    ),
    redundancy_pages: int | None = typer.Option(None, help="Extra parity pages (fountain)"),
    margin_mm: float | None = typer.Option(None, help="Uniform page margin in mm (all sides)"),
    margin_top_mm: float | None = typer.Option(None, help="Top page margin in mm"),
    margin_right_mm: float | None = typer.Option(None, help="Right page margin in mm"),
    margin_bottom_mm: float | None = typer.Option(None, help="Bottom page margin in mm"),
    margin_left_mm: float | None = typer.Option(None, help="Left page margin in mm"),
    tag_pitch_mm: float | None = typer.Option(None, help="AprilTag pitch in millimetres"),
    tag_size_mm: float | None = typer.Option(
        None, help="AprilTag size in millimetres. Default 4. Allowed: 8, 6, 5, 4, 3.5, 3, 2.5, or 2",
    ),
    qr_module_mm: float | None = typer.Option(
        None, "--qr-module-mm", help="QR module size in millimetres. Default 0.36",
    ),
    dot_ratio: float | None = typer.Option(
        None, "--dot-ratio", help="Dot diameter as a fraction of the cell. Default 0.62",
    ),
    sides: int = typer.Option(1, "--sides", min=1, max=2, help="Sides printed per sheet: 1 or 2 (duplex)"),
    fill_sheets: bool = typer.Option(
        False,
        "--fill-sheets/--no-fill-sheets",
        help="Use every side of the sheets the file needs: extra parity pages, more parity bytes, larger cells",
    ),
    sheets: int = typer.Option(0, "--sheets", min=0, help="With --fill-sheets, fill at least this many sheets"),
    fill_priority: str = typer.Option(
        "protection", "--fill-priority", help="With --fill-sheets, spend spare room on: protection, balanced, or dots",
    ),
    password: str | None = typer.Option(
        None,
        help="Passphrase for payload encryption (built-in default key when omitted)",
    ),
) -> None:
    """Encode a file into print-ready PNG page(s). Saves into data/print/jobs/ by default."""
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        raise typer.Exit(1)
    if fill_priority not in FILL_PRIORITIES:
        print_error(f"--fill-priority must be one of: {', '.join(FILL_PRIORITIES)}")
        raise typer.Exit(1)
    requested = cli_encoding_config(
        num_symbols, cell_size_px, paper_size,
        print_dpi, ecc_sym, redundancy_pages, margin_mm,
        margin_top_mm, margin_right_mm, margin_bottom_mm, margin_left_mm,
        tag_pitch_mm, tag_size_mm, qr_module_mm, dot_ratio,
    )
    raw = input_file.read_bytes()
    plan = SheetPlan(sides, fill_sheets, sheets, fill_priority)
    config = plan_config(raw, requested, input_file.name, plan)
    prepared = prepare_payload(raw, config, filename=input_file.name, passphrase=password)
    _render(input_file, len(raw), config, prepared, password, sides)


def _render(
    input_file: Path,
    file_size: int,
    config: PaperClipConfig,
    prepared: PreparedPayload,
    password: str | None,
    sides: int,
) -> None:
    job_dir = create_encode_job(config, input_file.name, prepared, sides)
    output_base = digital_dir(job_dir) / "page"
    console.print(f"[cyan]Job created: {job_dir}[/cyan]\n")
    show_encoding_plan(input_file, output_base.parent, config, file_size, len(prepared.payload))
    if password:
        console.print("[bold yellow]User passphrase in use[/bold yellow]")
    console.print()
    progress, task = make_page_progress("Rendering pages")
    with progress:
        paths = encode(
            input_file, output_base, config,
            on_page_complete=make_page_callback(progress, task),
            passphrase=password,
            prepared=prepared,
        )
    for path in paths:
        print_success(f"Saved {path}")
    console.print(f"\n[bold]Job directory: {job_dir}[/bold]")
