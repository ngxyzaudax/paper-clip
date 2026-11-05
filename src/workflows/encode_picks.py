from collections.abc import Callable
from typing import Literal, NamedTuple

from common.cell_size_picks import cell_size_pick_options
from common.color_picker import symbol_alphabet_options
from common.ecc_sym_picks import ecc_sym_pick_options
from common.paper_sizes import paper_size_options
from common.parity_pages_picks import parity_pages_pick_options
from common.print_dpi_presets import print_dpi_select_options
from common.scale_picks import dot_ratio_options, qr_module_options, tag_pitch_options, tag_size_options

Level = Literal["simple", "advanced", "expert"]
Kind = Literal["select", "switch"]
PickValue = str | int | float | bool
SHEET_TARGETS = tuple(range(1, 11))


class PickField(NamedTuple):
    key: str
    label: str
    options: Callable[[], list[tuple[str, PickValue]]]
    level: Level = "expert"
    kind: Kind = "select"
    hint: str = ""


def sides_options() -> list[tuple[str, int]]:
    return [("One side", 1), ("Both sides", 2)]


def fill_options() -> list[tuple[str, bool]]:
    return [("Fill", True), ("Only what the file needs", False)]


def priority_options() -> list[tuple[str, str]]:
    return [("Error correction", "protection"), ("Balanced", "balanced"), ("Larger dots", "dots")]


def sheet_target_options() -> list[tuple[str, int]]:
    return [("Fewest that fit", 0), *((f"{count} sheet{'s' if count > 1 else ''}", count) for count in SHEET_TARGETS)]


PICK_FIELDS: tuple[PickField, ...] = (
    PickField("paper_size", "Paper size", paper_size_options, "simple"),
    PickField("sides", "Print on", sides_options, "simple",
              hint="Both sides need a printer that can print the back. The front and back are the same sheet."),
    PickField("fill_sheets", "Fill the sheets with extra protection", fill_options, "simple", "switch",
              "A small file still fills the sheet. Spare paper becomes pages you can lose, and leftover room makes the dots survive more damage. The back is used only when Print on is Both sides."),
    PickField("print_dpi", "Printer sharpness", print_dpi_select_options, "advanced",
              hint="A higher number draws smaller dots and fits more on the page."),
    PickField("redundancy_pages", "Spare pages", parity_pages_pick_options, "advanced",
              hint="Each spare page can rebuild one lost or unreadable page."),
    PickField("ecc_sym", "Repair bytes", ecc_sym_pick_options, "advanced",
              hint="How much of each patch of dots can be ruined and still read. Empty room on the page raises this on its own."),
    PickField("sheets", "Sheets to fill", sheet_target_options, "expert",
              hint="Spread protection over more sheets than the file needs. Turn on Fill the sheets to use this."),
    PickField("fill_priority", "Spend spare room on", priority_options, "expert",
              hint="Stain and tear survival uses the spare room as repair data. Larger dots survive fading, blur, and ink bleed. Balanced splits the room between the two."),
    PickField("symbol_count", "Colours", symbol_alphabet_options),
    PickField("cell_size_px", "Dot size", cell_size_pick_options, hint="Larger dots are easier to photograph and hold less of the file."),
    PickField("tag_size_mm", "Finder marks", tag_size_options, hint="The camera uses these squares to straighten the page."),
    PickField("tag_pitch_mm", "Distance between finder marks", tag_pitch_options),
    PickField("qr_module_mm", "Page-code square size", qr_module_options, hint="Size of the tiny squares in the code on the page."),
    PickField("dot_ratio", "Dot fill", dot_ratio_options, hint="Share of each square that is ink. The rest stays white so neighbouring dots do not run together."),
)


def option_catalog() -> list[dict[str, object]]:
    return [_field_json(field) for field in PICK_FIELDS]


def _field_json(field: PickField) -> dict[str, object]:
    return {
        "key": field.key,
        "label": field.label,
        "level": field.level,
        "kind": field.kind,
        "hint": field.hint,
        "options": [{"label": label, "value": value} for label, value in field.options()],
    }
