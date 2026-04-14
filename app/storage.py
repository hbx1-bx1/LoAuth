"""
Secured Storage
================
SQLite-backed vault that stores accounts with AES-256-GCM encrypted secrets.
The master password is never persisted — only a salt and a verification token
are saved so the app can confirm the password on login.
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional

from .crypto import CryptoManager, VERIFICATION_PLAINTEXT

log = logging.getLogger(__name__)

# Default data directory (next to the project root)
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DB_FILE = _DATA_DIR / "vault.db"


class Vault:
    """Encrypted account vault backed by SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = Path(db_path) if db_path else _DB_FILE
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._ensure_schema()

    # ------------------------------------------------------------------
    #  Schema
    # ------------------------------------------------------------------
    def _ensure_schema(self):
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    id                  INTEGER PRIMARY KEY,
                    salt                BLOB    NOT NULL,
                    verification_token  BLOB    NOT NULL
                )
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    name             TEXT    NOT NULL,
                    issuer           TEXT    DEFAULT '',
                    encrypted_secret BLOB    NOT NULL
                )
            """)

    # ------------------------------------------------------------------
    #  Master password management
    # ------------------------------------------------------------------
    def is_setup(self) -> bool:
        """Has a master password been configured yet?"""
        cur = self._conn.execute("SELECT COUNT(*) FROM metadata")
        return cur.fetchone()[0] > 0

    def setup_password(self, password: str) -> bytes:
        """First-time setup — derive key, store salt + verification token.
        Returns the derived encryption key for the current session."""
        if self.is_setup():
            raise ValueError("Master password already configured.")
        salt = CryptoManager.generate_salt()
        key = CryptoManager.derive_key(password, salt)
        token = CryptoManager.encrypt(key, VERIFICATION_PLAINTEXT)
        with self._conn:
            self._conn.execute(
                "INSERT INTO metadata (id, salt, verification_token) VALUES (1, ?, ?)",
                (salt, token),
            )
        return key

    def unlock(self, password: str) -> bytes:
        """Verify *password* and return the derived key, or raise ValueError."""
        row = self._conn.execute(
            "SELECT salt, verification_token FROM metadata WHERE id = 1"
        ).fetchone()
        if not row:
            raise ValueError("Vault not initialised.")
        salt, token = row
        key = CryptoManager.derive_key(password, salt)
        plain = CryptoManager.decrypt(key, token)
        if plain != VERIFICATION_PLAINTEXT:
            raise ValueError("Wrong password.")
        return key

    # ------------------------------------------------------------------
    #  Account CRUD
    # ------------------------------------------------------------------
    def add_account(self, key: bytes, name: str, issuer: str, secret: str) -> int:
        """Encrypt *secret* and store the account. Returns the new row id."""
        blob = CryptoManager.encrypt(key, secret)
        with self._conn:
            cur = self._conn.execute(
                "INSERT INTO accounts (name, issuer, encrypted_secret) VALUES (?, ?, ?)",
                (name, issuer, blob),
            )
            return cur.lastrowid

    def get_accounts(self, key: bytes) -> List[Dict]:
        """Return all accounts with their secrets decrypted in-memory."""
        rows = self._conn.execute(
            "SELECT id, name, issuer, encrypted_secret FROM accounts"
        ).fetchall()
        accounts: List[Dict] = []
        for rid, name, issuer, blob in rows:
            try:
                secret = CryptoManager.decrypt(key, blob)
                accounts.append(
                    {"id": rid, "name": name, "issuer": issuer, "secret": secret}
                )
            except ValueError:
                log.warning("Could not decrypt account %s — skipping.", rid)
        return accounts

    def delete_account(self, account_id: int):
        with self._conn:
            self._conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))

    def close(self):
        self._conn.close()
