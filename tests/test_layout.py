import pytest

from common.config import default_config, resolve_config
from common.format_spec import MIN_MARGIN_MM, PRINTER_MIN_MARGIN_MM
from common.geometry import page_geometry
from common.geometry_tags import tag_quiet_px
from common.page_layout import valid_cells_ordered

A6_SWEEP = {"paper_size": "A6", "print_dpi": 360, "cell_size_px": 18, "margin_mm": 10, "num_symbols": 5}


def _configs():
    return [default_config(), resolve_config(**A6_SWEEP), resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18)]


def _overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return not (a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])


@pytest.mark.parametrize("config", _configs())
def test_qr_sits_at_the_page_centre(config) -> None:
    geometry = page_geometry(config)
    centre_x = geometry.origin_x + geometry.qr.x + geometry.qr.width / 2
    centre_y = geometry.origin_y + geometry.qr.y + geometry.qr.height / 2
    assert abs(centre_x - geometry.page_w / 2) <= geometry.cell
    assert abs(centre_y - geometry.page_h / 2) <= geometry.cell


@pytest.mark.parametrize("config", _configs())
def test_calibration_strip_sits_under_the_qr(config) -> None:
    geometry = page_geometry(config)
    qr, strip, block = geometry.qr, geometry.calibration, geometry.centre
    assert strip.y >= qr.y + qr.height
    assert strip.y - (qr.y + qr.height) < geometry.cell
    assert block.x <= strip.x and strip.x + strip.width <= block.x + block.width
    assert strip.y + strip.height + geometry.cell == block.y + block.height


@pytest.mark.parametrize("config", _configs())
def test_no_tag_or_data_cell_touches_the_centre_block(config) -> None:
    geometry = page_geometry(config)
    quiet = tag_quiet_px(config.print_dpi)
    block = tuple(geometry.centre)
    for tag in geometry.tags:
        assert not _overlap((tag.x - quiet, tag.y - quiet, tag.size + 2 * quiet, tag.size + 2 * quiet), block)
    cell = geometry.cell
    for row, col in valid_cells_ordered(config):
        assert not _overlap((col * cell, row * cell, cell, cell), block)


@pytest.mark.parametrize("config", _configs())
def test_tag_ids_follow_the_full_mesh(config) -> None:
    geometry = page_geometry(config)
    for tag in geometry.tags:
        assert tag.tag_id == tag.row * geometry.tag_cols + tag.col
    corners = {0, geometry.tag_cols - 1, (geometry.tag_rows - 1) * geometry.tag_cols, geometry.tag_rows * geometry.tag_cols - 1}
    assert corners <= {tag.tag_id for tag in geometry.tags}
    assert len(geometry.tag_xs) == geometry.tag_cols and len(geometry.tag_ys) == geometry.tag_rows


def test_data_fills_every_row_around_the_qr() -> None:
    config = default_config()
    geometry = page_geometry(config)
    per_row = [0] * geometry.rows
    for row, _ in valid_cells_ordered(config):
        per_row[row] += 1
    assert min(per_row) >= geometry.cols // 2
    tag_box_cells = -(-(geometry.tags[0].size + 2 * tag_quiet_px(config.print_dpi)) // geometry.cell) + 1
    assert per_row[0] >= geometry.cols - geometry.tag_cols * tag_box_cells


def test_margins_stay_out_of_borderless_territory() -> None:
    assert PRINTER_MIN_MARGIN_MM == 3.0
    assert MIN_MARGIN_MM > PRINTER_MIN_MARGIN_MM
    resolve_config(margin_mm=MIN_MARGIN_MM)
    with pytest.raises(ValueError, match="borderless"):
        resolve_config(margin_mm=MIN_MARGIN_MM - 0.5)
    with pytest.raises(ValueError, match="borderless"):
        resolve_config(margin_bottom_mm=0)
