import logging
import subprocess
import sys
import time

from common.mdns_parse import Service
from common.system_browse_parse import (
    instance_names,
    prefer_ipv4,
    reached_host,
    service_from_lookup,
    services_from_avahi,
)

logger = logging.getLogger(__name__)

_CACHE: tuple[float, tuple[Service, ...]] | None = None
_TTL = 30.0


def system_uscan_services(timeout: float = 2.0) -> list[Service]:
    cached = _cached()
    if cached is not None:
        return list(cached)
    found = tuple(prefer_ipv4(_browse(timeout)))
    _remember(found)
    logger.info("System scanner browse found %s eSCL service(s)", len(found))
    return list(found)


def _browse(timeout: float) -> list[Service]:
    if sys.platform == "darwin":
        return _dns_sd_services(timeout)
    return services_from_avahi(_run(["avahi-browse", "-rpt", "-t", "_uscan._tcp"], timeout))


def _dns_sd_services(timeout: float) -> list[Service]:
    names = instance_names(_run(["dns-sd", "-B", "_uscan._tcp"], timeout))
    found: list[Service] = []
    for name in names:
        service = _resolve_name(name, timeout)
        if service is not None:
            found.append(service)
    return found


def _resolve_name(name: str, timeout: float) -> Service | None:
    lookup = _run(["dns-sd", "-L", name, "_uscan._tcp", "local"], timeout)
    host, _port = reached_host(lookup)
    address = _run(["dns-sd", "-G", "v4", host], timeout) if host else ""
    return service_from_lookup(name, lookup, address)


def _run(command: list[str], timeout: float) -> str:
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except OSError as exc:
        logger.info("Scanner browse command failed: %s", exc)
        return ""
    return _finish(proc, timeout)


def _finish(proc: subprocess.Popen[str], timeout: float) -> str:
    try:
        output, _stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.terminate()
        output = _stopped(proc)
    return output or ""


def _stopped(proc: subprocess.Popen[str]) -> str:
    try:
        output, _stderr = proc.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        proc.kill()
        output, _stderr = proc.communicate()
    return output or ""


def _cached() -> tuple[Service, ...] | None:
    if _CACHE is None or time.monotonic() - _CACHE[0] >= _TTL:
        return None
    return _CACHE[1]


def _remember(found: tuple[Service, ...]) -> None:
    global _CACHE
    _CACHE = (time.monotonic(), found)
