import zstandard


def compress(data: bytes) -> bytes:
    compressor = zstandard.ZstdCompressor(level=19)
    return compressor.compress(data)


def decompress(data: bytes) -> bytes:
    return zstandard.ZstdDecompressor().decompress(data)

