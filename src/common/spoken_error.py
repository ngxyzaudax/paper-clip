def plain_device_message(detail: str) -> str:
    """Return a device failure in ordinary words, leaving other messages unchanged."""
    if not detail:
        return "invalid request"
    if not _technical(detail):
        return detail
    if "printer" in detail.lower() or "ipp" in detail.lower():
        return "The printer did not answer. Check that it is turned on and on this network."
    return "The scanner did not answer. Check that it is turned on and on this network, then try again."


def _technical(detail: str) -> bool:
    lowered = detail.lower()
    markers = ("escl", "errno", "ipp ", "no route to host", "connection refused", "timed out", "scannercapabilities")
    return any(marker in lowered for marker in markers)
