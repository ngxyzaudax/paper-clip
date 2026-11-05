from common.format_spec import HEADER_GRID_COPIES, HEADER_GRID_ECC, HEADER_STRUCT
from common.page_bytes import symbol_count_for_bytes


def header_codeword_length() -> int:
    return HEADER_STRUCT.size + HEADER_GRID_ECC


def header_grid_byte_count() -> int:
    return header_codeword_length() * HEADER_GRID_COPIES


def header_grid_symbols(num_symbols: int) -> int:
    return symbol_count_for_bytes(header_grid_byte_count(), num_symbols)
