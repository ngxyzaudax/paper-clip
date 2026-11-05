from collections.abc import Callable

from fastapi import HTTPException

from web.wizard_present import present
from workflows.wizard_scans import page_index_of, scan_rows
from workflows.wizard_state import revise_wizard


def keep_named(job_id: str, name: str) -> dict[str, object]:
    revise_wizard(job_id, _keep(name))
    return present(job_id)


def _keep(name: str) -> Callable[[dict[str, object]], dict[str, object]]:
    def revise(wizard: dict[str, object]) -> dict[str, object]:
        return _with_kept(wizard, name)
    return revise


def _with_kept(wizard: dict[str, object], name: str) -> dict[str, object]:
    scans = scan_rows(wizard)
    chosen = _chosen(scans, name)
    return {**wizard, "scans": [mark_kept(item, chosen) for item in scans]}


def _chosen(scans: list[dict[str, object]], name: str) -> dict[str, object]:
    found = [item for item in scans if item.get("name") == name]
    if not found:
        raise HTTPException(404, "Scan not found")
    return found[0]


def mark_kept(item: dict[str, object], chosen: dict[str, object]) -> dict[str, object]:
    if item.get("name") == chosen.get("name"):
        return _kept_flag(item, True)
    if _same_page(item, chosen):
        return _kept_flag(item, False)
    return item


def _same_page(item: dict[str, object], chosen: dict[str, object]) -> bool:
    left = page_index_of(item.get("page_index"))
    right = page_index_of(chosen.get("page_index"))
    return left is not None and right is not None and left == right


def _kept_flag(item: dict[str, object], kept: bool) -> dict[str, object]:
    if item.get("status") not in ("identified", "duplicate"):
        return {**item, "kept": kept}
    status = "identified" if kept else "duplicate"
    return {**item, "kept": kept, "status": status}
