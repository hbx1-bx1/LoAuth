"""
UI Helpers
===========
Shared utilities consumed by both the CLI and the Flet GUI:
clipboard management, color palette, and text formatting.
"""

import subprocess
import platform
import logging

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Colour palette  (shared between GUI theme and CLI ANSI codes)
# ---------------------------------------------------------------------------
class Colors:
    BG          = "#0D1117"
    SURFACE     = "#161B22"
    SURFACE2    = "#1C2333"
    PRIMARY     = "#00D4AA"
    PRIMARY_DIM = "#009E7E"
    ACCENT      = "#58A6FF"
    DANGER      = "#F85149"
    WARNING     = "#D29922"
    TEXT        = "#E6EDF3"
    TEXT_DIM    = "#8B949E"
    CARD_BG     = "#1A2030"
    CARD_BORDER = "#30363D"
    WHITE       = "#FFFFFF"


# ---------------------------------------------------------------------------
#  Clipboard (pure-Python, no pyperclip dependency)
# ---------------------------------------------------------------------------
def copy_to_clipboard(text: str) -> bool:
    """Copy *text* to the system clipboard. Returns True on success."""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(
                ["pbcopy"], stdin=subprocess.PIPE, close_fds=True
            ).communicate(text.encode("utf-8"))
        elif system == "Linux":
            # Try xclip first, fall back to xsel
            for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
                try:
                    subprocess.Popen(
                        cmd, stdin=subprocess.PIPE, close_fds=True
                    ).communicate(text.encode("utf-8"))
                    break
                except FileNotFoundError:
                    continue
            else:
                log.warning("No clipboard tool found (install xclip or xsel).")
                return False
        else:
            # Fallback for other systems
            log.warning("Clipboard not supported on %s.", system)
            return False
        return True
    except Exception:
        log.exception("Clipboard copy failed.")
        return False
