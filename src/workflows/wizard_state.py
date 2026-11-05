import json
from collections.abc import Callable
from pathlib import Path

from common.data_store import SCAN_JOBS_DIR
from common.json_file import JsonFileError, JsonObject, update_json_object
from web.safe import safe_segment, under_data
from workflows.scan_jobs import read_job
from workflows.wizard_scans import rows_for_update, scan_rows, scan_rows_on_disk, stored_scan_rows, upsert_scan


def session_dir(job_id: str) -> Path:
    return under_data(SCAN_JOBS_DIR / safe_segment(job_id))


def load_wizard(job_id: str) -> dict[str, object]:
    folder = session_dir(job_id)
    return _assemble(job_id, read_job(folder), folder)


def save_wizard(job_id: str, wizard: dict[str, object]) -> dict[str, object]:
    return revise_meta(job_id, _store_wizard(stored_wizard(wizard)))


def stored_wizard(wizard: dict[str, object]) -> dict[str, object]:
    parsed = json.loads(json.dumps(wizard))
    if not isinstance(parsed, dict):
        raise JsonFileError("Wizard state is not an object")
    return {key: value for key, value in parsed.items() if key != "job_id"}


def revise_wizard(
    job_id: str,
    revise: Callable[[dict[str, object]], dict[str, object]],
) -> dict[str, object]:
    return revise_meta(job_id, _wizard_change(revise))


def revise_meta(
    job_id: str,
    revise: Callable[[dict[str, object], dict[str, object]], dict[str, object]],
) -> dict[str, object]:
    folder = session_dir(job_id)
    update_json_object(folder / "job.json", _meta_change(job_id, folder, revise))
    return load_wizard(job_id)


def update_scan(job_id: str, name: str, fields: dict[str, object]) -> dict[str, object]:
    return revise_meta(job_id, _scan_change(name, fields))


def _assemble(job_id: str, meta: dict[str, object], folder: Path) -> dict[str, object]:
    base = _base(meta)
    return {
        "job_id": job_id,
        "duplex": bool(base.get("duplex", False)),
        "print_job_id": str(base.get("print_job_id", "")),
        "sha256": str(base.get("sha256", "")),
        "total_pages": int(base.get("total_pages", 0) or 0),
        "data_pages": int(base.get("data_pages", 0) or 0),
        "passphrase_required": bool(base.get("passphrase_required", False)),
        "scans": scan_rows_on_disk(folder, base.get("scans")),
    }


def _base(meta: dict[str, object]) -> dict[str, object]:
    wizard = meta.get("wizard")
    if isinstance(wizard, dict):
        return wizard
    return {}


def _store_wizard(
    stored: dict[str, object],
) -> Callable[[dict[str, object], dict[str, object]], dict[str, object]]:
    def change(meta: dict[str, object], _wizard: dict[str, object]) -> dict[str, object]:
        return {**meta, "wizard": stored}
    return change


def _wizard_change(
    revise: Callable[[dict[str, object]], dict[str, object]],
) -> Callable[[dict[str, object], dict[str, object]], dict[str, object]]:
    def change(meta: dict[str, object], wizard: dict[str, object]) -> dict[str, object]:
        return {**meta, "wizard": stored_wizard(revise(wizard))}
    return change


def _meta_change(
    job_id: str,
    folder: Path,
    revise: Callable[[dict[str, object], dict[str, object]], dict[str, object]],
) -> Callable[[JsonObject], JsonObject]:
    def change(meta: JsonObject) -> JsonObject:
        return revise(meta, _assemble(job_id, meta, folder))
    return change


def _scan_change(
    name: str,
    fields: dict[str, object],
) -> Callable[[dict[str, object], dict[str, object]], dict[str, object]]:
    def change(meta: dict[str, object], wizard: dict[str, object]) -> dict[str, object]:
        rows = rows_for_update(scan_rows(wizard), stored_scan_rows(meta), name)
        updated = {**wizard, "scans": upsert_scan(rows, name, fields)}
        return {**meta, "wizard": stored_wizard(updated)}
    return change
