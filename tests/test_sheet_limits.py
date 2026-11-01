from calibration.sheet_limits import choose_profile
from calibration.sheet_score import PatchRead
from calibration.sheet_spec import CELL_PITCHES, DOT_RATIOS, QR_MODULES, SYMBOL_COUNTS, TAG_PITCHES, TAG_SIZES


def test_margin_steps_back_from_the_tightest_size_that_passed() -> None:
    reads = _passing()
    reads.append(_read(kind="qr", name="qr-0.20", qr_mm=0.20, decoded=False, accuracy=0.0))
    reads.append(_read(kind="tag", name="tag-2.5", tag_mm=2.5, tags_found=1, residual=2.0, slipped=True, accuracy=0.2))
    chosen = choose_profile(tuple(read for read in reads if not _replaced(read)))
    assert chosen.qr_module_mm == 0.25
    assert chosen.tag_size_mm == 3.5
    assert chosen.tag_pitch_mm == 24.0
    assert chosen.cell_size_px == 18
    assert chosen.dot_ratio == 0.62
    assert chosen.num_symbols == 11
    assert chosen.bytes_per_side > 0


def test_one_failed_read_drops_that_size() -> None:
    reads = [read for read in _passing() if not (read.kind == "dot" and read.cell_px == 17)]
    for ratio in DOT_RATIOS:
        reads.append(_read(
            kind="dot", name=f"dot-17-{ratio:g}", cell_px=17, dot_ratio=ratio, accuracy=0.4, slipped=True,
        ))
    chosen = choose_profile(tuple(reads))
    assert chosen.cell_size_px == 20


def test_passing_dense_cells_save_14_px_and_leave_pitch_at_24() -> None:
    reads = _passing()
    reads.append(_read(kind="qr", name="qr-0.18", qr_mm=0.18, decoded=True, accuracy=1.0))
    reads.append(_read(kind="tag", name="tag-2", tag_mm=2.0, pitch_mm=16))
    reads.append(_read(kind="pitch", name="pitch-12", pitch_mm=12.0, tag_mm=6.0, cell_px=16))
    for cell in (16, 15, 14, 13):
        for ratio in DOT_RATIOS:
            reads.append(_read(kind="dot", name=f"dot-{cell}-{ratio:g}", cell_px=cell, dot_ratio=ratio, pitch_mm=16))
    chosen = choose_profile(tuple(reads))
    assert chosen.qr_module_mm == 0.20
    assert chosen.tag_size_mm == 2.5
    assert chosen.tag_pitch_mm == 24.0
    assert chosen.cell_size_px == 14


def test_a_pass_below_a_failure_does_not_count() -> None:
    reads = [read for read in _passing() if not (read.kind == "tag" and read.tag_mm == 6.0)]
    reads.append(_read(kind="tag", name="tag-6", tag_mm=6.0, tags_found=6, tags_expected=6, residual=0.9))
    assert choose_profile(tuple(reads)).tag_size_mm == 8.0


def _replaced(read: PatchRead) -> bool:
    return (read.kind == "qr" and read.qr_mm == 0.20 and read.decoded) or (
        read.kind == "tag" and read.tag_mm == 2.5 and read.accuracy == 1.0
    )


def _passing() -> list[PatchRead]:
    reads = [_read(kind="qr", name=f"qr-{mm:.2f}", qr_mm=mm, decoded=True, accuracy=1.0) for mm in QR_MODULES]
    reads += [_read(kind="tag", name=f"tag-{mm:g}", tag_mm=mm, pitch_mm=16) for mm in TAG_SIZES]
    reads += [_read(kind="pitch", name=f"pitch-{mm:g}", pitch_mm=mm, tag_mm=8) for mm in TAG_PITCHES]
    reads += [
        _read(kind="dot", name=f"dot-{cell}-{ratio:g}", cell_px=cell, dot_ratio=ratio, pitch_mm=16)
        for cell in CELL_PITCHES for ratio in DOT_RATIOS
    ]
    reads += [
        _read(kind="symbol", name=f"sym-{cell}-{count}", cell_px=cell, symbols=count, dot_ratio=0.62)
        for cell in (22, 20, 18) for count in SYMBOL_COUNTS
    ]
    return reads


def _read(**overrides: object) -> PatchRead:
    values = dict(
        kind="dot", name="dot", qr_mm=0.0, tag_mm=8.0, pitch_mm=16.0, cell_px=22, dot_ratio=0.62,
        symbols=5, decoded=False, tags_found=4, tags_expected=4, residual=0.0, slipped=False, accuracy=1.0,
    )
    values.update(overrides)
    return PatchRead(**values)
