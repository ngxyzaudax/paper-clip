import json
from pathlib import Path

import cv2
import numpy as np

from calibration.sheet_pass import patch_passed
from calibration.sheet_score import PatchRead
from common.config import resolve_config
from common.data_store import create_print_job, record_print
from common.page_layout import page_image_size
from health.check import run_check
from scan_sim.render import render_arrays
from serialization.decode.identify import identify_scan
from serialization.decode.readiness import document_readiness
from serialization.encode.encoder import prepare_payload
from serialization.encode.fit_ecc import fill_config
from serialization.encode.page_preview import layout_page, payload_page
from serialization.encode.pipeline import encode, render_pages


def _config():
    return resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10)


def test_payload_page_matches_the_full_render(tmp_path: Path) -> None:
    config = _config()
    raw = b"preview-bytes-for-one-page"
    source = tmp_path / "note.txt"
    source.write_bytes(raw)
    config = fill_config(raw, config, source.name)
    prepared = prepare_payload(raw, config, source.name)
    images = render_pages(source, config, prepared=prepared)
    page = payload_page(prepared, config, 0)
    assert np.array_equal(np.asarray(page), np.asarray(images[0]))


def test_layout_page_uses_the_page_size() -> None:
    config = _config()
    image = layout_page(config)
    assert image.size == page_image_size(config)


def test_encode_writes_each_page_before_the_next(tmp_path: Path) -> None:
    config = _config()
    raw = b"stream-me"
    source = tmp_path / "stream.txt"
    source.write_bytes(raw)
    seen: list[int] = []

    def on_image(index: int, _total: int, _image: object) -> None:
        seen.append(index)

    paths = encode(source, tmp_path / "digital" / "page", config, on_page_image=on_image)
    assert seen == list(range(len(paths)))
    assert all(path.is_file() for path in paths)


def test_identify_reads_a_page_rotated_180() -> None:
    config = _config()
    page = render_arrays(b"secret-page", config, "secret.bin", passphrase="hunter2")[0]
    found = identify_scan(cv2.rotate(page, cv2.ROTATE_180))
    assert found is not None
    assert found.page_index == 0
    assert found.rotation == 180
    assert found.passphrase_required is True
    assert found.sha256


def test_readiness_counts_parity_pages() -> None:
    assert document_readiness(2, 2, {0}).state == "missing"
    assert document_readiness(2, 3, {0, 1}).state == "ready"
    assert document_readiness(2, 3, {0, 2}).state == "parity"
    assert document_readiness(2, 3, {0}).state == "missing"


def test_print_job_records_sha256_and_prints(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("common.data_store.PRINT_JOBS_DIR", tmp_path)
    job = create_print_job(
        "notes.txt", "inline", {}, 1,
        paper_size="A4", data_pages=1, payload_bytes=4,
        data_capacity_bytes_per_page=10, original_sha256="abc",
    )
    record_print(job, "ipp://printer", True, [7])
    meta = json.loads((job / "job.json").read_text())
    assert meta["original_sha256"] == "abc"
    assert meta["prints"][0]["duplex"] is True
    assert meta["prints"][0]["ipp_job_ids"] == [7]


def test_patch_passed_follows_kind() -> None:
    qr = PatchRead("qr", "q", 0.25, 0, 0, 0, 0, 0, True, 0, 0, 0, False, 1)
    assert patch_passed(qr) is True
    assert patch_passed(qr._replace(decoded=False)) is False
    tag = PatchRead("tag", "t", 0, 8, 16, 0, 0.62, 5, False, 6, 6, 0.1, False, 1)
    assert patch_passed(tag) is True
    assert patch_passed(tag._replace(accuracy=0.5)) is False


def test_damage_panels_are_written_beside_the_sheet() -> None:
    page = render_arrays(b"health-preview", _config(), "health.bin")[0]
    check = run_check([page], use_model=False, track=False)
    assert check.reading.damage_pages
    panel = Path(check.reading.damage_pages[0])
    assert panel.is_file()
    assert panel.parent == Path(check.reading.damage_image).with_suffix("")
