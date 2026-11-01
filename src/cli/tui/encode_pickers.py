from __future__ import annotations

from cli.tui.encode_pick_fields import PICK_BY_ID
from cli.tui.option_picker_screen import OptionPickerScreen


def encode_option_picker(button_id: str | None) -> OptionPickerScreen | None:
    field = PICK_BY_ID.get(button_id or "")
    if field is None:
        return None
    return OptionPickerScreen(field.title, field.options())
