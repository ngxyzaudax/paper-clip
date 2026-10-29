import http.client
import logging
import ssl
from typing import NamedTuple
from urllib.parse import urlsplit

from common.device_error import DeviceError

logger = logging.getLogger(__name__)
_tls_hosts: set[tuple[str, int | None]] = set()


class _Target(NamedTuple):
    scheme: str
    host: str
    port: int | None
    path: str


def post_ipp(uri: str, body: bytes, timeout: float) -> bytes:
    target = _prefer_tls(_target(uri))
    status, upgrade, payload = _post(target, body, timeout)
    if _needs_tls(target.scheme, status, upgrade):
        _tls_hosts.add((target.host, target.port))
        logger.info("IPP endpoint requires TLS; retrying %s over IPPS", uri)
        status, _upgrade, payload = _post(target._replace(scheme="ipps"), body, timeout)
    if status != 200:
        raise DeviceError(f"IPP HTTP {status} from {uri}")
    return payload


def _prefer_tls(target: _Target) -> _Target:
    if target.scheme == "ipp" and (target.host, target.port) in _tls_hosts:
        return target._replace(scheme="ipps")
    return target


def _needs_tls(scheme: str, status: int, upgrade: str) -> bool:
    return scheme == "ipp" and status == 426 and "tls" in upgrade.lower()


def _target(uri: str) -> _Target:
    parts = urlsplit(uri)
    if parts.scheme not in ("ipp", "ipps") or not parts.hostname:
        raise DeviceError(f"not an IPP URI: {uri}")
    return _Target(parts.scheme, parts.hostname, parts.port, parts.path or "/ipp/print")


def _post(target: _Target, body: bytes, timeout: float) -> tuple[int, str, bytes]:
    connection = _connection(target, timeout)
    try:
        connection.request("POST", target.path, body=body, headers={"Content-Type": "application/ipp"})
        response = connection.getresponse()
        return response.status, response.getheader("Upgrade") or "", response.read()
    except OSError as exc:
        raise DeviceError(f"IPP request to {target.host} failed: {exc}") from exc
    finally:
        connection.close()


def _connection(target: _Target, timeout: float) -> http.client.HTTPConnection:
    port = target.port or 631
    if target.scheme == "ipp":
        return http.client.HTTPConnection(target.host, port, timeout=timeout)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return http.client.HTTPSConnection(target.host, port, timeout=timeout, context=context)
