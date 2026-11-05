import secrets
import socket
import threading
import webbrowser

import uvicorn

from web.app import create_app
from web.auth import token_url

_LOOPBACK = {"127.0.0.1", "localhost", "::1"}
_PORT_TRIES = 20


def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    """Serve the interface, opening a browser on the sign-in link when asked."""
    token = _token(host)
    sock = _listening_socket(host, port)
    url = _url(host, sock.getsockname()[1])
    link = token_url(url, token) if token else url
    print(f"paper-clip listening on {link}")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(link)).start()
    server = uvicorn.Server(uvicorn.Config(create_app(token), log_level="info"))
    server.run(sockets=[sock])


def _token(host: str) -> str | None:
    return None if host in _LOOPBACK else secrets.token_urlsafe(24)


def _url(host: str, port: int) -> str:
    shown = f"[{host}]" if ":" in host else host
    return f"http://{shown}:{port}/"


def _listening_socket(host: str, start: int) -> socket.socket:
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    for port in range(start, start + _PORT_TRIES):
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            sock.close()
            continue
        sock.listen(128)
        return sock
    raise SystemExit(f"No free port from {start} to {start + _PORT_TRIES - 1}")
