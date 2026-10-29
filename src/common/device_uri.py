from common.mdns_parse import Service
from common.types import PrinterInfo, ScannerInfo


def printer_uri(service: Service) -> str:
    scheme = "ipps" if service.service_type.lower().startswith("_ipps.") else "ipp"
    port = service.port or (443 if scheme == "ipps" else 631)
    resource = service.txt.get("rp", "ipp/print").strip("/")
    return f"{scheme}://{_host(service)}:{port}/{resource}"


def scanner_uri(service: Service) -> str:
    port = service.port or 443
    scheme = "https" if port in (443, 8443) else "http"
    return f"{scheme}://{_host(service)}:{port}"


def printer_from_service(service: Service, saved_uri: str) -> PrinterInfo:
    uri = printer_uri(service)
    return PrinterInfo(
        name=service.txt.get("ty") or service.instance or uri,
        uri=uri,
        state="driverless",
        is_default=uri == saved_uri,
    )


def scanner_from_service(service: Service, saved_uri: str) -> ScannerInfo:
    uri = scanner_uri(service)
    vendor = service.txt.get("usb_MFG", "")
    model = service.txt.get("ty") or service.instance or uri
    return ScannerInfo(uri, vendor, model, "escl")


def _host(service: Service) -> str:
    ipv4 = [item for item in service.addresses if ":" not in item]
    if ipv4:
        return ipv4[0]
    if service.addresses:
        return service.addresses[0]
    return service.host.rstrip(".") or service.instance
