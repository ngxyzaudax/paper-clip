from serialization.decode.identify import ScanIdentity
from workflows.wizard_scans import scan_rows, upsert_scan


def apply_note(
    wizard: dict[str, object],
    identity: ScanIdentity | None,
    name: str,
    quality: dict[str, object],
    rows: list[dict[str, object]],
) -> dict[str, object]:
    fields = {**identity_fields(wizard, identity, name), **quality}
    return {**remember_document(wizard, identity), "scans": upsert_scan(rows, name, fields)}


def identity_fields(wizard: dict[str, object], identity: ScanIdentity | None, name: str) -> dict[str, object]:
    if identity is None:
        return {"status": "unidentified", "kept": True, "page_index": None}
    if len(identity.page_indices) > 1:
        return _two_pages(identity)
    if _foreign(wizard, identity):
        return _foreign_fields(identity)
    return _identified(wizard, identity, name)


def remember_document(wizard: dict[str, object], identity: ScanIdentity | None) -> dict[str, object]:
    if not _can_remember(wizard, identity) or identity is None:
        return wizard
    return {
        **wizard,
        "sha256": identity.sha256,
        "total_pages": identity.total_pages,
        "data_pages": identity.data_pages,
        "passphrase_required": bool(wizard["passphrase_required"] or identity.passphrase_required),
        **({"duplex": True} if identity.duplex else {}),
    }


def _two_pages(identity: ScanIdentity) -> dict[str, object]:
    return {
        "status": "two-pages",
        "kept": False,
        "page_index": identity.page_index,
        "page_indices": list(identity.page_indices),
    }


def _foreign(wizard: dict[str, object], identity: ScanIdentity) -> bool:
    return bool(wizard["sha256"]) and identity.sha256 != wizard["sha256"]


def _foreign_fields(identity: ScanIdentity) -> dict[str, object]:
    return {"status": "foreign", "kept": False, "page_index": identity.page_index, "sha256": identity.sha256}


def _identified(wizard: dict[str, object], identity: ScanIdentity, name: str) -> dict[str, object]:
    duplicate = _kept_page(wizard, identity.page_index, name)
    return {
        "status": "duplicate" if duplicate else "identified",
        "kept": not duplicate,
        "page_index": identity.page_index,
        "total_pages": identity.total_pages,
        "sha256": identity.sha256,
        "rotation": identity.rotation,
        "passphrase_required": identity.passphrase_required,
    }


def _kept_page(wizard: dict[str, object], page_index: int, name: str) -> bool:
    return any(_same_kept(item, page_index, name) for item in scan_rows(wizard))


def _same_kept(item: dict[str, object], page_index: int, name: str) -> bool:
    return bool(item.get("kept") and item.get("name") != name and item.get("page_index") == page_index)


def _can_remember(wizard: dict[str, object], identity: ScanIdentity | None) -> bool:
    if identity is None or len(identity.page_indices) != 1:
        return False
    current = wizard["sha256"]
    return not current or current == identity.sha256
