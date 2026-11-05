from serialization.decode.observation import PageObservation


def header_summary(pages: tuple[PageObservation, ...]) -> str:
    if not pages:
        return ""
    return "; ".join(_line(page) for page in pages)


def _line(page: PageObservation) -> str:
    total = len(page.qr_slots_read) or 1
    read = page.qr_copies_read
    index = "u" if page.header.page_index < 0 else str(page.header.page_index + 1)
    mark = " [dark_orange]reprint[/]" if read <= 1 or page.header_source == "orphan" else ""
    if page.header_source == "orphan":
        return f"p{index} orphan from p{page.inferred_from + 1}{mark}"
    return f"p{index} {page.header_source} {read}/{total}{mark}"
