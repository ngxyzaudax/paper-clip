from pathlib import Path

from common.config import PaperClipConfig, resolve_config


def _opt_int(raw: str) -> int | None:
    s = raw.strip()
    if not s:
        return None
    return int(s)


def _opt_float(raw: str) -> float | None:
    s = raw.strip()
    if not s:
        return None
    return float(s)


def tui_encoding_config(
    config_path_str: str,
    num_colors_str: str,
    cell_size_str: str,
    paper_size: str,
    print_dpi_str: str,
    rs_str: str,
    redundancy_pages_str: str,
    margin_top_str: str,
    margin_right_str: str,
    margin_bottom_str: str,
    margin_left_str: str,
) -> PaperClipConfig:
    cf = Path(config_path_str.strip()).expanduser() if config_path_str.strip() else None
    if cf is not None and not cf.is_file():
        raise ValueError(f"Config file not found: {cf}")
    return resolve_config(
        config_file=cf,
        num_colors=_opt_int(num_colors_str),
        cell_size_px=_opt_int(cell_size_str),
        paper_size=paper_size if paper_size else None,
        print_dpi=_opt_int(print_dpi_str),
        rs_redundancy=_opt_float(rs_str),
        redundancy_pages=_opt_int(redundancy_pages_str),
        margin_top_mm=_opt_float(margin_top_str),
        margin_right_mm=_opt_float(margin_right_str),
        margin_bottom_mm=_opt_float(margin_bottom_str),
        margin_left_mm=_opt_float(margin_left_str),
    )
