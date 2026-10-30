import socket

from common.mdns_browse import browse_types
from common.mdns_socket import (
    MDNS_ADDRESS,
    bind_mdns,
    close_mdns_ports,
    enable_reuse,
    open_mdns_ports,
    send_queries,
)
from common.net_interfaces import ipv4_interfaces


class _Log:
    def __init__(self) -> None:
        self.sent: list[tuple[bytes, tuple[str, int]]] = []

    def sendto(self, payload: bytes, address: tuple[str, int]) -> int:
        self.sent.append((payload, address))
        return len(payload)


def test_linux_reuses_the_address_without_reuseport() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        before = sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT)
        enable_reuse(sock, "linux")
        assert sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR) != 0
        assert sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT) == before
    finally:
        sock.close()


def test_darwin_reuses_the_port() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        before = sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT)
        enable_reuse(sock, "darwin")
        assert sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT) != before
    finally:
        sock.close()


def test_bind_uses_another_port_when_the_requested_one_is_taken() -> None:
    holder = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        holder.bind(("", 0))
        busy = int(holder.getsockname()[1])
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            assert bind_mdns(sock, busy) != busy
        finally:
            sock.close()
    finally:
        holder.close()


def test_send_queries_writes_every_query_on_every_sender() -> None:
    first, second = _Log(), _Log()
    send_queries([first, second], [b"a", b"b"])
    expect = [(b"a", MDNS_ADDRESS), (b"b", MDNS_ADDRESS)]
    assert first.sent == expect
    assert second.sent == expect


def test_senders_use_an_ephemeral_port_on_each_interface() -> None:
    ports = open_mdns_ports()
    try:
        bound = {sock.getsockname()[0] for sock in ports.senders}
        assert ports.senders
        assert all(int(sock.getsockname()[1]) not in (0, 5353) for sock in ports.senders)
        for addr in ipv4_interfaces():
            assert addr in bound
    finally:
        close_mdns_ports(ports)


def test_browse_returns_no_services_when_the_socket_cannot_open(monkeypatch) -> None:
    def fail():
        raise OSError("network down")

    monkeypatch.setattr("common.mdns_browse.open_mdns_ports", fail)
    assert browse_types(("_ipp._tcp.local",), timeout=0.1) == {"_ipp._tcp.local": []}
