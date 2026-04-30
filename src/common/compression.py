import zstandard


def compress(data: bytes) -> bytes:
    compressor = zstandard.ZstdCompressor(level=19)
    return compressor.compress(data)

