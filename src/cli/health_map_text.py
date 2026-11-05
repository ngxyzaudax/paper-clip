from health.report import HealthReport

LEVELS = (
    (0.02, "grey35", "··"),
    (0.05, "green", "░░"),
    (0.12, "yellow", "▒▒"),
    (0.30, "dark_orange", "▓▓"),
    (float("inf"), "red", "██"),
)
PAGE_GAP = "    "


def zone_cell(share: float) -> str:
    style, glyph = next((style, glyph) for limit, style, glyph in LEVELS if share < limit)
    return f"[{style}]{glyph}[/]"


def map_lines(report: HealthReport) -> list[str]:
    """Each data page as a coarse grid of zones shaded by the share of misread cells, pages side by side."""
    pages = list(report.pages)
    if not pages:
        return []
    width = 2 * len(pages[0].damage_map[0])
    titles = PAGE_GAP.join(f"{'Page ' + str(page.index + 1):<{width}}" for page in pages)
    rows = zip(*(page.damage_map for page in pages))
    return [f"[bold]{titles}[/]", *(PAGE_GAP.join(_row(row) for row in group) for group in rows), _legend()]


def _row(row: tuple[float, ...]) -> str:
    return "".join(zone_cell(share) for share in row)


def _legend() -> str:
    labels = ("<2%", "<5%", "<12%", "<30%", "more")
    return "[dim]misread cells per zone:[/] " + "  ".join(
        f"[{style}]{glyph}[/] {label}" for (_limit, style, glyph), label in zip(LEVELS, labels)
    )
