from typing import NamedTuple

type SymbolGrid = list[list[int]]
type RGB = tuple[int, int, int]
type Point = tuple[float, float]


class Region(NamedTuple):
    x: int
    y: int
    width: int
    height: int


class HeaderData(NamedTuple):
    magic: bytes
    version: int
    flags: int
    num_colors: int
    cell_size_px: int
    ecc_symbols: int
    scan_dpi: int
    grid_cols: int
    grid_rows: int
    page_index: int
    total_pages: int
    data_pages: int
    data_length: int
    sha256_hash: bytes
    header_crc: int
    crc_valid: bool


class PageInfo(NamedTuple):
    filename: str
    file_size: int
    page_index: int
    total_pages: int
    data_pages: int
    sha256_hash: bytes
    encrypted: bool
    timestamp: str


class PrinterInfo(NamedTuple):
    name: str
    uri: str
    state: str
    is_default: bool


class PrinterCapabilities(NamedTuple):
    resolutions: list[tuple[int, int]]
    paper_sizes: list[str]
    color_modes: list[str]
    duplex_modes: list[str]


class ScannerInfo(NamedTuple):
    device_id: str
    vendor: str
    model: str
    device_type: str


class ScannerCapabilities(NamedTuple):
    resolutions: list[int]
    modes: list[str]
    sources: list[str]
