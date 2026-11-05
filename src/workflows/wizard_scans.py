from pathlib import Path

from workflows.scan_list import scan_paths


def scan_rows(wizard: dict[str, object]) -> list[dict[str, object]]:
    return copied_scans(wizard.get("scans"))


def stored_scan_rows(meta: dict[str, object]) -> list[dict[str, object]]:
    wizard = meta.get("wizard")
    if not isinstance(wizard, dict):
        return []
    return copied_scans(wizard.get("scans"))


def scan_rows_on_disk(folder: Path, stored: object) -> list[dict[str, object]]:
    known = {str(item.get("name")): item for item in copied_scans(stored)}
    return [named_scan(known.get(path.name), path.name) for path in scan_paths(folder)]


def rows_for_update(
    visible: list[dict[str, object]],
    stored: list[dict[str, object]],
    name: str,
) -> list[dict[str, object]]:
    if has_scan(visible, name):
        return visible
    return [*visible, *[item for item in stored if item.get("name") == name]]


def upsert_scan(
    scans: list[dict[str, object]],
    name: str,
    fields: dict[str, object],
) -> list[dict[str, object]]:
    if not has_scan(scans, name):
        return [*scans, {**fields, "name": name}]
    return [merged_scan(item, name, fields) for item in scans]


def page_index_of(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def copied_scans(stored: object) -> list[dict[str, object]]:
    if not isinstance(stored, list):
        return []
    return [dict(item) for item in stored if isinstance(item, dict)]


def named_scan(item: dict[str, object] | None, name: str) -> dict[str, object]:
    if item is None:
        return {"name": name}
    return {**item, "name": name}


def has_scan(scans: list[dict[str, object]], name: str) -> bool:
    return any(item.get("name") == name for item in scans)


def merged_scan(item: dict[str, object], name: str, fields: dict[str, object]) -> dict[str, object]:
    if item.get("name") != name:
        return item
    return {**item, **fields}
