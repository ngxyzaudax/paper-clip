import http.client
import ssl
from urllib.parse import urlsplit

from common.device_error import DeviceError


def request_escl(
    uri: str,
    method: str,
    path: str,
    body: bytes | None = None,
    timeout: float = 60,
    content_type: str = "",
) -> tuple[int, str, bytes]:
    parts = urlsplit(uri)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise DeviceError(f"not an eSCL URI: {uri}")
    target = path if path.startswith("/") else "/" + path
    connection = _connection(parts.scheme, parts.hostname, parts.port, timeout)
    headers = {"Content-Type": content_type} if content_type else {}
    try:
        connection.request(method, target, body=body, headers=headers)
        response = connection.getresponse()
        status = response.status
        location = response.getheader("Location") or ""
        payload = response.read()
    except OSError as exc:
        raise DeviceError(f"eSCL {method} {uri}{target} failed: {exc}") from exc
    finally:
        connection.close()
    return status, location, payload


def _connection(scheme: str, host: str, port: int | None, timeout: float) -> http.client.HTTPConnection:
    if scheme == "http":
        return http.client.HTTPConnection(host, port or 80, timeout=timeout)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return http.client.HTTPSConnection(host, port or 443, timeout=timeout, context=context)
