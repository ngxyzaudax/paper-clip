import ctypes
import ctypes.util
import logging
import socket
import sys

logger = logging.getLogger(__name__)

_UP = 0x1
_LOOPBACK = 0x8
_MAX_INTERFACES = 256


class _Ifaddrs(ctypes.Structure):
    pass


_Ifaddrs._fields_ = [
    ("ifa_next", ctypes.POINTER(_Ifaddrs)),
    ("ifa_name", ctypes.c_char_p),
    ("ifa_flags", ctypes.c_uint),
    ("ifa_addr", ctypes.c_void_p),
    ("ifa_netmask", ctypes.c_void_p),
    ("ifa_ifu", ctypes.c_void_p),
    ("ifa_data", ctypes.c_void_p),
]

_IfaddrsPtr = ctypes.POINTER(_Ifaddrs)
_libc: ctypes.CDLL | None = None


def ipv4_interfaces() -> tuple[str, ...]:
    found = list(_getifaddrs_ipv4())
    default = _default_ipv4()
    if default and default not in found:
        found.append(default)
    return tuple(found)


def ipv4_from_sockaddr(addr: int, platform_name: str) -> str | None:
    if address_family(addr, platform_name) != socket.AF_INET:
        return None
    return read_ipv4(addr)


def address_family(addr: int, platform_name: str) -> int:
    if platform_name == "darwin":
        return int(ctypes.c_uint8.from_address(addr + 1).value)
    return int(ctypes.c_ushort.from_address(addr).value)


def read_ipv4(addr: int) -> str:
    return socket.inet_ntoa(ctypes.string_at(addr + 4, 4))


def _getifaddrs_ipv4() -> tuple[str, ...]:
    try:
        return _read_ifaddrs(sys.platform)
    except OSError as exc:
        logger.warning("IPv4 interface lookup failed: %s", exc)
        return ()


def _read_ifaddrs(platform_name: str) -> tuple[str, ...]:
    libc = _load_libc()
    head = _IfaddrsPtr()
    if libc.getifaddrs(ctypes.byref(head)) != 0:
        raise OSError(ctypes.get_errno(), "getifaddrs failed")
    try:
        return tuple(_addresses(head, platform_name))
    finally:
        if head:
            libc.freeifaddrs(head)


def _addresses(head: _IfaddrsPtr, platform_name: str) -> list[str]:
    found: list[str] = []
    cursor = head
    for _ in range(_MAX_INTERFACES):
        if not cursor:
            break
        item = cursor.contents
        addr = _ipv4_of(item, platform_name)
        if addr:
            found.append(addr)
        cursor = item.ifa_next
    return list(dict.fromkeys(found))


def _ipv4_of(item: _Ifaddrs, platform_name: str) -> str | None:
    if not item.ifa_addr or not _usable(int(item.ifa_flags)):
        return None
    addr = ipv4_from_sockaddr(int(item.ifa_addr), platform_name)
    if addr is None or addr.startswith("127.") or addr == "0.0.0.0":
        return None
    return addr


def _usable(flags: int) -> bool:
    return bool(flags & _UP) and not bool(flags & _LOOPBACK)


def _default_ipv4() -> str | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 9))
        addr = str(sock.getsockname()[0])
    except OSError:
        return None
    finally:
        sock.close()
    if addr.startswith("127.") or addr == "0.0.0.0":
        return None
    return addr


def _load_libc() -> ctypes.CDLL:
    global _libc
    if _libc is not None:
        return _libc
    path = ctypes.util.find_library("c")
    if not path:
        raise OSError("libc was not found")
    libc = ctypes.CDLL(path, use_errno=True)
    libc.getifaddrs.argtypes = [ctypes.POINTER(_IfaddrsPtr)]
    libc.getifaddrs.restype = ctypes.c_int
    libc.freeifaddrs.argtypes = [_IfaddrsPtr]
    libc.freeifaddrs.restype = None
    _libc = libc
    return libc
