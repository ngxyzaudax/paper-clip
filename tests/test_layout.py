import pytest

from common.config import PaperClipConfig, default_config, resolve_config, validate_config
from common.format_spec import MIN_MARGIN_MM, PRINTER_MIN_MARGIN_MM
from common.geometry import page_geometry
from common.geometry_measure import mm_to_px
from common.geometry_shift import tag_box
from common.geometry_tags import tag_quiet_px
from common.page_layout import valid_cells_ordered

A6_SWEEP = {"paper_size": "A6", "print_dpi": 360, "cell_size_px": 18, "margin_mm": 10, "num_symbols": 5}


def _configs():
    return [default_config(), resolve_config(**A6_SWEEP), resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18)]


def _tag_air(config: PaperClipConfig) -> int:
    geometry = page_geometry(config)
    quiet = tag_quiet_px(config.print_dpi, config.tag_size_mm)
    block_gaps = (
        _separation(
            (slot.block.x, slot.block.y, slot.block.width, slot.block.height),
            tag_box(tag, quiet),
        )
        for slot in geometry.slots
        for tag in geometry.tags
    )
    return min(block_gaps)


def _separation(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    dx = max(b[0] - (a[0] + a[2]), a[0] - (b[0] + b[2]), 0)
    dy = max(b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3]), 0)
    if dx and dy:
        return int((dx * dx + dy * dy) ** 0.5)
    return dx + dy


def _overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return not (a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])


_ANCHORS = ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75))


@pytest.mark.parametrize("config", _configs())
def test_header_copies_keep_their_quadrant(config) -> None:
    geometry = page_geometry(config)
    assert len(geometry.slots) == 4
    for slot, (fx, fy) in zip(geometry.slots, _ANCHORS):
        centre_x = slot.block.x + slot.block.width / 2
        centre_y = slot.block.y + slot.block.height / 2
        assert (centre_x < geometry.usable_w / 2) == (fx < 0.5)
        assert (centre_y < geometry.usable_h / 2) == (fy < 0.5)


@pytest.mark.parametrize(
    "config",
    [
        default_config(),
        resolve_config(
            cell_size_px=13,
            num_symbols=11,
            tag_size_mm=6,
            tag_pitch_mm=24,
            print_dpi=720,
            qr_module_mm=0.22,
            dot_ratio=0.62,
        ),
    ],
)
def test_qr_sits_in_the_gap_between_tags(config) -> None:
    assert _tag_air(config) >= mm_to_px(10, config.print_dpi)


@pytest.mark.parametrize("config", _configs())
def test_calibration_strip_sits_under_each_qr(config) -> None:
    geometry = page_geometry(config)
    for slot in geometry.slots:
        qr, strip, block = slot.qr, slot.calibration, slot.block
        assert strip.y >= qr.y + qr.height
        assert strip.y - (qr.y + qr.height) < geometry.cell
        assert block.x <= strip.x and strip.x + strip.width <= block.x + block.width
        assert strip.y + strip.height + geometry.cell == block.y + block.height


@pytest.mark.parametrize("config", _configs())
def test_no_tag_or_data_cell_touches_a_header_block(config) -> None:
    geometry = page_geometry(config)
    quiet = tag_quiet_px(config.print_dpi, config.tag_size_mm)
    cell = geometry.cell
    for slot in geometry.slots:
        block = (slot.block.x, slot.block.y, slot.block.width, slot.block.height)
        for tag in geometry.tags:
            assert not _overlap((tag.x - quiet, tag.y - quiet, tag.size + 2 * quiet, tag.size + 2 * quiet), block)
        for row, col in valid_cells_ordered(config):
            assert not _overlap((col * cell, row * cell, cell, cell), block)


@pytest.mark.parametrize("config", _configs())
def test_tag_ids_follow_the_full_mesh(config) -> None:
    geometry = page_geometry(config)
    for tag in geometry.tags:
        assert tag.tag_id == tag.row * geometry.tag_cols + tag.col
    assert {tag.tag_id for tag in geometry.tags} == set(range(geometry.tag_rows * geometry.tag_cols))


def test_data_fills_every_row_around_the_qr() -> None:
    config = default_config()
    geometry = page_geometry(config)
    per_row = [0] * geometry.rows
    for row, _ in valid_cells_ordered(config):
        per_row[row] += 1
    assert min(per_row) >= geometry.cols // 2
    quiet = tag_quiet_px(config.print_dpi, config.tag_size_mm)
    tag_box_cells = -(-(geometry.tags[0].size + 2 * quiet) // geometry.cell) + 1
    assert per_row[0] >= geometry.cols - geometry.tag_cols * tag_box_cells


def test_margins_stay_out_of_borderless_territory() -> None:
    assert PRINTER_MIN_MARGIN_MM == 3.0
    assert MIN_MARGIN_MM > PRINTER_MIN_MARGIN_MM
    resolve_config(margin_mm=MIN_MARGIN_MM)
    with pytest.raises(ValueError, match="borderless"):
        resolve_config(margin_mm=MIN_MARGIN_MM - 0.5)
    with pytest.raises(ValueError, match="borderless"):
        resolve_config(margin_bottom_mm=0)
    with pytest.raises(ValueError, match="borderless"):
        validate_config(PaperClipConfig(margin_left_mm=PRINTER_MIN_MARGIN_MM))
