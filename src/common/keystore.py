import json
import logging
from pathlib import Path

from common.encryption import decrypt

from common.data_store import DATA_ROOT

logger = logging.getLogger(__name__)

KEYSTORE_DIR = DATA_ROOT
KEYSTORE_FILE = KEYSTORE_DIR / "keys.json"


def _load_store() -> dict[str, str]:
    if not KEYSTORE_FILE.exists():
        return {}
    try:
        data = json.loads(KEYSTORE_FILE.read_text())
        return data.get("passwords", {})
    except (json.JSONDecodeError, KeyError):
        return {}


def _save_store(passwords: dict[str, str]) -> None:
    KEYSTORE_DIR.mkdir(parents=True, exist_ok=True)
    KEYSTORE_FILE.write_text(json.dumps({"passwords": passwords}, indent=2))
    KEYSTORE_FILE.chmod(0o600)


def save_password(label: str, passphrase: str) -> None:
    passwords = _load_store()
    passwords[label] = passphrase
    _save_store(passwords)
    logger.info("Saved password with label '%s'", label)


def list_passwords() -> list[str]:
    return list(_load_store().keys())


def load_password(label: str) -> str | None:
    return _load_store().get(label)


def try_stored_passwords(encrypted_blob: bytes) -> tuple[bytes, str] | None:
    passwords = _load_store()
    for label, passphrase in passwords.items():
        try:
            result = decrypt(encrypted_blob, passphrase)
            logger.info("Decrypted with stored password '%s'", label)
            return result, label
        except Exception:
            continue
    return None
