from common.config import PaperClipConfig
from common.page_layout import data_capacity_bytes, grid_dimensions, pages_needed
from common.palette import palette_from_config
from serialization.encode.encoder import prepare_payload
from serialization.encode.fill_sheets import plan_config, sheets_for
from serialization.encode.frame_payload import PreparedPayload
from workflows.encoding_form import EncodingFormPicks, resolve_encoding_form, sheet_plan


def build_plan(
    raw: bytes,
    filename: str,
    picks: EncodingFormPicks,
    passphrase: str | None,
) -> tuple[PreparedPayload, PaperClipConfig, dict[str, object]]:
    requested = resolve_encoding_form(picks)
    config = plan_config(raw, requested, filename, sheet_plan(picks))
    prepared = prepare_payload(raw, config, filename, passphrase)
    data_pages = pages_needed(len(prepared.payload), config)
    return prepared, config, {
        **layout_plan(config, picks, data_pages),
        "filename": filename,
        "file_bytes": len(raw),
        "payload_bytes": len(prepared.payload),
        "sha256": prepared.original_sha256.hex(),
        "passphrase_required": bool(prepared.flags & 1),
        "requested": requested_fields(requested),
    }


def requested_fields(config: PaperClipConfig) -> dict[str, int]:
    """Return the protection settings the user asked for before sheet filling."""
    return {"ecc_sym": config.ecc_sym, "cell_size_px": config.cell_size_px, "parity_pages": config.redundancy_pages}


def layout_plan(config: PaperClipConfig, picks: EncodingFormPicks, data_pages: int) -> dict[str, object]:
    total_pages = data_pages + config.redundancy_pages
    cols, rows = grid_dimensions(config)
    return {
        "filename": "",
        "file_bytes": 0,
        "payload_bytes": 0,
        "sha256": "",
        "data_pages": data_pages,
        "parity_pages": config.redundancy_pages,
        "total_pages": total_pages,
        "sides": sheet_plan(picks).sides,
        "sheets": sheets_for(total_pages, sheet_plan(picks).sides),
        "fill_sheets": picks.fill_sheets,
        "fill_priority": sheet_plan(picks).priority,
        "capacity_bytes": data_capacity_bytes(config),
        "ecc_sym": config.ecc_sym,
        "cell_size_px": config.cell_size_px,
        "grid": [cols, rows],
        "palette": [list(color) for color in palette_from_config(config)],
        "passphrase_required": False,
        "requested": requested_fields(config),
    }
