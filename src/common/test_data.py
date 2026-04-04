import hashlib
import logging
import secrets
from pathlib import Path

from common.config import PaperClipConfig
from common.page_layout import data_capacity_bytes

logger = logging.getLogger(__name__)

FILENAME_TEMPLATE = "testdata_XXXXXXXXXXXX.bin"
ZSTD_INCOMPRESSIBLE_OVERHEAD = 18
PAYLOAD_OVERHEAD = len(FILENAME_TEMPLATE.encode()) + ZSTD_INCOMPRESSIBLE_OVERHEAD


def usable_capacity(config: PaperClipConfig, pages: int = 1) -> int:
    return data_capacity_bytes(config) * pages - PAYLOAD_OVERHEAD


def generate_test_payload(config: PaperClipConfig, pages: int = 1) -> bytes:
    size = usable_capacity(config, pages)
    data = secrets.token_bytes(size)
    logger.info("Generated %d bytes of random test data (%d page(s))", size, pages)
    return data


def save_test_file(data: bytes, output_dir: Path) -> tuple[Path, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sha256 = hashlib.sha256(data).hexdigest()
    filename = f"testdata_{sha256[:12]}.bin"
    path = output_dir / filename
    path.write_bytes(data)
    (output_dir / f"{filename}.sha256").write_text(sha256)
    logger.info("Saved test file: %s (%d bytes, sha256=%s)", path, len(data), sha256)
    return path, sha256


def verify_against_original(decoded_path: Path, original_sha256: str) -> bool:
    decoded_hash = hashlib.sha256(decoded_path.read_bytes()).hexdigest()
    return decoded_hash == original_sha256
