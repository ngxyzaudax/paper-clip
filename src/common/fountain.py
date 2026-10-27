import logging

from reedsolo import RSCodec

logger = logging.getLogger(__name__)


def encode_parity_pages(
    data_page_payloads: list[bytes],
    redundancy_pages: int,
) -> list[bytes]:
    if redundancy_pages <= 0 or not data_page_payloads:
        return []
    k = len(data_page_payloads)
    max_len = max(len(p) for p in data_page_payloads)
    padded = [p.ljust(max_len, b"\x00") for p in data_page_payloads]
    codec = RSCodec(redundancy_pages)
    parity_pages = [bytearray(max_len) for _ in range(redundancy_pages)]
    for byte_pos in range(max_len):
        data_bytes = bytes(p[byte_pos] for p in padded)
        encoded = bytes(codec.encode(data_bytes))
        parity_bytes = encoded[k:]
        for r in range(redundancy_pages):
            parity_pages[r][byte_pos] = parity_bytes[r]
    logger.info(
        "Generated %d parity page(s) from %d data page(s) (%d bytes each)",
        redundancy_pages, k, max_len,
    )
    return [bytes(p) for p in parity_pages]


def reconstruct_missing(
    pages: list[bytes | None],
    data_pages: int,
    redundancy_pages: int,
) -> list[bytes]:
    if redundancy_pages <= 0:
        raise ValueError("no parity pages are available")
    width = data_pages + redundancy_pages
    slots: list[bytes | None] = list(pages[:width])
    if len(slots) < width:
        slots.extend([None] * (width - len(slots)))
    present = [page for page in slots if page is not None]
    if not present:
        raise ValueError("no pages available to reconstruct")
    max_len = max(len(page) for page in present)
    codec = RSCodec(redundancy_pages)
    restored = [bytearray(max_len) for _ in range(data_pages)]
    for pos in range(max_len):
        codeword = bytearray(width)
        erase = [index for index, page in enumerate(slots) if page is None]
        for index, page in enumerate(slots):
            if page is None:
                continue
            codeword[index] = page[pos] if pos < len(page) else 0
        decoded = bytes(codec.decode(bytes(codeword), erase_pos=erase)[0])
        for index in range(data_pages):
            restored[index][pos] = decoded[index]
    return [bytes(part) for part in restored]
