from textual.widget import Widget
from textual.widgets import Button, Static

from cli.tui.encode_pick_fields import PICK_BY_ID, PICK_FIELDS
from cli.tui.encoding_form import EncodingFormPicks, profile_source_text


def apply_encode_pick(picks: EncodingFormPicks, button_id: str, result: object) -> bool:
    field = PICK_BY_ID.get(button_id)
    if field is None:
        return False
    setattr(picks, field.attribute, field.cast(result))
    return True


def refresh_encode_pick_labels(screen: Widget, picks: EncodingFormPicks) -> None:
    for field in PICK_FIELDS:
        screen.query_one(f"#{field.button_id}", Button).label = field.describe(getattr(picks, field.attribute))
    screen.query_one("#enc-profile-source", Static).update(profile_source_text(picks))
