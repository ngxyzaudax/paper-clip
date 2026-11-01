import numpy as np
from PIL import Image

import calibration.sheet_io as sheet_io
from calibration.scan_record import ScanRecord, record_path, scan_record
from calibration.sheet_draw import draw_side
from calibration.sheet_place import sheet_side
from calibration.sheet_score import PatchRead
from calibration.sheet_session import archive_session, next_scan_path
from calibration.session_plan import coverage, next_instruction, view_label


def test_scan_record_finds_side_and_rotation_and_caches(tmp_path) -> None:
    image = np.rot90(np.asarray(draw_side(sheet_side("back"))), 2)
    scan = tmp_path / "scan-01.png"
    Image.fromarray(np.ascontiguousarray(image)).save(scan, compress_level=1)
    record = scan_record(scan)
    assert (record.side, record.rotation, len(record.reads)) == ("back", 180, 25)
    assert all(read.decoded for read in record.reads if read.kind == "qr")
    assert all(
        read.accuracy >= 0.99 and not read.slipped and read.tags_found == read.tags_expected
        for read in record.reads if read.kind != "qr"
    )
    assert record_path(scan).exists()
    assert scan_record(scan) == record


def test_instructions_walk_both_sides_in_either_orientation() -> None:
    read = (_read(),)
    assert next_instruction(()).startswith("Place the FRONT")
    front = (ScanRecord("scan-01.png", "front", 180, read),)
    assert next_instruction(front).startswith("Place the BACK")
    lost = front + (ScanRecord("scan-02.png", "", 0, ()),)
    assert "frame was not found" in next_instruction(lost)
    done = front + (ScanRecord("scan-02.png", "back", 0, read),)
    assert coverage(done).complete
    assert next_instruction(done).startswith("Both sides")
    assert view_label(lost[-1]) == "scan-02.png: frame not found"
    assert view_label(done[-1]) == "scan-02.png: back, upright, 1 patches"


def test_session_numbering_and_archive(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sheet_io, "calibration_dir", lambda: tmp_path)
    monkeypatch.setattr("calibration.sheet_session.calibration_dir", lambda: tmp_path)
    monkeypatch.setattr("calibration.sheet_session.session_dir", lambda: tmp_path / "session")
    first = next_scan_path()
    assert first.name == "scan-01.png"
    first.write_bytes(b"x")
    assert next_scan_path().name == "scan-02.png"
    moved = archive_session()
    assert moved is not None and (moved / "scan-01.png").exists()
    assert not (tmp_path / "session").exists()
    assert archive_session() is None


def _read() -> PatchRead:
    return PatchRead("dot", "dot", 0.0, 8.0, 16.0, 22, 0.62, 5, False, 4, 4, 0.0, False, 1.0)
