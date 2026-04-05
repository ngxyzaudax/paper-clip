from __future__ import annotations

from collections.abc import Callable
from typing import Any

from cli.tui.option_picker_screen import OptionPickerScreen
from common.cell_size_picks import cell_size_pick_options
from common.color_picker import symbol_alphabet_options
from common.dot_print_picks import dot_gain_pick_options, dot_guard_pick_options
from common.paper_sizes import paper_size_options
from common.print_dpi_presets import print_dpi_select_options

_OptionListFn = Callable[[], list[tuple[str, Any]]]

_ENCODE_PICKERS: dict[str, tuple[str, _OptionListFn]] = {
    "enc-cell-pick": ("Cell size (px)", cell_size_pick_options),
    "enc-symbols-pick": ("Symbol alphabet", symbol_alphabet_options),
    "enc-dpi-pick": ("Print DPI", print_dpi_select_options),
    "enc-paper-pick": ("Paper size", paper_size_options),
    "enc-dot-gain-pick": ("Dot gain", dot_gain_pick_options),
    "enc-dot-guard-pick": ("Dot guard (px)", dot_guard_pick_options),
}


def encode_option_picker(button_id: str | None) -> OptionPickerScreen | None:
    if not button_id:
        return None
    spec = _ENCODE_PICKERS.get(button_id)
    if spec is None:
        return None
    title, options_fn = spec
    return OptionPickerScreen(title, options_fn())
