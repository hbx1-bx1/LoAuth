#!/usr/bin/env python3
"""
LoAuth — Flet Desktop GUI
===========================
A modern, dark-themed, professional 2FA authenticator desktop application
built with Flet.  Features:
  - Encrypted vault unlock / first-time setup
  - Live-updating 6-digit TOTP codes
  - Circular countdown timer per code (30 s)
  - Click-to-copy with toast notification
  - Add / delete accounts
  - Fuzzy search
"""

import time
import threading
import math
import flet as ft

from app import __version__
from app.storage import Vault
from app.auth_engine import generate_totp, time_remaining, progress_fraction, validate_secret, TOTP_INTERVAL
from app.ui_helpers import Colors, copy_to_clipboard


# ─── Constants ────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 460
WINDOW_HEIGHT = 720
TICK_MS       = 250          # UI refresh interval (milliseconds)


# ═══════════════════════════════════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════════════════════════════════
def start_gui():
    """Public entry-point called from main.py."""

    def app(page: ft.Page):
        # ── Page configuration ────────────────────────────────────────
        page.title = f"LoAuth v{__version__}"
        page.bgcolor = Colors.BG
        page.window.width = WINDOW_WIDTH
        page.window.height = WINDOW_HEIGHT
        page.window.resizable = False
        page.padding = 0
        page.spacing = 0
        page.fonts = {
            "mono": "RobotoMono",
        }

        # ── Shared state ──────────────────────────────────────────────
        vault = Vault()
        session: dict = {"key": None, "running": True}

        # ────────────────────────────────────────────────────────────
        #  Toast helper
        # ────────────────────────────────────────────────────────────
        def show_toast(msg: str, color: str = Colors.PRIMARY):
            sb = ft.SnackBar(
                content=ft.Text(msg, color=Colors.WHITE, size=14, weight=ft.FontWeight.W_500),
                bgcolor=color,
                duration=2000,
            )
            page.overlay.append(sb)
            sb.open = True
            page.update()

        # ────────────────────────────────────────────────────────────
        #  AUTH SCREEN  (login / first-time setup)
        # ────────────────────────────────────────────────────────────
        def build_auth_screen():
            is_new = not vault.is_setup()

            pw_field = ft.TextField(
                label="Master Password",
                password=True,
                can_reveal_password=True,
                border_color=Colors.CARD_BORDER,
                focused_border_color=Colors.PRIMARY,
                cursor_color=Colors.PRIMARY,
                text_style=ft.TextStyle(color=Colors.TEXT),
                label_style=ft.TextStyle(color=Colors.TEXT_DIM),
                width=320,
            )
            confirm_field = ft.TextField(
                label="Confirm Password",
                password=True,
                can_reveal_password=True,
                border_color=Colors.CARD_BORDER,
                focused_border_color=Colors.PRIMARY,
                cursor_color=Colors.PRIMARY,
                text_style=ft.TextStyle(color=Colors.TEXT),
                label_style=ft.TextStyle(color=Colors.TEXT_DIM),
                width=320,
                visible=is_new,
            )
            error_text = ft.Text("", color=Colors.DANGER, size=13)

            def on_submit(e):
                pw = pw_field.value or ""
                if is_new:
                    pw2 = confirm_field.value or ""
                    if not pw or not pw2:
                        error_text.value = "Please fill in both fields."
                        page.update()
                        return
                    if pw != pw2:
                        error_text.value = "Passwords do not match."
                        page.update()
                        return
                    try:
                        session["key"] = vault.setup_password(pw)
                    except Exception as exc:
                        error_text.value = str(exc)
                        page.update()
                        return
                else:
                    if not pw:
                        error_text.value = "Enter your master password."
                        page.update()
                        return
                    try:
                        session["key"] = vault.unlock(pw)
                    except ValueError as exc:
                        error_text.value = str(exc)
                        page.update()
                        return

                show_main_screen()

            pw_field.on_submit = on_submit
            confirm_field.on_submit = on_submit

            submit_btn = ft.Button(
                content="Create Vault" if is_new else "Unlock",
                bgcolor=Colors.PRIMARY,
                color=Colors.BG,
                width=320,
                height=48,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                on_click=on_submit,
            )

            shield_icon = ft.Icon(ft.Icons.SHIELD_OUTLINED, size=64, color=Colors.PRIMARY)
            title = ft.Text(
                "LoAuth",
                size=36,
                weight=ft.FontWeight.BOLD,
                color=Colors.PRIMARY,
            )
            subtitle = ft.Text(
                "First-Time Setup" if is_new else "Welcome Back",
                size=14,
                color=Colors.TEXT_DIM,
            )

            auth_col = ft.Column(
                [
                    ft.Container(height=60),
                    shield_icon,
                    title,
                    subtitle,
                    ft.Container(height=20),
                    pw_field,
                    confirm_field,
                    error_text,
                    ft.Container(height=8),
                    submit_btn,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.START,
                spacing=8,
            )

            page.controls.clear()
            page.add(
                ft.Container(
                    content=auth_col,
                    expand=True,
                    bgcolor=Colors.BG,
                    padding=20,
                )
            )
            page.update()

        # ────────────────────────────────────────────────────────────
        #  MAIN SCREEN  (accounts list)
        # ────────────────────────────────────────────────────────────
        accounts_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        search_ref = ft.Ref[ft.TextField]()
        timer_widgets: list = []   # list of dicts with refs for live updating

        def _build_account_card(acc: dict) -> ft.Container:
            """Build a single account card with code + countdown ring."""
            code_text = ft.Text(
                generate_totp(acc["secret"]),
                size=28,
                weight=ft.FontWeight.BOLD,
                color=Colors.PRIMARY,
                font_family="mono",
                selectable=False,
            )
            remaining = time_remaining()
            frac = progress_fraction()
            ring = ft.ProgressRing(
                value=1.0 - frac,
                stroke_width=3,
                width=38,
                height=38,
                color=Colors.PRIMARY if remaining > 5 else Colors.DANGER,
                bgcolor=Colors.CARD_BORDER,
            )
            timer_label = ft.Text(
                f"{remaining}s",
                size=11,
                color=Colors.TEXT_DIM,
                text_align=ft.TextAlign.CENTER,
            )
            timer_stack = ft.Stack(
                [
                    ring,
                    ft.Container(
                        content=timer_label,
                        alignment=ft.Alignment(0, 0),
                        width=38,
                        height=38,
                    ),
                ],
                width=38,
                height=38,
            )

            # Keep refs for live-update loop
            timer_widgets.append({
                "secret": acc["secret"],
                "code": code_text,
                "ring": ring,
                "label": timer_label,
            })

            issuer = acc.get("issuer", "")
            display_name = acc["name"]
            if issuer:
                display_name = f"{issuer}  ·  {acc['name']}"

            name_text = ft.Text(
                display_name,
                size=13,
                color=Colors.TEXT_DIM,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
                width=220,
            )

            def on_copy(e, secret=acc["secret"]):
                code = generate_totp(secret)
                if code != "------":
                    copy_to_clipboard(code)
                    show_toast("Copied to clipboard!")

            copy_btn = ft.IconButton(
                icon=ft.Icons.CONTENT_COPY_ROUNDED,
                icon_color=Colors.TEXT_DIM,
                icon_size=18,
                tooltip="Copy code",
                on_click=on_copy,
                style=ft.ButtonStyle(
                    overlay_color={ft.ControlState.HOVERED: Colors.SURFACE2},
                ),
            )

            def on_delete(e, aid=acc["id"]):
                vault.delete_account(aid)
                refresh_accounts()

            delete_btn = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                icon_color=Colors.DANGER,
                icon_size=18,
                tooltip="Delete account",
                on_click=on_delete,
                style=ft.ButtonStyle(
                    overlay_color={ft.ControlState.HOVERED: "#2D1518"},
                ),
            )

            card = ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Column(
                                    [name_text, code_text],
                                    spacing=2,
                                    expand=True,
                                ),
                                timer_stack,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Row(
                            [copy_btn, delete_btn],
                            alignment=ft.MainAxisAlignment.END,
                            spacing=0,
                        ),
                    ],
                    spacing=0,
                ),
                bgcolor=Colors.CARD_BG,
                border=ft.Border.all(1, Colors.CARD_BORDER),
                border_radius=14,
                padding=ft.Padding.only(left=18, right=10, top=14, bottom=6),
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                ink=True,
                on_click=on_copy,
            )
            return card

        def refresh_accounts(query: str = ""):
            """Reload account list from vault and rebuild cards."""
            timer_widgets.clear()
            accounts_column.controls.clear()
            if session["key"] is None:
                return

            accounts = vault.get_accounts(session["key"])
            if query:
                q = query.lower()
                accounts = [
                    a for a in accounts
                    if q in a["name"].lower() or q in (a.get("issuer") or "").lower()
                ]

            if not accounts:
                accounts_column.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(ft.Icons.LOCK_OUTLINE_ROUNDED, size=48, color=Colors.TEXT_DIM),
                                ft.Text(
                                    "No accounts yet" if not query else "No results",
                                    size=15,
                                    color=Colors.TEXT_DIM,
                                ),
                                ft.Text(
                                    "Tap  +  to add your first account" if not query else "",
                                    size=12,
                                    color=Colors.TEXT_DIM,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        alignment=ft.Alignment(0, 0),
                        padding=ft.Padding.only(top=80),
                    )
                )
            else:
                for acc in accounts:
                    accounts_column.controls.append(_build_account_card(acc))

            page.update()

        def on_search_change(e):
            refresh_accounts(e.control.value)

        # ── Add-account bottom sheet ──────────────────────────────
        def show_add_dialog(e):
            name_f = ft.TextField(
                label="Account Name",
                border_color=Colors.CARD_BORDER,
                focused_border_color=Colors.PRIMARY,
                cursor_color=Colors.PRIMARY,
                text_style=ft.TextStyle(color=Colors.TEXT),
                label_style=ft.TextStyle(color=Colors.TEXT_DIM),
            )
            issuer_f = ft.TextField(
                label="Issuer (optional)",
                border_color=Colors.CARD_BORDER,
                focused_border_color=Colors.PRIMARY,
                cursor_color=Colors.PRIMARY,
                text_style=ft.TextStyle(color=Colors.TEXT),
                label_style=ft.TextStyle(color=Colors.TEXT_DIM),
            )
            secret_f = ft.TextField(
                label="Secret Key (Base32)",
                border_color=Colors.CARD_BORDER,
                focused_border_color=Colors.PRIMARY,
                cursor_color=Colors.PRIMARY,
                text_style=ft.TextStyle(color=Colors.TEXT),
                label_style=ft.TextStyle(color=Colors.TEXT_DIM),
            )
            err = ft.Text("", color=Colors.DANGER, size=13)

            def save(ev):
                n = (name_f.value or "").strip()
                i = (issuer_f.value or "").strip()
                s = (secret_f.value or "").strip()
                if not n or not s:
                    err.value = "Name and secret key are required."
                    page.update()
                    return
                if not validate_secret(s):
                    err.value = "Invalid secret key (must be Base32)."
                    page.update()
                    return
                vault.add_account(session["key"], n, i, s)
                bs.open = False
                page.update()
                refresh_accounts(search_ref.current.value if search_ref.current else "")
                show_toast("Account added!")

            bs = ft.BottomSheet(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                content=ft.Container(
                                    width=40, height=4,
                                    bgcolor=Colors.TEXT_DIM,
                                    border_radius=2,
                                ),
                                alignment=ft.Alignment(0, 0),
                                padding=ft.Padding.only(top=12, bottom=8),
                            ),
                            ft.Text(
                                "Add Account",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT,
                            ),
                            ft.Container(height=4),
                            name_f,
                            issuer_f,
                            secret_f,
                            err,
                            ft.Container(height=4),
                            ft.Button(
                                content="Save",
                                bgcolor=Colors.PRIMARY,
                                color=Colors.BG,
                                width=400,
                                height=48,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                                on_click=save,
                            ),
                            ft.Container(height=12),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    bgcolor=Colors.SURFACE,
                    border_radius=ft.BorderRadius.only(top_left=20, top_right=20),
                    padding=ft.Padding.symmetric(horizontal=24, vertical=0),
                ),
                bgcolor="#00000000",
            )
            page.overlay.append(bs)
            bs.open = True
            page.update()

        # ── Lock / logout ─────────────────────────────────────────
        def on_lock(e):
            session["key"] = None
            session["running"] = False
            build_auth_screen()

        # ── Build main layout ─────────────────────────────────────
        def show_main_screen():
            session["running"] = True
            page.controls.clear()

            header = ft.Container(
                content=ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.SHIELD_OUTLINED, color=Colors.PRIMARY, size=24),
                                ft.Text(
                                    "LoAuth",
                                    size=22,
                                    weight=ft.FontWeight.BOLD,
                                    color=Colors.TEXT,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
                                    icon_color=Colors.TEXT_DIM,
                                    icon_size=20,
                                    tooltip="Lock vault",
                                    on_click=on_lock,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED,
                                    icon_color=Colors.PRIMARY,
                                    icon_size=26,
                                    tooltip="Add account",
                                    on_click=show_add_dialog,
                                ),
                            ],
                            spacing=0,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                bgcolor=Colors.SURFACE,
                padding=ft.Padding.symmetric(horizontal=18, vertical=10),
            )

            search_bar = ft.Container(
                content=ft.TextField(
                    ref=search_ref,
                    hint_text="Search accounts…",
                    hint_style=ft.TextStyle(color=Colors.TEXT_DIM, size=14),
                    text_style=ft.TextStyle(color=Colors.TEXT, size=14),
                    border_color=Colors.CARD_BORDER,
                    focused_border_color=Colors.PRIMARY,
                    cursor_color=Colors.PRIMARY,
                    prefix_icon=ft.Icons.SEARCH_ROUNDED,
                    border_radius=12,
                    content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    on_change=on_search_change,
                ),
                padding=ft.Padding.symmetric(horizontal=18, vertical=6),
            )

            version_label = ft.Container(
                content=ft.Text(
                    f"v{__version__}  ·  AES-256-GCM  ·  Argon2id",
                    size=11,
                    color=Colors.TEXT_DIM,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding.only(bottom=10, top=4),
            )

            page.add(
                ft.Container(
                    content=ft.Column(
                        [
                            header,
                            search_bar,
                            ft.Container(
                                content=accounts_column,
                                expand=True,
                                padding=ft.Padding.symmetric(horizontal=14),
                            ),
                            version_label,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    expand=True,
                    bgcolor=Colors.BG,
                )
            )
            page.update()

            refresh_accounts()
            _start_live_update()

        # ────────────────────────────────────────────────────────────
        #  Live-update loop (runs in a background thread)
        # ────────────────────────────────────────────────────────────
        def _start_live_update():
            def loop():
                while session.get("running"):
                    try:
                        rem = time_remaining()
                        frac = progress_fraction()
                        ring_val = 1.0 - frac
                        color = Colors.PRIMARY if rem > 5 else Colors.DANGER
                        for w in timer_widgets:
                            new_code = generate_totp(w["secret"])
                            w["code"].value = new_code
                            w["ring"].value = ring_val
                            w["ring"].color = color
                            w["label"].value = f"{rem}s"
                            w["label"].color = color if rem <= 5 else Colors.TEXT_DIM
                        page.update()
                    except Exception:
                        pass
                    time.sleep(TICK_MS / 1000.0)

            t = threading.Thread(target=loop, daemon=True)
            t.start()

        # ── Start ─────────────────────────────────────────────────
        build_auth_screen()

    ft.run(app)


# Allow running directly: python gui.py
if __name__ == "__main__":
    start_gui()
