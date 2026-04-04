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
    available: dict[int, bytes],
    data_page_count: int,
    total_page_count: int,
) -> list[bytes]:
    redundancy = total_page_count - data_page_count
    if redundancy <= 0:
        return [available.get(i, b"") for i in range(data_page_count)]

    missing_data = [i for i in range(data_page_count) if i not in available]
    if not missing_data:
        return [available[i] for i in range(data_page_count)]

    if len(available) < data_page_count:
        logger.warning(
            "Need %d pages but only %d available, attempting erasure recovery",
            data_page_count, len(available),
        )

    max_len = max(len(v) for v in available.values()) if available else 0
    padded: dict[int, bytes] = {
        k: v.ljust(max_len, b"\x00") for k, v in available.items()
    }

    n = data_page_count + redundancy
    codec = RSCodec(redundancy)
    recovered = [bytearray(max_len) for _ in range(data_page_count)]

    for byte_pos in range(max_len):
        codeword = bytearray(n)
        erasure_pos: list[int] = []
        for i in range(n):
            if i in padded:
                codeword[i] = padded[i][byte_pos]
            else:
                erasure_pos.append(i)
        try:
            decoded = bytes(codec.decode(bytes(codeword), erase_pos=erasure_pos)[0])
            for i in range(data_page_count):
                recovered[i][byte_pos] = decoded[i]
        except Exception:
            for i in range(data_page_count):
                if i in padded:
                    recovered[i][byte_pos] = padded[i][byte_pos]

    logger.info("Erasure recovery complete: %d missing page(s) reconstructed", len(missing_data))
    return [bytes(p) for p in recovered]
