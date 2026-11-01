from common.mdns_parse import Service


def instance_names(browse_text: str) -> tuple[str, ...]:
    names: list[str] = []
    for line in browse_text.splitlines():
        name = _instance_name(line)
        if name and name not in names:
            names.append(name)
    return tuple(names)


def service_from_lookup(name: str, lookup_text: str, address_text: str) -> Service | None:
    host, port = reached_host(lookup_text)
    if not host or port <= 0:
        return None
    return Service("_uscan._tcp.local", name, host, port, ipv4_addresses(address_text), {})


def reached_host(text: str) -> tuple[str, int]:
    for line in text.splitlines():
        found = _reached_line(line)
        if found != ("", 0):
            return found
    return "", 0


def ipv4_addresses(text: str) -> tuple[str, ...]:
    found: list[str] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[1] != "Add":
            continue
        for token in parts:
            if _ipv4_address(token) and token not in found:
                found.append(token)
    return tuple(found)


def services_from_avahi(text: str) -> list[Service]:
    found: list[Service] = []
    for line in text.splitlines():
        service = _avahi_line(line)
        if service is not None:
            found.append(service)
    return prefer_ipv4(found)


def prefer_ipv4(services: list[Service]) -> list[Service]:
    chosen: dict[str, Service] = {}
    for service in services:
        key = service.instance.casefold()
        current = chosen.get(key)
        if current is None or (_has_ipv4(service) and not _has_ipv4(current)):
            chosen[key] = service
    return list(chosen.values())


def _instance_name(line: str) -> str:
    marker = "_uscan._tcp."
    if "Add" not in line or marker not in line:
        return ""
    return line.split(marker, 1)[1].strip()


def _reached_line(line: str) -> tuple[str, int]:
    if "can be reached at" not in line:
        return "", 0
    target = line.split("can be reached at", 1)[1].strip().split(" ", 1)[0]
    host, separator, port_text = target.rpartition(":")
    if separator and port_text.isdigit():
        return host.rstrip("."), int(port_text)
    return "", 0


def _avahi_line(line: str) -> Service | None:
    if not line.startswith("="):
        return None
    parts = line.split(";")
    if len(parts) < 9 or not parts[8].isdigit() or not parts[6]:
        return None
    address = (parts[7],) if _ipv4_address(parts[7]) else ()
    return Service("_uscan._tcp.local", parts[3], parts[6].rstrip("."), int(parts[8]), address, {})


def _has_ipv4(service: Service) -> bool:
    return any(_ipv4_address(item) for item in service.addresses)


def _ipv4_address(host: str) -> bool:
    pieces = host.split(".")
    if len(pieces) != 4:
        return False
    return all(piece.isdigit() and 0 <= int(piece) <= 255 for piece in pieces)
