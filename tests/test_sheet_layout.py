import pytest

from calibration.sheet_field import tag_centers, tag_quiet_mm, written_cells
from calibration.sheet_place import sheet_side
from calibration.sheet_spec import CONTENT_MM, PAGE_H_MM, PAGE_W_MM, TAG_COLUMNS, TAG_ROWS


def test_both_sides_fit_every_patch_on_a4() -> None:
    front, back = sheet_side("front"), sheet_side("back")
    _expect_fit(front)
    _expect_fit(back)
    assert _counts(front.patches) == {"qr": 3, "tag": 3, "pitch": 0, "dot": 9, "symbol": 9}
    assert _counts(back.patches) == {"qr": 0, "tag": 0, "pitch": 0, "dot": 15, "symbol": 25}
    assert {patch.name for patch in front.patches}.isdisjoint({patch.name for patch in back.patches})
    assert {patch.cell_px for patch in front.patches if patch.kind == "dot"} == {15, 14, 13}
    assert {patch.cell_px for patch in back.patches if patch.kind == "dot"} == {12, 11, 10, 9, 8}
    _expect_full(front)
    _expect_full(back)
    _expect_symbol_gate(front)
    _expect_symbol_gate(back)


def _expect_full(side) -> None:
    bottom = max(patch.y_mm + patch.h_mm for patch in side.patches)
    right = max(patch.x_mm + patch.w_mm for patch in side.patches)
    assert bottom >= PAGE_H_MM - CONTENT_MM - 0.05
    assert right >= PAGE_W_MM - CONTENT_MM - 0.05
    for patch in side.patches:
        if patch.kind != "qr":
            _expect_mesh(patch)


def _expect_mesh(patch) -> None:
    span = patch.tag_mm + 2.0 * tag_quiet_mm(patch.tag_mm)
    width = (TAG_COLUMNS - 1) * patch.pitch_mm + span
    height = (TAG_ROWS - 1) * patch.pitch_mm + span
    assert patch.w_mm - width < 3.0, patch.name
    assert patch.h_mm - height < 3.0, patch.name


def _expect_symbol_gate(side) -> None:
    cells = {patch.cell_px for patch in side.patches if patch.kind == "dot"}
    gated = {
        patch.cell_px for patch in side.patches
        if patch.kind == "symbol" and patch.symbols == 11 and patch.dot_ratio == 0.62
    }
    assert cells == gated


def _base(name: str) -> int:
    return 500 if name == "front" else 520


def _expect_fit(side) -> None:
    assert {tag.tag_id for tag in side.frame} == set(range(_base(side.name), _base(side.name) + 16))
    ids = [tag_id for patch in side.patches for tag_id in patch.tag_ids]
    assert len(ids) == len(set(ids))
    assert ids and min(ids) >= 10 and max(ids) < 500
    for patch in side.patches:
        assert 5.0 <= patch.x_mm
        assert 5.0 <= patch.y_mm
        assert patch.x_mm + patch.w_mm <= PAGE_W_MM - 5.0
        assert patch.y_mm + patch.h_mm <= PAGE_H_MM - 5.0
        if patch.kind != "qr":
            assert written_cells(patch) >= 300, patch.name
            assert len(patch.tag_ids) == 6
            half = patch.tag_mm / 2
            for x_mm, y_mm in tag_centers(patch).values():
                assert patch.x_mm <= x_mm - half and x_mm + half <= patch.x_mm + patch.w_mm, patch.name
                assert patch.y_mm <= y_mm - half and y_mm + half <= patch.y_mm + patch.h_mm, patch.name
    _expect_separated(side.patches)


def _counts(patches: tuple) -> dict[str, int]:
    return {kind: sum(item.kind == kind for item in patches) for kind in ("qr", "tag", "pitch", "dot", "symbol")}


def _expect_separated(patches: tuple) -> None:
    for index, left in enumerate(patches):
        for right in patches[index + 1:]:
            if _overlaps(left, right):
                pytest.fail(f"{left.name} overlaps {right.name}")


def _overlaps(left, right) -> bool:
    return not (
        left.x_mm + left.w_mm <= right.x_mm + 0.05
        or right.x_mm + right.w_mm <= left.x_mm + 0.05
        or left.y_mm + left.h_mm <= right.y_mm + 0.05
        or right.y_mm + right.h_mm <= left.y_mm + 0.05
    )
