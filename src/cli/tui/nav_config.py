DEFAULT_NAV_ID = "nav-encode"

NAV_GROUPS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("WORKFLOW", [
        ("nav-encode", "1 Encode", "ENC"),
        ("nav-print", "2 Print", "PRT"),
        ("nav-scan", "3 Scan", "SCN"),
        ("nav-decode", "4 Decode", "DEC"),
    ]),
    ("SETUP", [
        ("nav-devices", "5 Devices", "DEV"),
        ("nav-calibrate", "6 Calibrate", "CAL"),
    ]),
]

PANEL_REGISTRY: dict[str, tuple[str, str]] = {
    "nav-encode": ("cli.tui.encode_screen", "EncodeScreen"),
    "nav-print": ("cli.tui.print_screen", "PrintScreen"),
    "nav-scan": ("cli.tui.scan_screen", "ScanScreen"),
    "nav-decode": ("cli.tui.decode_screen", "DecodeScreen"),
    "nav-devices": ("cli.tui.devices_screen", "DevicesScreen"),
    "nav-calibrate": ("cli.tui.calibrate_screen", "CalibrateScreen"),
}

PANELS_ACCEPTING_JOB: frozenset[str] = frozenset({"nav-print", "nav-decode"})

NAV_ORDER: tuple[str, ...] = tuple(nav_id for _, items in NAV_GROUPS for nav_id, _, _ in items)
NAV_FULL: dict[str, str] = {i: l for _, g in NAV_GROUPS for i, l, _ in g}
NAV_SHORT: dict[str, str] = {i: s for _, g in NAV_GROUPS for i, _, s in g}


def status_text() -> str:
    return "\n".join(_device_lines() + [_profile_line()])


def _device_lines() -> list[str]:
    try:
        from common.device_config import get_printer_settings, get_scanner_settings
        printer, scanner = get_printer_settings(), get_scanner_settings()
    except Exception:
        return ["[dim]No devices[/dim]"]
    pr = str(printer.get("name") or printer.get("uri") or "")
    sc = str(scanner.get("uri") or scanner.get("device") or "")
    lines = [f"Pr: {pr[:18]}"] if pr else []
    if sc:
        lines.append(f"Sc: {(sc.split(':')[-1] if ':' in sc else sc)[:18]}")
    return lines or ["[dim]No devices[/dim]"]


def _profile_line() -> str:
    from calibration.profile import load_density_profile
    saved = load_density_profile()
    if saved is None:
        return "[dim]Profile: defaults[/dim]"
    return f"[green]Profile: {saved.cell_size_px}px {saved.num_symbols}sym[/green]"
