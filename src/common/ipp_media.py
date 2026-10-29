from typing import NamedTuple


class MediaSize(NamedTuple):
    keyword: str
    points: tuple[int, int]
    hundredths: tuple[int, int]


MEDIA_SIZES: dict[str, MediaSize] = {
    "A4": MediaSize("iso_a4_210x297mm", (595, 842), (21000, 29700)),
    "A5": MediaSize("iso_a5_148x210mm", (420, 595), (14800, 21000)),
    "A6": MediaSize("iso_a6_105x148mm", (298, 420), (10500, 14800)),
    "Letter": MediaSize("na_letter_8.5x11in", (612, 792), (21590, 27940)),
    "Legal": MediaSize("na_legal_8.5x14in", (612, 1008), (21590, 35560)),
}
