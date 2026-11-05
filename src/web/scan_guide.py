from workflows.wizard_scans import page_index_of

START = "Put any page face down on the glass. You can start with any sheet."
FLIP = "That side is in. Flip this sheet and scan the other side."
NEXT_SHEET = "That sheet is done. Take another sheet and scan either side."
NEXT_PAGE = "That page is in. Put another page face down. Any page you have not scanned yet is fine."
DONE = "Every side is in. Decode when you are ready."


def scan_step(wizard: dict[str, object], scans: list[dict[str, object]]) -> dict[str, object]:
    problem = problem_step(scans)
    if problem is not None:
        return problem
    total = int(wizard.get("total_pages") or 0)
    kept = kept_pages(scans, total)
    done = len(kept)
    if total <= 0 or done == 0:
        return step("wait", START, done=done, total=total)
    if done >= total:
        return step("done", DONE, done=done, total=total)
    if bool(wizard.get("duplex")):
        return duplex_step(total, kept, last_page(scans), done)
    return step("next", NEXT_PAGE, page=first_missing(total, kept), done=done, total=total)


def problem_step(scans: list[dict[str, object]]) -> dict[str, object] | None:
    if not scans:
        return None
    status = str(scans[-1].get("status", ""))
    if status == "unidentified":
        return step("retry", "That scan could not be read. Close the lid and scan the same side again.")
    if status == "two-pages":
        return step("retry", "That photo shows two pages. Scan one side at a time.")
    if status == "foreign":
        return step("retry", "That sheet is from a different file. Set it aside and scan a side of this file.")
    return None


def duplex_step(total: int, kept: set[int], last: int | None, done: int) -> dict[str, object]:
    if last is not None and (last ^ 1) < total and (last ^ 1) not in kept:
        return step("flip", FLIP, page=last ^ 1, sheet=last // 2 + 1, side="back" if last % 2 == 0 else "front", done=done, total=total)
    target = first_missing(total, kept)
    return step("next", NEXT_SHEET, page=target, sheet=target // 2 + 1, side="either", done=done, total=total)


def kept_pages(scans: list[dict[str, object]], total: int) -> set[int]:
    found = [page_index_of(item.get("page_index")) for item in scans if item.get("kept")]
    return {index for index in found if index is not None and (total <= 0 or index < total)}


def last_page(scans: list[dict[str, object]]) -> int | None:
    for item in reversed(scans):
        if item.get("kept"):
            return page_index_of(item.get("page_index"))
    return None


def first_missing(total: int, kept: set[int]) -> int:
    return next(index for index in range(total) if index not in kept)


def step(
    action: str,
    text: str,
    page: int | None = None,
    sheet: int | None = None,
    side: str = "",
    done: int = 0,
    total: int = 0,
) -> dict[str, object]:
    return {"action": action, "page": page, "sheet": sheet, "side": side, "text": text, "done": done, "total": total}
