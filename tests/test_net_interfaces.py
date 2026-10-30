import ctypes
import socket
import struct

from common.net_interfaces import ipv4_from_sockaddr, ipv4_interfaces


def test_darwin_sockaddr_is_not_read_as_linux() -> None:
    addr, _buf = _sockaddr(_darwin_bytes())
    assert ipv4_from_sockaddr(addr, "darwin") == "10.1.2.3"
    assert ipv4_from_sockaddr(addr, "linux") is None


def test_linux_sockaddr_is_not_read_as_darwin() -> None:
    addr, _buf = _sockaddr(_linux_bytes())
    assert ipv4_from_sockaddr(addr, "linux") == "10.4.5.6"
    assert ipv4_from_sockaddr(addr, "darwin") is None


def test_ipv4_interfaces_skip_loopback() -> None:
    for addr in ipv4_interfaces():
        assert not addr.startswith("127.")
        socket.inet_aton(addr)


def _sockaddr(raw: bytes) -> tuple[int, ctypes.Array]:
    buf = ctypes.create_string_buffer(raw)
    return ctypes.addressof(buf), buf


def _darwin_bytes() -> bytes:
    raw = bytearray(16)
    raw[0] = 16
    raw[1] = socket.AF_INET
    raw[4:8] = socket.inet_aton("10.1.2.3")
    return bytes(raw)


def _linux_bytes() -> bytes:
    raw = bytearray(16)
    raw[0:2] = struct.pack("=H", socket.AF_INET)
    raw[4:8] = socket.inet_aton("10.4.5.6")
    return bytes(raw)
