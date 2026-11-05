from common.format_spec import FLAG_DUPLEX, FLAG_USER_PASSPHRASE
from common.qr_scale import flags_with_qr_mm
from common.tag_scale import flags_with_tag_mm, tag_mm_from_flags
from web.scan_guide import FLIP, NEXT_SHEET, scan_step


def test_duplex_flag_survives_the_scale_bits() -> None:
    flags = flags_with_qr_mm(flags_with_tag_mm(FLAG_USER_PASSPHRASE | FLAG_DUPLEX, 4.0), 0.22)
    assert flags & FLAG_DUPLEX
    assert flags & FLAG_USER_PASSPHRASE
    assert tag_mm_from_flags(flags) == 4.0


def test_first_side_of_a_duplex_sheet_asks_for_a_flip() -> None:
    wizard = {"duplex": True, "total_pages": 4, "data_pages": 3}
    scans = [{"name": "scan_001.png", "kept": True, "page_index": 0, "status": "identified"}]
    guide = scan_step(wizard, scans)
    assert guide["action"] == "flip"
    assert guide["page"] == 1
    assert guide["text"] == FLIP


def test_a_finished_sheet_asks_for_either_side_of_the_next_one() -> None:
    wizard = {"duplex": True, "total_pages": 4}
    scans = [
        {"name": "a.png", "kept": True, "page_index": 2, "status": "identified"},
        {"name": "b.png", "kept": True, "page_index": 3, "status": "identified"},
    ]
    guide = scan_step(wizard, scans)
    assert guide["action"] == "next"
    assert guide["side"] == "either"
    assert guide["sheet"] == 1
    assert guide["text"] == NEXT_SHEET


def test_scanning_the_back_first_asks_to_flip_to_the_front() -> None:
    wizard = {"duplex": True, "total_pages": 2}
    scans = [{"name": "back.png", "kept": True, "page_index": 1, "status": "identified"}]
    guide = scan_step(wizard, scans)
    assert guide["action"] == "flip"
    assert guide["page"] == 0
    assert guide["side"] == "front"
