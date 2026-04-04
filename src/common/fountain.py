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
