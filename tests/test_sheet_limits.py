from calibration.sheet_limits import choose_profile
from calibration.sheet_score import PatchRead
from calibration.sheet_spec import CELL_PITCHES, DOT_RATIOS, QR_MODULES, SYMBOL_COUNTS, TAG_SIZES


def test_margin_steps_back_from_the_tightest_size_that_passed() -> None:
    reads = [read for read in _passing() if not (read.kind == "qr" and read.qr_mm == 0.20 and read.decoded)]
    reads.append(_read(kind="qr", name="qr-0.20", qr_mm=0.20, decoded=False, accuracy=0.0))
    chosen = choose_profile(tuple(reads))
    assert chosen.qr_module_mm == 0.25
    assert chosen.tag_size_mm == 6.0
    assert chosen.tag_pitch_mm == 16.0
    assert chosen.cell_size_px == 13
    assert chosen.dot_ratio == 0.62
    assert chosen.num_symbols == 11
    assert chosen.bytes_per_side > 0


def test_one_failed_read_drops_that_size() -> None:
    reads = [read for read in _passing() if not (read.kind == "dot" and read.cell_px == 13)]
    for ratio in DOT_RATIOS:
        reads.append(_read(
            kind="dot", name=f"dot-13-{ratio:g}", cell_px=13, dot_ratio=ratio, accuracy=0.4, slipped=True,
        ))
    chosen = choose_profile(tuple(reads))
    assert chosen.cell_size_px == 14


def test_cells_below_the_millimetre_floor_stay_out_of_the_profile() -> None:
    reads = _passing()
    for cell in (12, 11, 10, 9, 8):
        for ratio in DOT_RATIOS:
            reads.append(_read(kind="dot", name=f"dot-{cell}-{ratio:g}", cell_px=cell, dot_ratio=ratio, pitch_mm=16))
        for count in SYMBOL_COUNTS:
            reads.append(_read(kind="symbol", name=f"sym-{cell}-{count}", cell_px=cell, symbols=count, dot_ratio=0.62))
    chosen = choose_profile(tuple(reads))
    assert chosen.qr_module_mm == 0.22
    assert chosen.tag_size_mm == 6.0
    assert chosen.tag_pitch_mm == 16.0
    assert chosen.cell_size_px == 10
    assert chosen.num_symbols == 11


def test_symbol_accuracy_drop_keeps_the_cell_with_the_larger_sizes() -> None:
    reads = _passing()
    for cell in (12, 11, 10):
        for ratio in DOT_RATIOS:
            reads.append(_read(kind="dot", name=f"dot-{cell}-{ratio:g}", cell_px=cell, dot_ratio=ratio))
        reads.append(_read(
            kind="symbol", name=f"sym-{cell}-11", cell_px=cell, symbols=11, dot_ratio=0.62, accuracy=0.991,
        ))
    chosen = choose_profile(tuple(reads))
    assert chosen.cell_size_px == 13
    assert chosen.num_symbols == 11


def test_a_pass_below_a_failure_does_not_count() -> None:
    reads = [read for read in _passing() if not (read.kind == "tag" and read.tag_mm == 6.0)]
    reads.append(_read(kind="tag", name="tag-6", tag_mm=6.0, tags_found=6, tags_expected=6, residual=0.9))
    assert choose_profile(tuple(reads)).tag_size_mm == 8.0


def _passing() -> list[PatchRead]:
    reads = [_read(kind="qr", name=f"qr-{mm:.2f}", qr_mm=mm, decoded=True, accuracy=1.0) for mm in QR_MODULES]
    reads += [_read(kind="tag", name=f"tag-{mm:g}", tag_mm=mm, pitch_mm=16) for mm in TAG_SIZES]
    reads += [
        _read(kind="dot", name=f"dot-{cell}-{ratio:g}", cell_px=cell, dot_ratio=ratio, pitch_mm=16)
        for cell in CELL_PITCHES for ratio in DOT_RATIOS
    ]
    reads += [
        _read(kind="symbol", name=f"sym-{cell}-{count}", cell_px=cell, symbols=count, dot_ratio=0.62)
        for cell in CELL_PITCHES for count in SYMBOL_COUNTS
    ]
    return reads


def _read(**overrides: object) -> PatchRead:
    values = dict(
        kind="dot", name="dot", qr_mm=0.0, tag_mm=8.0, pitch_mm=16.0, cell_px=22, dot_ratio=0.62,
        symbols=5, decoded=False, tags_found=4, tags_expected=4, residual=0.0, slipped=False, accuracy=1.0,
    )
    values.update(overrides)
    return PatchRead(**values)
