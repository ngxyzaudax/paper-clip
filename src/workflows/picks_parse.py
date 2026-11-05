from dataclasses import asdict, fields

from workflows.encode_picks import PICK_FIELDS, PickValue
from workflows.encoding_form import EncodingFormPicks, default_encoding_form_picks

TRUE_WORDS = ("1", "true", "yes", "on")
FALSE_WORDS = ("0", "false", "no", "off")


def picks_from_dict(data: dict[str, PickValue | None]) -> EncodingFormPicks:
    """Merge client picks over the defaults, casting each value and refusing values outside the catalog."""
    base = asdict(default_encoding_form_picks())
    known = {field.name for field in fields(EncodingFormPicks)}
    given = {key: _checked(key, _cast(base[key], value), base[key]) for key, value in data.items() if key in known and value is not None}
    return EncodingFormPicks(**{**base, **given})


def picks_record(picks: EncodingFormPicks) -> dict[str, PickValue]:
    """Return the picks as a plain JSON-ready mapping."""
    return asdict(picks)


def _cast(current: PickValue, value: PickValue) -> PickValue:
    if isinstance(current, bool):
        return _as_bool(value)
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"Expected a {type(current).__name__}, got {type(value).__name__}")
    return value if isinstance(value, type(current)) else type(current)(value)


def _as_bool(value: PickValue) -> bool:
    word = str(value).lower()
    if value is True or word in TRUE_WORDS:
        return True
    if value is False or word in FALSE_WORDS:
        return False
    raise ValueError(f"Expected true or false, got {value!r}")


def _checked(key: str, value: PickValue, default: PickValue) -> PickValue:
    allowed = _allowed(key)
    if allowed is None or value == default or value in allowed:
        return value
    raise ValueError(f"Unsupported value for {key}: {value!r}")


def _allowed(key: str) -> tuple[PickValue, ...] | None:
    field = next((item for item in PICK_FIELDS if item.key == key), None)
    return tuple(value for _label, value in field.options()) if field else None
