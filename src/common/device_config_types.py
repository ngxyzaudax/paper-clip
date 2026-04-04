from typing import TypedDict


class PrinterSettings(TypedDict):
    name: str
    dpi: int
    paper_size: str


class ScannerSettings(TypedDict):
    device: str
    dpi: int
    mode: str


class DeviceConfigFile(TypedDict):
    printer: PrinterSettings
    scanner: ScannerSettings
