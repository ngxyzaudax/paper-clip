from collections.abc import Callable

from serialization.decode.identify import ScanIdentity
from web.wizard_fields import apply_note
from workflows.scan_jobs import count_scans
from workflows.wizard_scans import rows_for_update, scan_rows, stored_scan_rows
from workflows.wizard_state import revise_meta, session_dir, stored_wizard


def commit_scan(
    job_id: str,
    name: str,
    identity: ScanIdentity | None,
    quality: dict[str, object],
    dpi: int | None,
    mode: str,
) -> None:
    revise_meta(job_id, _commit(job_id, name, identity, quality, dpi, mode))


def capture_fields(dpi: int | None, mode: str, pages: int) -> dict[str, object]:
    return _with_mode(_with_dpi({"pages": pages}, dpi), mode)


def _commit(
    job_id: str,
    name: str,
    identity: ScanIdentity | None,
    quality: dict[str, object],
    dpi: int | None,
    mode: str,
) -> Callable[[dict[str, object], dict[str, object]], dict[str, object]]:
    def revise(meta: dict[str, object], wizard: dict[str, object]) -> dict[str, object]:
        rows = rows_for_update(scan_rows(wizard), stored_scan_rows(meta), name)
        updated = apply_note(wizard, identity, name, quality, rows)
        extra = capture_fields(dpi, mode, count_scans(session_dir(job_id)))
        return {**meta, **extra, "wizard": stored_wizard(updated)}
    return revise


def _with_dpi(fields: dict[str, object], dpi: int | None) -> dict[str, object]:
    if dpi is None:
        return fields
    return {**fields, "dpi": dpi}


def _with_mode(fields: dict[str, object], mode: str) -> dict[str, object]:
    if not mode:
        return fields
    return {**fields, "mode": mode}
