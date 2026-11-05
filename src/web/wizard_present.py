from serialization.decode.readiness import document_readiness
from web.scan_guide import scan_step
from workflows.wizard_scans import page_index_of, scan_rows
from workflows.wizard_state import load_wizard


def present(job_id: str) -> dict[str, object]:
    wizard = load_wizard(job_id)
    scans = scan_rows(wizard)
    guide = scan_step(wizard, scans)
    return {
        **wizard,
        "scans": [scan_item(item) for item in scans],
        "readiness": readiness(wizard, scans),
        "step": guide,
        "next_prompt": str(guide["text"]),
    }


def scan_item(item: dict[str, object]) -> dict[str, object]:
    return _with_indices(_scan_core(item), item.get("page_indices"))


def readiness(wizard: dict[str, object], scans: list[dict[str, object]]) -> dict[str, object]:
    total = int(wizard["total_pages"] or 0)
    if total <= 0:
        return {"state": "missing", "missing": [], "parity_pages": 0}
    ready = document_readiness(int(wizard["data_pages"] or 0), total, kept_indices(scans))
    return {"state": ready.state, "missing": list(ready.missing), "parity_pages": ready.parity_pages}


def kept_indices(scans: list[dict[str, object]]) -> set[int]:
    found = [page_index_of(item.get("page_index")) for item in scans if item.get("kept")]
    return {index for index in found if index is not None}


def _scan_core(item: dict[str, object]) -> dict[str, object]:
    return {
        "name": str(item.get("name", "")),
        "page_index": page_index_of(item.get("page_index")),
        "total_pages": int(item.get("total_pages", 0) or 0),
        "sha256": str(item.get("sha256", "")),
        "rotation": int(item.get("rotation", 0) or 0),
        "status": str(item.get("status", "pending")),
        "kept": bool(item.get("kept", False)),
        "quality": item.get("quality"),
        "erasures": item.get("erasures") if isinstance(item.get("erasures"), int) else None,
    }


def _with_indices(presented: dict[str, object], indices: object) -> dict[str, object]:
    if not isinstance(indices, list):
        return presented
    return {**presented, "page_indices": list(indices)}
