import common.device_discover as device_discover
from common.device_discover import list_escl_scanners, list_ipp_printers
from common.mdns_parse import Service
from common.types import PrinterInfo


def test_discovery_prefers_plain_ipp_for_one_uuid(monkeypatch) -> None:
    plain = _service("_ipp._tcp.local", "ET-8500", 631, {"ty": "ET-8500", "rp": "ipp/print", "UUID": "abc"})
    secure = _service("_ipps._tcp.local", "ET-8500", 631, {"ty": "ET-8500", "rp": "ipp/print", "UUID": "abc"})
    _mock_browse(monkeypatch, {"_ipp._tcp.local": [plain], "_ipps._tcp.local": [secure]})
    monkeypatch.setattr(
        "common.device_discover.get_printer_settings",
        lambda: {"uri": "ipp://192.0.2.8:631/ipp/print"},
    )
    found = list_ipp_printers()
    assert len(found) == 1
    assert found[0].uri == "ipp://192.0.2.8:631/ipp/print"
    assert found[0].state == "driverless"
    assert found[0].is_default


def test_configured_uri_is_kept_when_mdns_misses_it(monkeypatch) -> None:
    _mock_browse(monkeypatch, {})
    monkeypatch.setattr(
        "common.device_discover.get_printer_settings",
        lambda: {"uri": "ipps://192.0.2.9:631/ipp/print"},
    )
    found = list_ipp_printers()
    assert found == [PrinterInfo("192.0.2.9", "ipps://192.0.2.9:631/ipp/print", "configured", True)]


def test_escl_discovery_uses_the_uscan_service(monkeypatch) -> None:
    service = _service("_uscan._tcp.local", "ET-8500", 443, {"ty": "ET-8500", "usb_MFG": "EPSON", "rs": "eSCL"})
    _mock_browse(monkeypatch, {"_uscan._tcp.local": [service]})
    monkeypatch.setattr("common.device_discover.get_scanner_settings", lambda: {"uri": "", "device": ""})
    found = list_escl_scanners()
    assert len(found) == 1
    assert found[0].device_id == "https://192.0.2.8:443"
    assert found[0].vendor == "EPSON"
    assert found[0].device_type == "escl"


def _mock_browse(monkeypatch, found: dict[str, list[Service]]) -> None:
    device_discover._CACHE = None
    monkeypatch.setattr("common.device_discover.browse_types", lambda timeout=1.6: found)


def _service(service_type: str, instance: str, port: int, txt: dict[str, str]) -> Service:
    return Service(service_type, instance, "printer.local", port, ("192.0.2.8",), txt)
