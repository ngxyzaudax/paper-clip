import hashlib
import json
import shutil
import threading
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from common.config import PaperClipConfig
from common.data_store import DATA_ROOT
from serialization.encode.frame_payload import PreparedPayload
from serialization.encode.page_preview import layout_page, payload_page
from web.thumbs import jpeg_bytes
from workflows.encode_plan import build_plan, layout_plan
from workflows.encoding_form import EncodingFormPicks, resolve_encoding_form
from workflows.page_geometry_view import geometry_view
from workflows.picks_parse import picks_record

KEEP_PREVIEWS = 12
_lock = threading.Lock()
_cache: OrderedDict[str, "CachedEncode"] = OrderedDict()


@dataclass(frozen=True)
class CachedEncode:
    request: str
    file_id: str
    prepared: PreparedPayload | None
    config: PaperClipConfig
    plan: dict[str, object]


def previews_root() -> Path:
    return DATA_ROOT / ".thumbs" / "previews"


def render_preview(
    file_id: str | None,
    picks: EncodingFormPicks,
    page: int,
    passphrase: str | None,
    raw: bytes | None,
    filename: str,
) -> dict[str, object]:
    cached = _build(file_id, picks, passphrase, raw, filename)
    preview_id = _remember(cached)
    index = min(max(0, page), _last_page(cached))
    _write_page(previews_root() / preview_id / f"{index}.jpg", cached, index)
    return {
        "preview_id": preview_id,
        "plan": cached.plan,
        "geometry": geometry_view(cached.config),
        "page": index,
        "image": f"/api/media/preview/{preview_id}/{index}.jpg",
    }


def cached_encode(preview_id: str) -> CachedEncode | None:
    with _lock:
        return _cache.get(preview_id)


def matching_encode(preview_id: str, request: str) -> CachedEncode | None:
    """Return the cached preview only when it was built from the same file, picks, and passphrase."""
    cached = cached_encode(preview_id)
    return cached if cached is not None and cached.request == request and cached.prepared is not None else None


def request_key(file_id: str | None, picks: EncodingFormPicks, passphrase: str | None) -> str:
    """Return a digest identifying one preview request without retaining the passphrase."""
    body = json.dumps({"file": file_id or "", "picks": picks_record(picks), "secret": passphrase or ""}, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()


def preview_jpeg(preview_id: str, name: str) -> Path:
    path = previews_root() / preview_id / name
    if path.is_file():
        return path
    cached = cached_encode(preview_id)
    index = _page_index(name)
    if cached is None or index is None or index > _last_page(cached):
        raise FileNotFoundError(name)
    _write_page(path, cached, index)
    return path


def _write_page(path: Path, cached: CachedEncode, index: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.{uuid.uuid4().hex}.part")
    partial.write_bytes(jpeg_bytes(_page(cached, index)))
    partial.replace(path)


def _page_index(name: str) -> int | None:
    stem, _, suffix = name.partition(".")
    return int(stem) if suffix == "jpg" and stem.isdigit() else None


def _remember(cached: CachedEncode) -> str:
    preview_id = uuid.uuid4().hex
    with _lock:
        _cache[preview_id] = cached
        stale = [_cache.popitem(last=False)[0] for _ in range(max(0, len(_cache) - KEEP_PREVIEWS))]
    for old in stale:
        shutil.rmtree(previews_root() / old, ignore_errors=True)
    return preview_id


def _build(
    file_id: str | None,
    picks: EncodingFormPicks,
    passphrase: str | None,
    raw: bytes | None,
    filename: str,
) -> CachedEncode:
    request = request_key(file_id, picks, passphrase)
    if raw is None:
        config = resolve_encoding_form(picks)
        return CachedEncode(request, file_id or "", None, config, layout_plan(config, picks, 1))
    prepared, config, plan = build_plan(raw, filename, picks, passphrase)
    return CachedEncode(request, file_id or "", prepared, config, plan)


def _last_page(cached: CachedEncode) -> int:
    total = cached.plan.get("total_pages")
    return max(0, total - 1) if isinstance(total, int) else 0


def _page(cached: CachedEncode, page: int) -> Image.Image:
    if cached.prepared is None:
        return layout_page(cached.config)
    return payload_page(cached.prepared, cached.config, page)
