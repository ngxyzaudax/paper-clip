import zstandard


def compress(data: bytes) -> bytes:
    compressor = zstandard.ZstdCompressor(level=19)
    return compressor.compress(data)


def decompress(data: bytes) -> bytes:
    decompressor = zstandard.ZstdDecompressor()
    return decompressor.decompress(data, max_output_size=100 * 1024 * 1024)
