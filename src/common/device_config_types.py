from typing import TypedDict


class PrinterSettings(TypedDict):
    name: str
    uri: str
    dpi: int
    paper_size: str
    profile: dict[str, str]


class ScannerSettings(TypedDict):
    device: str
    uri: str
    dpi: int
    mode: str
    profile: dict[str, str]


class DeviceConfigFile(TypedDict):
    printer: PrinterSettings
    scanner: ScannerSettings
