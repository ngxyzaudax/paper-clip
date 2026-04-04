NAV_GROUPS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("DATA", [
        ("nav-encode", "Encode File", "ENC"),
        ("nav-decode", "Decode Pages", "DEC"),
        ("nav-verify", "Verify Roundtrip", "VER"),
        ("nav-info", "Config Info", "INF"),
    ]),
    ("HARDWARE", [
        ("nav-capture", "Capture", "CAP"),
        ("nav-scan", "Scan Pages", "SCN"),
        ("nav-devices", "Devices", "DEV"),
    ]),
    ("TOOLS", [
        ("nav-print", "Print Pages", "PRT"),
        ("nav-generate", "Generate Test Job", "GEN"),
        ("nav-config", "Config Files", "CFG"),
        ("nav-ml", "ML Training", "ML"),
    ]),
]

PANEL_REGISTRY: dict[str, tuple[str, str]] = {
    "nav-encode": ("cli.tui.encode_screen", "EncodeScreen"),
    "nav-decode": ("cli.tui.decode_screen", "DecodeScreen"),
    "nav-verify": ("cli.tui.verify_screen", "VerifyScreen"),
    "nav-info": ("cli.tui.info_screen", "InfoScreen"),
    "nav-capture": ("cli.tui.capture_screen", "CaptureScreen"),
    "nav-scan": ("cli.tui.scan_screen", "ScanScreen"),
    "nav-devices": ("cli.tui.devices_screen", "DevicesScreen"),
    "nav-print": ("cli.tui.print_screen", "PrintScreen"),
    "nav-generate": ("cli.tui.generate_screen", "GenerateScreen"),
    "nav-config": ("cli.tui.config_screen", "ConfigScreen"),
    "nav-ml": ("cli.tui.ml_screen", "MLScreen"),
}

NAV_FULL: dict[str, str] = {i: l for _, g in NAV_GROUPS for i, l, _ in g}
NAV_SHORT: dict[str, str] = {i: s for _, g in NAV_GROUPS for i, _, s in g}


WELCOME = """\
       ┌──────────┐
       │ ▓▓░░▓▓░░ │
       │ ░░▓▓░░▓▓ │  File ──► Paper
       │ ▓▓░░▓▓░░ │
       │ ░░▓▓░░▓▓ │  Paper ──► File
       └──────────┘

    Select an option from the sidebar."""


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
