from collections.abc import Callable
from itertools import combinations, permutations

from common.page_bytes import PageBytePlan, symbol_count_for_bytes
from serialization.decode.erasures import bytes_and_erasures
from serialization.decode.errors import DecodeError, PassphraseError
from serialization.decode.observation import PageObservation
from serialization.encode.header_bytes import DecodedQrHeader

Attempt = Callable[[dict[int, PageObservation]], None]


def assign_orphans(
    orphans: list[PageObservation],
    chosen: dict[int, PageObservation],
    header: DecodedQrHeader,
    plan: PageBytePlan,
    attempt: Attempt,
) -> dict[int, PageObservation]:
    missing = [index for index in range(header.total_pages) if index not in chosen]
    if len(orphans) > len(missing):
        raise DecodeError("more unindexed pages than missing page slots")
    if len(orphans) > 3 or len(missing) > 6:
        raise DecodeError("too many unindexed pages to place")
    for combo in combinations(missing, len(orphans)):
        for order in permutations(combo):
            trial = _place(orphans, chosen, header, plan, order)
            if _accepts(trial, attempt):
                return trial
    raise DecodeError("could not match pages whose headers were lost")


def _place(
    orphans: list[PageObservation],
    chosen: dict[int, PageObservation],
    header: DecodedQrHeader,
    plan: PageBytePlan,
    order: tuple[int, ...],
) -> dict[int, PageObservation]:
    trial = dict(chosen)
    for page, index in zip(orphans, order, strict=True):
        trial[index] = _at_index(page, header, index, plan)
    return trial


def _accepts(trial: dict[int, PageObservation], attempt: Attempt) -> bool:
    try:
        attempt(trial)
    except PassphraseError:
        raise
    except DecodeError:
        return False
    return True


def _at_index(
    page: PageObservation, header: DecodedQrHeader, index: int, plan: PageBytePlan,
) -> PageObservation:
    nbytes = plan.read_len[index] if index < header.data_pages else plan.parity_len
    needed = symbol_count_for_bytes(nbytes, header.num_symbols)
    symbols, confidence = _fit(list(page.symbols), list(page.confidence), needed)
    data, erasures = bytes_and_erasures(symbols, confidence, header.num_symbols, nbytes)
    return page._replace(
        header=header._replace(page_index=index),
        data=data,
        erasures=tuple(erasures),
        symbols=tuple(symbols),
        confidence=tuple(confidence),
    )


def _fit(symbols: list[int], confidence: list[float], needed: int) -> tuple[list[int], list[float]]:
    chosen = symbols[:needed]
    conf = confidence[:needed]
    if len(chosen) < needed:
        chosen.extend([0] * (needed - len(chosen)))
        conf.extend([0.0] * (needed - len(conf)))
    return chosen, conf
