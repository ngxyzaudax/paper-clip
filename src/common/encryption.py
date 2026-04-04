import os
import struct

from argon2.low_level import Type, hash_secret_raw

SALT_SIZE = 16
NONCE_SIZE = 12
TAG_SIZE = 16
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536
ARGON2_PARALLELISM = 4
KEY_SIZE = 32


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    return hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=KEY_SIZE,
        type=Type.ID,
    )


def _aes_gcm_encrypt(key: bytes, nonce: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aead = AESGCM(key)
    ciphertext_with_tag = aead.encrypt(nonce, plaintext, None)
    return ciphertext_with_tag[:-TAG_SIZE], ciphertext_with_tag[-TAG_SIZE:]


def _aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aead = AESGCM(key)
    return aead.decrypt(nonce, ciphertext + tag, None)


def encrypt(data: bytes, passphrase: str) -> bytes:
    """Returns: salt(16) + nonce(12) + ciphertext + tag(16)"""
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(passphrase, salt)
    ct, tag = _aes_gcm_encrypt(key, nonce, data)
    return salt + nonce + ct + tag


def decrypt(blob: bytes, passphrase: str) -> bytes:
    salt = blob[:SALT_SIZE]
    nonce = blob[SALT_SIZE : SALT_SIZE + NONCE_SIZE]
    ct_and_tag = blob[SALT_SIZE + NONCE_SIZE:]
    ciphertext = ct_and_tag[:-TAG_SIZE]
    tag = ct_and_tag[-TAG_SIZE:]
    key = _derive_key(passphrase, salt)
    return _aes_gcm_decrypt(key, nonce, ciphertext, tag)


ENCRYPTION_OVERHEAD = SALT_SIZE + NONCE_SIZE + TAG_SIZE
