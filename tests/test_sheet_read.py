import json

import numpy as np

from calibration.sheet_draw import draw_side
from calibration.sheet_sample import _printed_references
from serialization.decode.nearest_colour import nearest_symbols, rgb_to_lab
from calibration.sheet_io import layout_manifest
from calibration.sheet_limits import choose_profile
from calibration.sheet_place import sheet_side
from calibration.sheet_score import score_page


def test_pale_printed_ink_is_not_scored_as_blank() -> None:
    ideal = np.array(
        [[255, 255, 255], [0, 0, 0], [0, 255, 255], [255, 0, 255], [255, 255, 0]],
        np.float32,
    )
    samples = np.array(
        [[247, 246, 250], [162, 223, 242], [76, 71, 72], [160, 220, 240]],
        np.float32,
    )
    refs = _printed_references(samples, [[0, 2], [-1, 2]], ideal)
    symbols, _confidence = nearest_symbols(samples, refs)
    ideal_pick = int(np.argmin(np.linalg.norm(rgb_to_lab(samples[1:2]) - rgb_to_lab(ideal), axis=1)))
    assert ideal_pick == 0
    assert symbols.tolist() == [0, 2, 1, 2]


def test_layout_manifest_lists_both_sides() -> None:
    manifest = layout_manifest()
    assert [row["side"] for row in manifest] == ["front", "back"]
    assert [len(row["patches"]) for row in manifest] == [24, 40]
    json.dumps(manifest)


def test_clean_front_reads_every_patch_and_keeps_one_step_of_margin() -> None:
    image = np.asarray(draw_side(sheet_side("front")))
    side, reads = score_page(np.rot90(image, 2))
    assert side == "front"
    assert len(reads) == 24
    assert all(read.decoded for read in reads if read.kind == "qr")
    assert all(
        read.accuracy >= 0.99 and not read.slipped and read.tags_found == read.tags_expected
        for read in reads if read.kind != "qr"
    )
    chosen = choose_profile(reads)
    assert chosen.qr_module_mm == 0.22
    assert chosen.tag_size_mm == 6.0
    assert chosen.tag_pitch_mm == 16.0
    assert chosen.cell_size_px == 13
    assert chosen.dot_ratio == 0.62
    assert chosen.num_symbols == 11
    assert chosen.bytes_per_side > 0
