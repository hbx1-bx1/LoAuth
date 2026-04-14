#!/usr/bin/env python3
"""
LoAuth — CLI entry-point
=========================
Run ``loauth`` (or ``python main.py``) to launch the desktop GUI.
Use ``loauth --cli`` to start the interactive terminal interface.
"""

import sys
import argparse
import logging

from app import __version__

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s  %(name)s: %(message)s",
)

# ── ANSI helpers ──────────────────────────────────────────────────────────
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

BANNER = f"""{CYAN}{BOLD}
  ██╗      ██████╗  █████╗ ██╗   ██╗████████╗██╗  ██╗
  ██║     ██╔═══██╗██╔══██╗██║   ██║╚══██╔══╝██║  ██║
  ██║     ██║   ██║███████║██║   ██║   ██║   ███████║
  ██║     ██║   ██║██╔══██║██║   ██║   ██║   ██╔══██║
  ███████╗╚██████╔╝██║  ██║╚██████╔╝   ██║   ██║  ██║
  ╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝
{RESET}{CYAN}  Secure 2FA Authenticator  v{__version__}{RESET}
"""


# ── CLI interactive mode ──────────────────────────────────────────────────
def run_cli():
    """Full interactive terminal authenticator."""
    from app.storage import Vault
    from app.auth_engine import generate_totp, validate_secret

    print(BANNER)
    vault = Vault()

    # -- master password flow --
    if not vault.is_setup():
        print(f"{YELLOW}Welcome to LoAuth!  Set up your master password.{RESET}")
        pw  = input("  Create master password: ")
        pw2 = input("  Confirm password:       ")
        if pw != pw2:
            print(f"{RED}Passwords do not match.{RESET}")
            sys.exit(1)
        key = vault.setup_password(pw)
        print(f"{GREEN}Vault created successfully.{RESET}\n")
    else:
        pw = input("  Master password: ")
        try:
            key = vault.unlock(pw)
        except ValueError as exc:
            print(f"{RED}{exc}{RESET}")
            sys.exit(1)
        print(f"{GREEN}Unlocked.{RESET}\n")

    # -- main menu loop --
    while True:
        print(f"{CYAN}{'─' * 40}")
        print(f"  1  View accounts & codes")
        print(f"  2  Add account (manual)")
        print(f"  3  Delete account")
        print(f"  4  Exit")
        print(f"{'─' * 40}{RESET}")
        choice = input("  Choose [1-4]: ").strip()

        if choice == "1":
            accounts = vault.get_accounts(key)
            if not accounts:
                print(f"  {YELLOW}No accounts yet.{RESET}")
                continue
            for a in accounts:
                code = generate_totp(a["secret"])
                issuer = f" ({a['issuer']})" if a["issuer"] else ""
                print(f"  [{a['id']}] {a['name']}{issuer}  →  {GREEN}{code}{RESET}")

        elif choice == "2":
            name   = input("  Account name: ").strip()
            issuer = input("  Issuer (optional): ").strip()
            secret = input("  Secret key: ").strip()
            if not name or not secret:
                print(f"  {RED}Name and secret are required.{RESET}")
                continue
            if not validate_secret(secret):
                print(f"  {RED}Invalid secret key.{RESET}")
                continue
            vault.add_account(key, name, issuer, secret)
            print(f"  {GREEN}Account added.{RESET}")

        elif choice == "3":
            aid = input("  Account ID to delete: ").strip()
            if aid.isdigit():
                vault.delete_account(int(aid))
                print(f"  {GREEN}Deleted.{RESET}")
            else:
                print(f"  {RED}Invalid ID.{RESET}")

        elif choice == "4":
            key = None
            print(f"{YELLOW}Goodbye.{RESET}")
            break

        else:
            print(f"  {RED}Invalid option.{RESET}")

    vault.close()


# ── Entry-point ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="loauth",
        description="LoAuth — Secure 2FA/TOTP Authenticator",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Launch the interactive terminal interface instead of the GUI.",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"LoAuth {__version__}",
    )
    args = parser.parse_args()

    try:
        if args.cli:
            run_cli()
        else:
            from gui import start_gui
            start_gui()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted — exiting safely.{RESET}")
        sys.exit(0)
    except Exception as exc:
        logging.error("Fatal: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
