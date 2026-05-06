DEFAULT_NAV_ID = "nav-encode"

NAV_GROUPS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("DATA", [
        ("nav-encode", "Encode File", "ENC"),
    ]),
    ("HARDWARE", [
        ("nav-devices", "Devices", "DEV"),
        ("nav-print", "Print", "PRT"),
        ("nav-scan", "Scan", "SCN"),
    ]),
]

PANEL_REGISTRY: dict[str, tuple[str, str]] = {
    "nav-encode": ("cli.tui.encode_screen", "EncodeScreen"),
    "nav-devices": ("cli.tui.devices_screen", "DevicesScreen"),
    "nav-print": ("cli.tui.print_screen", "PrintScreen"),
    "nav-scan": ("cli.tui.scan_screen", "ScanScreen"),
}

NAV_FULL: dict[str, str] = {i: l for _, g in NAV_GROUPS for i, l, _ in g}
NAV_SHORT: dict[str, str] = {i: s for _, g in NAV_GROUPS for i, _, s in g}


def status_text() -> str:
    parts: list[str] = []
    try:
        from common.device_config import get_printer_settings, get_scanner_settings
        pr = get_printer_settings().get("name", "")
        sc = get_scanner_settings().get("device", "")
        if pr:
            parts.append(f"Pr: {pr[:18]}")
        if sc:
            short = sc.split(":")[-1][:18] if ":" in sc else sc[:18]
            parts.append(f"Sc: {short}")
    except Exception:
        pass
    return "\n".join(parts) if parts else "[dim]No devices[/dim]"
