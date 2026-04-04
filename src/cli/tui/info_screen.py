from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Label, Select, Static

from common.config import PaperClipConfig
from common.config_store import list_profiles, load_profile
from common.page_layout import data_capacity_bytes, grid_dimensions, page_image_size, usable_area_px
from common.palette import palette_from_config
from common.paper_sizes import DEFAULT_PAPER_SIZE, paper_size_dimensions, paper_size_options
from common.symbols import bits_per_cell, symbol_count


class InfoScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._config: PaperClipConfig | None = None
        self._paper_size: str = DEFAULT_PAPER_SIZE

    def compose(self) -> ComposeResult:
        profiles = list_profiles()
        options = [(name, name) for name, _ in profiles]
        with VerticalScroll(classes="form-container"):
            yield Static("Configuration Info", classes="screen-title")
            with Vertical(classes="section"):
                yield Static("Select Profile", classes="section-title")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Profile")
                        yield Select(options, prompt="Select profile", id="config-select")
                    with Vertical(classes="form-col"):
                        yield Label("Paper Size")
                        yield Select(paper_size_options(), value=DEFAULT_PAPER_SIZE, id="paper-select")
            yield Static("", id="info-display", classes="details-panel")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        if event.select.id == "config-select":
            try:
                self._config = load_profile(str(event.value))
                self._refresh_display()
            except Exception as e:
                self._config = None
                self.query_one("#info-display", Static).update(f"[red]{e}[/red]")
        elif event.select.id == "paper-select":
            self._paper_size = str(event.value)
            self._refresh_display()

    def _refresh_display(self) -> None:
        if not self._config:
            return
        from dataclasses import replace
        try:
            w, h = paper_size_dimensions(self._paper_size)
            config = replace(self._config, page_width_mm=w, page_height_mm=h)
        except ValueError:
            config = self._config
        self._display_info(config)

    def _display_info(self, c: PaperClipConfig) -> None:
        cols, rows = grid_dimensions(c)
        pw, ph = page_image_size(c)
        uw, uh = usable_area_px(c)
        bpc = bits_per_cell(c.num_colors)
        sc = symbol_count(c.num_colors)
        capacity = data_capacity_bytes(c)
        palette = palette_from_config(c)
        palette_text = "  ".join(
            f"[on rgb({r},{g},{b})]    [/on rgb({r},{g},{b})]"
            for r, g, b in palette
        )
        self.query_one("#info-display", Static).update(
            f"[bold cyan]Encoding Parameters[/bold cyan]\n"
            f"  Colors: {c.num_colors}    Cell: {c.cell_size_px}px\n"
            f"  Symbols: {sc}    Bits/cell: {bpc:.2f}    RS redundancy: {c.rs_redundancy:.0%}\n\n"
            f"[bold cyan]Hardware[/bold cyan]\n"
            f"  Scan DPI: {c.scan_dpi}    Margin: {c.margin_mm}mm\n"
            f"  Paper: {self._paper_size} ({c.page_width_mm}x{c.page_height_mm}mm, {pw}x{ph}px)\n"
            f"  Usable area: {uw}x{uh}px\n\n"
            f"[bold cyan]Capacity[/bold cyan]\n"
            f"  Grid: {cols}x{rows} = {cols * rows:,} cells\n"
            f"  Capacity/page: [bold]{capacity:,}[/bold] bytes ({capacity / 1024:.1f} KB)\n\n"
            f"[bold cyan]Color Palette[/bold cyan]\n"
            f"  {palette_text}"
        )
