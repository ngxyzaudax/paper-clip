from typing import NamedTuple

from calibration.scan_record import ScanRecord

SIDES = ("front", "back")
VIEWS_PER_SIDE = 1


class Coverage(NamedTuple):
    front: tuple[int, ...]
    back: tuple[int, ...]
    unread: int

    @property
    def views(self) -> int:
        return min(len(self.front), VIEWS_PER_SIDE) + min(len(self.back), VIEWS_PER_SIDE)

    @property
    def complete(self) -> bool:
        return self.views == VIEWS_PER_SIDE * len(SIDES)


def coverage(records: tuple[ScanRecord, ...]) -> Coverage:
    front = sorted({record.rotation for record in records if record.side == "front" and record.reads})
    back = sorted({record.rotation for record in records if record.side == "back" and record.reads})
    unread = sum(1 for record in records if not record.reads)
    return Coverage(tuple(front), tuple(back), unread)


def next_instruction(records: tuple[ScanRecord, ...]) -> str:
    if records and not records[-1].reads:
        return (
            "The frame was not found on the last scan. Lay the sheet flat, fully inside the glass, "
            "printed side down, and scan again."
        )
    seen = coverage(records)
    for side, rotations in (("front", seen.front), ("back", seen.back)):
        if not rotations:
            return f"Place the {side.upper()} face down on the glass and scan."
    return "Both sides are in. Save the profile, or scan either side again."


def view_label(record: ScanRecord) -> str:
    if not record.reads:
        return f"{record.name}: frame not found"
    turned = "upright" if record.rotation == 0 else f"turned {record.rotation} degrees"
    return f"{record.name}: {record.side}, {turned}, {len(record.reads)} patches"
