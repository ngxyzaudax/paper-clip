import pytest

from calibration.sheet_field import tag_centers, written_cells
from calibration.sheet_place import sheet_side
from calibration.sheet_spec import PAGE_H_MM, PAGE_W_MM


def test_both_sides_fit_every_patch_on_a4() -> None:
    front, back = sheet_side("front"), sheet_side("back")
    _expect_fit(front)
    _expect_fit(back)
    assert _counts(front.patches) == {"qr": 7, "tag": 6, "pitch": 2, "dot": 12, "symbol": 6}
    assert _counts(back.patches) == {"qr": 1, "tag": 1, "pitch": 1, "dot": 12, "symbol": 10}
    assert {patch.name for patch in front.patches}.isdisjoint({patch.name for patch in back.patches})
    assert {patch.name for patch in back.patches} >= {"qr-0.18", "tag-2", "pitch-12"}
    assert {patch.cell_px for patch in back.patches if patch.kind == "dot"} == {16, 15, 14, 13}


def _base(name: str) -> int:
    return 500 if name == "front" else 520


def _expect_fit(side) -> None:
    assert {tag.tag_id for tag in side.frame} == set(range(_base(side.name), _base(side.name) + 16))
    ids = [tag_id for patch in side.patches for tag_id in patch.tag_ids]
    assert len(ids) == len(set(ids))
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
