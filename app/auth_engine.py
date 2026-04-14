"""
Authentication Engine
======================
Generates TOTP (RFC 6238) and HOTP (RFC 4226) codes and exposes helpers
for computing the remaining seconds in the current time-step.
"""

import time
import math
import pyotp
import logging

log = logging.getLogger(__name__)

# Default TOTP interval (seconds)
TOTP_INTERVAL = 30


def generate_totp(secret: str) -> str:
    """
    Return a 6-digit TOTP code for the given Base32 *secret*.
    Returns ``"------"`` on any error so the UI always has something to show.
    """
    try:
        if not secret:
            raise ValueError("Empty secret.")
        clean = secret.replace(" ", "").strip().upper()
        return pyotp.TOTP(clean).now()
    except Exception:
        log.debug("TOTP generation failed for a secret.")
        return "------"


def time_remaining(interval: int = TOTP_INTERVAL) -> int:
    """Seconds remaining until the current TOTP code expires."""
    return interval - int(time.time() % interval)


def progress_fraction(interval: int = TOTP_INTERVAL) -> float:
    """
    Return a value in [0.0, 1.0] representing how much of the current
    time-step has elapsed (useful for progress-bar / ring widgets).
    """
    return (time.time() % interval) / interval


def validate_secret(secret: str) -> bool:
    """Return True if *secret* produces a valid 6-digit code."""
    code = generate_totp(secret)
    return code != "------"
