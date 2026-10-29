def read_dns_name(packet: bytes, offset: int) -> tuple[str, int]:
    labels: list[str] = []
    jumped = False
    end = offset
    for _ in range(128):
        if offset >= len(packet):
            break
        length = packet[offset]
        if length == 0:
            return ".".join(labels), offset + 1 if not jumped else end
        if length & 0xC0 == 0xC0:
            if not jumped:
                end = offset + 2
            offset = ((length & 0x3F) << 8) | packet[offset + 1]
            jumped = True
            continue
        offset += 1
        labels.append(packet[offset:offset + length].decode("utf-8", "replace"))
        offset += length
        if not jumped:
            end = offset
    return ".".join(labels), end


def encode_dns_name(name: str) -> bytes:
    encoded = bytearray()
    for label in name.rstrip(".").split("."):
        raw = label.encode()
        encoded.append(len(raw))
        encoded.extend(raw)
    encoded.append(0)
    return bytes(encoded)
