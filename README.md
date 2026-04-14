<div align="center">

<!-- ─── Hero Badge ─────────────────────────────────────────────── -->

<br/>

<img src="https://img.shields.io/badge/%F0%9F%94%90_LoAuth-v2.0.0-00D4AA?style=for-the-badge" alt="LoAuth v2.0.0" />

<br/><br/>

<!-- ─── Title ──────────────────────────────────────────────────── -->

# LoAuth

**A secure, offline-first, AI-designed 2FA desktop authenticator.**

Your secrets never leave your machine — encrypted at rest with military-grade cryptography.

<br/>

<!-- ─── Badges Row 1 — Tech Stack ──────────────────────────────── -->

<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
&nbsp;
<img src="https://img.shields.io/badge/GUI-Flet-0175C2?style=flat-square&logo=flutter&logoColor=white" alt="Flet" />
&nbsp;
<img src="https://img.shields.io/badge/Encryption-AES--256--GCM-FF6F00?style=flat-square&logo=letsencrypt&logoColor=white" alt="AES-256-GCM" />
&nbsp;
<img src="https://img.shields.io/badge/KDF-Argon2id-8E24AA?style=flat-square&logo=keybase&logoColor=white" alt="Argon2id" />

<!-- ─── Badges Row 2 — Meta ────────────────────────────────────── -->

<img src="https://img.shields.io/badge/License-MIT-22C55E?style=flat-square" alt="MIT" />
&nbsp;
<img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-E5E7EB?style=flat-square&logo=apple&logoColor=black" alt="Platform" />
&nbsp;
<img src="https://img.shields.io/badge/Status-Stable-00D4AA?style=flat-square" alt="Stable" />
&nbsp;
<a href="https://t.me/VURA_Official"><img src="https://img.shields.io/badge/Telegram-VURA__Official-26A5E4?style=flat-square&logo=telegram&logoColor=white" alt="Telegram" /></a>

<br/><br/>

---

</div>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  OVERVIEW                                                      -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## Overview

**LoAuth** is a professional-grade, two-factor authentication (TOTP) desktop application engineered with **security as the #1 priority**.

Every secret key is encrypted locally with **AES-256-GCM**. The encryption key is derived from your master password using **Argon2id** — the most robust password-hashing algorithm available. **Nothing is ever stored in plaintext.**

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  FEATURES                                                      -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## Features

| &nbsp; | Feature | Description |
|:---:|---|---|
| **`01`** | **Modern Desktop GUI** | Dark-themed Flet app with card-based layout, smooth animations, and live countdown rings |
| **`02`** | **Interactive CLI** | Full terminal interface via `loauth --cli` — no GUI required |
| **`03`** | **Military Encryption** | AES-256-GCM authenticated encryption + Argon2id key derivation (100 MiB memory-hard) |
| **`04`** | **Zero-Knowledge Vault** | Master password is **never** stored — only a salt + encrypted verification token |
| **`05`** | **One-Click Copy** | Tap any account card to copy the current TOTP code to clipboard |
| **`06`** | **Live Countdown Ring** | Circular progress indicator shows seconds remaining until code refresh (30 s) |
| **`07`** | **Global Command** | Type `loauth` from anywhere in your terminal after installation |
| **`08`** | **Offline-First** | Zero network dependencies — everything stays on your machine |
| **`09`** | **Instant Vault Lock** | Lock button clears the encryption key from RAM immediately |

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  INSTALLATION                                                  -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## Installation

### Quick Install (Recommended)

```bash
git clone https://github.com/bx1-official/LoAuth.git
cd LoAuth
chmod +x install.sh
bash install.sh
```

The installer automatically:

1. Detects your Python 3 installation
2. Creates an isolated virtual environment (`.venv/`)
3. Installs all dependencies (`flet`, `pyotp`, `cryptography`, `argon2-cffi`)
4. Registers **`loauth`** as a global terminal command

### Manual Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py            # Launch GUI
python main.py --cli      # Launch CLI
```

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  USAGE                                                         -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## Usage

```bash
loauth              # Launch the desktop GUI  (default)
loauth --cli        # Launch the interactive CLI
loauth --version    # Print version
```

### First Launch

1. Run **`loauth`** — the vault setup screen appears.
2. Create a strong **master password**. This is the only password you'll need to remember.
3. The main dashboard is empty — tap **`+`** to add your first 2FA account.

### Adding an Account

1. Tap the **`+`** icon in the top-right corner.
2. Enter the **Account Name**, optional **Issuer**, and the **Secret Key** (Base32 string provided by your service).
3. Press **Save** — the account appears instantly with a live 6-digit code and countdown ring.

### Copying a Code

- **Click any card** or tap the **copy icon** — the TOTP code is copied to your clipboard.
- A toast notification confirms the action.

### Locking the Vault

- Tap the **lock icon** in the header to immediately lock the vault and **wipe the key from memory**.

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  PROJECT STRUCTURE                                             -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## Project Structure

```
LoAuth/
│
├── app/                    # Core application package
│   ├── __init__.py         #   Package metadata & version
│   ├── auth_engine.py      #   TOTP generation, countdown math
│   ├── crypto.py           #   AES-256-GCM + Argon2id primitives
│   ├── storage.py          #   SQLite vault with encrypted secrets
│   └── ui_helpers.py       #   Clipboard, colour palette, utilities
│
├── gui.py                  # Flet desktop GUI
├── main.py                 # CLI entry-point & argument parser
│
├── install.sh              # One-command macOS / Linux installer
├── requirements.txt        # Pinned Python dependencies
├── LICENSE                 # MIT License
├── .gitignore              # Keeps data/ and .venv/ out of VCS
└── README.md               # You are here
```

> **`data/`** is created automatically at first launch and contains your encrypted vault (`vault.db`). It is git-ignored by default.

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  SECURITY ARCHITECTURE                                         -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## Security Architecture

```
 Master Password (never stored)
         │
         ▼
 ┌───────────────────────────────────┐
 │  Argon2id                         │
 │  ├─ time_cost   = 2               │
 │  ├─ memory_cost = 100 MiB         │
 │  ├─ parallelism = 8               │
 │  └─ output      = 256-bit Key     │
 └───────────────┬───────────────────┘
                 │
                 ▼
 ┌───────────────────────────────────┐
 │  AES-256-GCM                      │
 │  ├─ 96-bit random nonce per op    │
 │  └─ Authenticated encryption      │
 └───────────────┬───────────────────┘
                 │
                 ▼
 ┌───────────────────────────────────┐
 │  SQLite — vault.db                │
 │  ┌─────────────────────────────┐  │
 │  │ metadata                    │  │
 │  │  ├ salt (16 bytes)          │  │
 │  │  └ verification_token       │  │
 │  ├─────────────────────────────┤  │
 │  │ accounts                    │  │
 │  │  ├ name, issuer (plain)     │  │
 │  │  └ encrypted_secret (blob)  │  │
 │  └─────────────────────────────┘  │
 └───────────────────────────────────┘
```

| Layer | Detail |
|---|---|
| **Salt** | 16-byte `os.urandom` value, stored in DB |
| **Verification Token** | The constant `LOAUTH_VAULT_OK` encrypted with the derived key — used to validate the password without storing it |
| **Encrypted Secrets** | Each account's TOTP secret is individually encrypted with a unique 12-byte nonce |
| **Key Lifetime** | The derived key exists only in RAM during the session and is wiped on lock / exit |

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  DEPENDENCIES                                                  -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| [`flet`](https://flet.dev) | >= 0.25 | Cross-platform desktop GUI framework |
| [`pyotp`](https://github.com/pyauth/pyotp) | >= 2.9 | TOTP / HOTP code generation (RFC 6238) |
| [`cryptography`](https://cryptography.io) | >= 42.0 | AES-256-GCM authenticated encryption |
| [`argon2-cffi`](https://argon2-cffi.readthedocs.io) | >= 23.1 | Argon2id password hashing & key derivation |

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  UNINSTALL                                                     -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## Uninstall

```bash
# Remove the global command
rm -f ~/.local/bin/loauth

# Remove the project directory
rm -rf /path/to/LoAuth
```

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  LICENSE                                                       -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--  COMMUNITY & CONTACT                                           -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## Community & Contact

<div align="center">

<a href="https://t.me/VURA_Official">
  <img src="https://img.shields.io/badge/Telegram-Join%20VURA__Official-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram" />
</a>

<br/><br/>

Have questions, feedback, or feature requests?<br/>
Join the official Telegram channel for discussions and updates.

</div>

<br/>

---

<div align="center">

<sub>Engineered with precision. Built to protect.</sub>

<br/><br/>

<img src="https://img.shields.io/badge/made%20with-%E2%9D%A4%EF%B8%8F-red?style=flat-square" />
&nbsp;
<img src="https://img.shields.io/badge/by-bx1-00D4AA?style=flat-square" />

</div>
