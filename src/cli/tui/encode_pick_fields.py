from collections.abc import Callable
from typing import Any, NamedTuple

from common.cell_size_picks import cell_size_pick_label, cell_size_pick_options
from common.color_picker import symbol_alphabet_options, symbol_option_label
from common.paper_sizes import paper_size_option_label, paper_size_options
from common.parity_pages_picks import parity_pages_option_label, parity_pages_pick_options
from common.print_dpi_presets import print_dpi_option_label, print_dpi_select_options
from common.rs_redundancy_picks import rs_redundancy_option_label, rs_redundancy_pick_options
from common.scale_picks import (
    dot_ratio_label,
    dot_ratio_options,
    millimetre_label,
    qr_module_label,
    qr_module_options,
    tag_pitch_options,
    tag_size_options,
)


class PickField(NamedTuple):
    button_id: str
    label: str
    title: str
    attribute: str
    cast: Callable[[Any], Any]
    options: Callable[[], list[tuple[str, Any]]]
    describe: Callable[[Any], str]


PICK_FIELDS: tuple[PickField, ...] = (
    PickField("enc-symbols-pick", "Symbols", "Symbol alphabet", "symbol_count", int,
              symbol_alphabet_options, symbol_option_label),
    PickField("enc-cell-pick", "Cell px", "Cell size (px)", "cell_size_px", int,
              cell_size_pick_options, cell_size_pick_label),
    PickField("enc-tag-pick", "AprilTag", "AprilTag size", "tag_size_mm", float,
              tag_size_options, millimetre_label),
    PickField("enc-pitch-pick", "Tag pitch", "AprilTag pitch", "tag_pitch_mm", float,
              tag_pitch_options, millimetre_label),
    PickField("enc-qr-pick", "QR module", "QR module", "qr_module_mm", float,
              qr_module_options, qr_module_label),
    PickField("enc-dot-pick", "Dot ratio", "Dot ratio", "dot_ratio", float,
              dot_ratio_options, dot_ratio_label),
    PickField("enc-dpi-pick", "Print DPI", "Print DPI", "print_dpi", int,
              print_dpi_select_options, print_dpi_option_label),
    PickField("enc-rs-pick", "RS redundancy", "RS redundancy", "rs_redundancy", float,
              rs_redundancy_pick_options, rs_redundancy_option_label),
    PickField("enc-parity-pick", "Parity pages", "Parity pages", "redundancy_pages", int,
              parity_pages_pick_options, parity_pages_option_label),
    PickField("enc-paper-pick", "Paper size", "Paper size", "paper_size", str,
              paper_size_options, paper_size_option_label),
)

PICK_BY_ID: dict[str, PickField] = {field.button_id: field for field in PICK_FIELDS}


def field_rows(size: int = 2) -> list[tuple[PickField, ...]]:
    return [PICK_FIELDS[start:start + size] for start in range(0, len(PICK_FIELDS), size)]
