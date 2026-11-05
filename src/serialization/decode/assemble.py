from collections.abc import Callable

from common.page_bytes import PageBytePlan, page_byte_plan
from common.page_layout import data_capacity_bytes
from serialization.decode.assemble_rescue import rescue_failed_page
from serialization.decode.assemble_slots import Assembly, ErasureMap, Slots, decode_slots
from serialization.decode.errors import DecodeError
from serialization.decode.header_config import config_from_header
from serialization.decode.assemble_orphans import assign_orphans
from serialization.decode.observation import PageObservation
from serialization.encode.qr_header import DecodedQrHeader


def assemble_pages(pages: list[PageObservation], passphrase: str | None) -> Assembly:
    if not pages:
        raise DecodeError("no pages were decoded")
    header = compatible_header(pages)
    plan = page_byte_plan(
        header.payload_length, data_capacity_bytes(config_from_header(header)), header.data_pages, header.num_symbols,
    )
    chosen = _best_by_index(pages)
    orphans = [page for page in pages if page.header.page_index < 0]
    if orphans:
        chosen = assign_orphans(orphans, chosen, header, plan, _attempt(header, plan, passphrase))
    slots, erasure_map = _slots(chosen, header.total_pages)
    assembly = _decode(slots, erasure_map, header, plan, passphrase)
    return assembly._replace(scanned=tuple(sorted(chosen)), observed=chosen_pages(chosen))


def _attempt(
    header: DecodedQrHeader, plan: PageBytePlan, passphrase: str | None,
) -> Callable[[dict[int, PageObservation]], None]:
    def attempt(trial: dict[int, PageObservation]) -> None:
        slots, erasure_map = _slots(trial, header.total_pages)
        _decode(slots, erasure_map, header, plan, passphrase)
    return attempt


def chosen_pages(chosen: dict[int, PageObservation]) -> tuple[PageObservation, ...]:
    return tuple(chosen[index] for index in sorted(chosen))


def best_pages(pages: list[PageObservation]) -> tuple[PageObservation, ...]:
    return chosen_pages(_best_by_index(pages))


def _decode(
    slots: Slots, erasure_map: ErasureMap, header: DecodedQrHeader, plan: PageBytePlan, passphrase: str | None,
) -> Assembly:
    try:
        return decode_slots(slots, erasure_map, header, plan, passphrase)
    except DecodeError as exc:
        rescued = rescue_failed_page(slots, erasure_map, header, plan, passphrase, exc)
        if rescued is None:
            raise
        return rescued


def compatible_header(pages: list[PageObservation]) -> DecodedQrHeader:
    indexed = [page for page in pages if page.header.page_index >= 0]
    header = (indexed[0] if indexed else pages[0]).header
    for page in pages:
        other = page.header
        if (
            other.original_sha256 != header.original_sha256
            or other.payload_length != header.payload_length
            or other.total_pages != header.total_pages
            or other.data_pages != header.data_pages
        ):
            raise DecodeError("scan pages do not belong to the same document")
    return header


def _slots(chosen: dict[int, PageObservation], total_pages: int) -> tuple[Slots, ErasureMap]:
    slots: Slots = [None] * total_pages
    for index, page in chosen.items():
        slots[index] = page.data
    return slots, {index: list(page.erasures) for index, page in chosen.items()}


def _best_by_index(pages: list[PageObservation]) -> dict[int, PageObservation]:
    chosen: dict[int, PageObservation] = {}
    for page in pages:
        index = page.header.page_index
        if index < 0:
            continue
        if index >= page.header.total_pages:
            raise DecodeError(f"page index {index} is outside the document")
        previous = chosen.get(index)
        if previous is None or len(page.erasures) < len(previous.erasures):
            chosen[index] = page
    return chosen
