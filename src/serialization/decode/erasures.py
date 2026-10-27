from common.symbols import chunk_params, symbols_to_bytes

_ERASURE_CONFIDENCE = 0.22


def bytes_and_erasures(
    symbols: list[int],
    confidence: list[float],
    num_symbols: int,
    expected_bytes: int,
) -> tuple[bytes, list[int]]:
    if expected_bytes <= 0:
        return b"", []
    k, m = chunk_params(num_symbols)
    padded = list(symbols)
    conf = list(confidence)
    if len(padded) % m:
        missing = m - (len(padded) % m)
        padded.extend([0] * missing)
        conf.extend([0.0] * missing)
    rounded = ((expected_bytes + k - 1) // k) * k
    data = symbols_to_bytes(padded, num_symbols, rounded)
    erasures = []
    for chunk in range(0, len(padded), m):
        if any(conf[chunk + offset] < _ERASURE_CONFIDENCE for offset in range(m)):
            start = (chunk // m) * k
            erasures.extend(index for index in range(start, start + k) if index < expected_bytes)
    return data[:expected_bytes], erasures
