"""Dialogs used by the preview and the dry-run action bar."""

from __future__ import annotations

import flet as ft

from omitme.core.models import DeletableItem


def show_message_preview(page: ft.Page, item: DeletableItem) -> None:
    initials = "".join(part[0] for part in item.author.split()[:2]).upper() or "?"

    details = [
        ft.Row(
            [
                ft.CircleAvatar(
                    content=ft.Text(initials, size=13, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    color=ft.Colors.ON_PRIMARY_CONTAINER,
                    radius=18,
                ),
                ft.Column(
                    [
                        ft.Text(item.author, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"#{item.channel} · {item.created_at:%d %b %Y, %H:%M}",
                            size=11,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    spacing=0,
                    tight=True,
                ),
            ],
            spacing=10,
        ),
        ft.Divider(height=1),
        ft.Text(item.content, selectable=True),
    ]

    if item.attachments:
        details.append(
            ft.Row(
                [
                    ft.Icon(ft.Icons.ATTACH_FILE, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(
                        f"{item.attachments} attachment{'s' if item.attachments != 1 else ''}",
                        size=11,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=4,
            )
        )

    dialog = ft.AlertDialog(
        title=ft.Text("Message preview"),
        content=ft.Container(
            width=560,
            content=ft.Column(details, spacing=12, tight=True, scroll=ft.ScrollMode.AUTO),
        ),
        actions=[
            ft.TextButton("Close", on_click=lambda: page.pop_dialog()),
        ],
    )
    page.show_dialog(dialog)


def show_real_deletion_unavailable(page: ft.Page) -> None:
    dialog = ft.AlertDialog(
        title=ft.Text("Real deletion is not implemented"),
        content=ft.Text(
            "OmitMe 2.0 is currently a UI skeleton. The Delete action only "
            "simulates a dry run — no service data is touched."
        ),
        actions=[
            ft.FilledButton("Got it", on_click=lambda: page.pop_dialog()),
        ],
    )
    page.show_dialog(dialog)
