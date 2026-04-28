from common.scan_blend import tier_cumulative_ends

_TIER_TAG: dict[str, str] = {
    "primaries (K, C, M, Y)": "CMYK",
    "2-ink secondaries": "2-mix",
    "2-ink + K tints": "K-tint",
    "neutral gray": "gray",
    "3-ink mixes": "3-mix",
    "4-ink mix": "4-mix",
}


def compact_preset_for_ink_count(ink_count: int) -> str:
    tiers = tier_cumulative_ends()
    if ink_count <= 0 or not tiers:
        return ""
    prev = 0
    parts: list[str] = []
    for full_name, end in tiers:
        tag = _TIER_TAG[full_name]
        if ink_count >= end:
            parts.append(tag)
            prev = end
        elif ink_count > prev:
            parts.append(f"{tag}~")
            break
        else:
            break
    return "+".join(parts)


def symbol_row_label(symbol_count: int) -> str:
    preset = compact_preset_for_ink_count(symbol_count - 1)
    base = f"{symbol_count} sym"
    return f"{base} · {preset}" if preset else base
