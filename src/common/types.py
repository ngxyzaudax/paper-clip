from typing import NamedTuple

type SymbolGrid = list[list[int]]
type RGB = tuple[int, int, int]
type Point = tuple[float, float]


class Region(NamedTuple):
    x: int
    y: int
    width: int
    height: int


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
