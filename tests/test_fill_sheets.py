from common.config import PaperClipConfig, resolve_config
from common.page_layout import pages_needed
from scan_sim.render import render_document
from serialization.decode.pipeline import decode
from serialization.encode.fill_sheets import SheetPlan, plan_config, sheets_for
from serialization.encode.fit_ecc import fill_config
from serialization.encode.encoder import prepare_payload

RAW = b"paper-clip keeps this note " * 4
NAME = "note.txt"


def _page() -> PaperClipConfig:
    return resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10, redundancy_pages=0)


def _total_pages(config: PaperClipConfig) -> int:
    prepared = prepare_payload(RAW, config, NAME, None)
    return pages_needed(len(prepared.payload), config) + config.redundancy_pages


def test_without_fill_the_plan_matches_the_ecc_fill() -> None:
    assert plan_config(RAW, _page(), NAME, SheetPlan(sides=2, fill=False)) == fill_config(RAW, _page(), NAME)


def test_duplex_fill_turns_the_blank_back_into_a_parity_page() -> None:
    config = plan_config(RAW, _page(), NAME, SheetPlan(sides=2, fill=True))
    assert config.redundancy_pages == 1
    assert _total_pages(config) == 2


def test_sheet_target_spreads_parity_over_more_sheets() -> None:
    config = plan_config(RAW, _page(), NAME, SheetPlan(sides=2, fill=True, sheets=2))
    assert _total_pages(config) == 4
    assert sheets_for(_total_pages(config), 2) == 2


def test_protection_priority_keeps_every_parity_byte() -> None:
    base = fill_config(RAW, _page(), NAME)
    kept = plan_config(RAW, _page(), NAME, SheetPlan(sides=1, fill=True))
    assert kept.ecc_sym >= base.ecc_sym
    assert _total_pages(kept) == _total_pages(base)


def test_balanced_priority_trades_spare_parity_for_larger_dots() -> None:
    base = fill_config(RAW, _page(), NAME)
    grown = plan_config(RAW, _page(), NAME, SheetPlan(sides=1, fill=True, priority="balanced"))
    assert grown.cell_size_px > base.cell_size_px
    assert grown.ecc_sym >= 128
    assert _total_pages(grown) == _total_pages(base)


def test_dots_priority_grows_cells_at_least_as_far_as_balanced() -> None:
    balanced = plan_config(RAW, _page(), NAME, SheetPlan(sides=1, fill=True, priority="balanced"))
    dots = plan_config(RAW, _page(), NAME, SheetPlan(sides=1, fill=True, priority="dots"))
    assert dots.cell_size_px >= balanced.cell_size_px
    assert dots.ecc_sym >= _page().ecc_sym


def test_parity_back_alone_recovers_the_file() -> None:
    config = plan_config(RAW, _page(), NAME, SheetPlan(sides=2, fill=True))
    images, _prepared, _grids = render_document(RAW, config, NAME)
    assert len(images) == 2
    recovered, decoded_name = decode([images[1]], use_model=False)
    assert (recovered, decoded_name) == (RAW, NAME)
