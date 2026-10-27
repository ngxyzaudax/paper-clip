from common.config import PaperClipConfig, validate_config
from serialization.encode.qr_header import DecodedQrHeader


def config_from_header(header: DecodedQrHeader) -> PaperClipConfig:
    return validate_config(PaperClipConfig(
        num_symbols=header.num_symbols,
        cell_size_px=header.cell_size_px,
        print_dpi=header.print_dpi,
        rs_redundancy=0.20,
        redundancy_pages=max(0, header.total_pages - header.data_pages),
        page_width_mm=header.page_width_mm,
        page_height_mm=header.page_height_mm,
        margin_top_mm=header.margin_top_mm,
        margin_right_mm=header.margin_right_mm,
        margin_bottom_mm=header.margin_bottom_mm,
        margin_left_mm=header.margin_left_mm,
    ))
