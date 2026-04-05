from dataclasses import replace

from common.config import PaperClipConfig

PAPER_SIZES: dict[str, tuple[float, float]] = {
    "A3": (297.0, 420.0),
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
    "A6": (105.0, 148.0),
    "B4": (250.0, 353.0),
    "B5": (176.0, 250.0),
    "Letter": (215.9, 279.4),
    "Legal": (215.9, 355.6),
    "Tabloid": (279.4, 431.8),
}

DEFAULT_PAPER_SIZE = "A4"


def paper_size_names() -> list[str]:
    return list(PAPER_SIZES.keys())


def paper_size_dimensions(name: str) -> tuple[float, float]:
    if name not in PAPER_SIZES:
        raise ValueError(f"Unknown paper size: {name}. Available: {', '.join(PAPER_SIZES)}")
    return PAPER_SIZES[name]


def config_with_page_dimensions(config: PaperClipConfig, paper_size: str) -> PaperClipConfig:
    w, h = paper_size_dimensions(paper_size)
    return replace(config, page_width_mm=w, page_height_mm=h)


def detect_paper_size(width_mm: float, height_mm: float) -> str:
    for name, (w, h) in PAPER_SIZES.items():
        if abs(w - width_mm) < 0.5 and abs(h - height_mm) < 0.5:
            return name
    return f"{width_mm}x{height_mm}mm"


def paper_size_options() -> list[tuple[str, str]]:
    """Returns (label, value) pairs for Select widgets."""
    return [
        (f"{name} ({w:.0f} x {h:.0f} mm)", name)
        for name, (w, h) in PAPER_SIZES.items()
    ]


def paper_size_option_label(value: str) -> str:
    for label, name in paper_size_options():
        if name == value:
            return label
    return value
