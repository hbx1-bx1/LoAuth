"""
Cryptography Module
====================
Handles key derivation (Argon2id) and authenticated encryption (AES-256-GCM).
Secret keys are NEVER stored in plaintext — every value at rest is encrypted
with a key derived from the user's master password.
"""

import os
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from argon2.low_level import hash_secret_raw, Type

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  Constants
# ---------------------------------------------------------------------------
SALT_LENGTH = 16        # bytes
NONCE_LENGTH = 12       # bytes  (96-bit, recommended for AES-GCM)
KEY_LENGTH = 32         # bytes  (256-bit)
ARGON2_TIME_COST = 2
ARGON2_MEMORY_COST = 102_400   # ~100 MiB
ARGON2_PARALLELISM = 8
VERIFICATION_PLAINTEXT = "LOAUTH_VAULT_OK"


class CryptoManager:
    """Low-level cryptographic primitives used by the storage layer."""

    # ------------------------------------------------------------------
    #  Key derivation
    # ------------------------------------------------------------------
    @staticmethod
    def generate_salt() -> bytes:
        """Return a cryptographically-random salt."""
        return os.urandom(SALT_LENGTH)

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Derive a 256-bit key from *password* + *salt* using Argon2id.
        Argon2id is resistant to both side-channel and GPU-based attacks.
        """
        try:
            return hash_secret_raw(
                secret=password.encode("utf-8"),
                salt=salt,
                time_cost=ARGON2_TIME_COST,
                memory_cost=ARGON2_MEMORY_COST,
                parallelism=ARGON2_PARALLELISM,
                hash_len=KEY_LENGTH,
                type=Type.ID,
            )
        except Exception:
            log.exception("Key derivation failed.")
            raise ValueError("Key derivation error.")

    # ------------------------------------------------------------------
    #  Authenticated encryption  (AES-256-GCM)
    # ------------------------------------------------------------------
    @staticmethod
    def encrypt(key: bytes, plaintext: str) -> bytes:
        """Encrypt *plaintext* → nonce‖ciphertext (bytes)."""
        try:
            nonce = os.urandom(NONCE_LENGTH)
            ct = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
            return nonce + ct
        except Exception:
            log.exception("Encryption failed.")
            raise ValueError("Encryption error.")

    @staticmethod
    def decrypt(key: bytes, blob: bytes) -> str:
        """Decrypt nonce‖ciphertext → plaintext string."""
        try:
            nonce, ct = blob[:NONCE_LENGTH], blob[NONCE_LENGTH:]
            return AESGCM(key).decrypt(nonce, ct, None).decode("utf-8")
        except InvalidTag:
            raise ValueError("Wrong password or corrupted data.")
        except Exception:
            log.exception("Decryption failed.")
            raise ValueError("Decryption error.")
