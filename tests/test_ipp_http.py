import pytest

from common.device_error import DeviceError
from common.ipp_http import _Target, _needs_tls, post_ipp


def test_needs_tls_only_for_plain_ipp_upgrade() -> None:
    assert _needs_tls("ipp", 426, "TLS/1.0, HTTP/1.1")
    assert not _needs_tls("ipps", 426, "TLS/1.0")
    assert not _needs_tls("ipp", 426, "HTTP/1.1")
    assert not _needs_tls("ipp", 200, "TLS/1.0")


def test_plain_ipp_retries_over_ipps(monkeypatch) -> None:
    from common import ipp_http

    ipp_http._tls_hosts.clear()
    calls: list[str] = []

    def fake_post(target: _Target, body: bytes, timeout: float) -> tuple[int, str, bytes]:
        calls.append(target.scheme)
        if target.scheme == "ipp":
            return 426, "TLS/1.0, HTTP/1.1", b""
        return 200, "", b"ipp-ok"

    monkeypatch.setattr("common.ipp_http._post", fake_post)
    assert post_ipp("ipp://192.168.1.2:631/ipp/print", b"req", 5) == b"ipp-ok"
    assert calls == ["ipp", "ipps"]


def test_later_requests_skip_plain_ipp_after_upgrade(monkeypatch) -> None:
    from common import ipp_http

    ipp_http._tls_hosts.clear()
    calls: list[str] = []

    def fake_post(target: _Target, body: bytes, timeout: float) -> tuple[int, str, bytes]:
        calls.append(target.scheme)
        if target.scheme == "ipp":
            return 426, "TLS/1.0, HTTP/1.1", b""
        return 200, "", b"ok"

    monkeypatch.setattr("common.ipp_http._post", fake_post)
    assert post_ipp("ipp://printer.example:631/ipp/print", b"a", 5) == b"ok"
    assert post_ipp("ipp://printer.example:631/ipp/print", b"b", 5) == b"ok"
    assert calls == ["ipp", "ipps", "ipps"]


def test_post_ipp_rejects_a_non_ipp_uri_and_http_errors(monkeypatch) -> None:
    from common import ipp_http

    ipp_http._tls_hosts.clear()
    with pytest.raises(DeviceError, match="not an IPP"):
        post_ipp("http://printer.example/ipp/print", b"req", 1)

    def fake_post(target: _Target, body: bytes, timeout: float) -> tuple[int, str, bytes]:
        return 400, "", b""

    monkeypatch.setattr("common.ipp_http._post", fake_post)
    with pytest.raises(DeviceError, match="HTTP 400"):
        post_ipp("ipp://printer.example:631/ipp/print", b"req", 1)
