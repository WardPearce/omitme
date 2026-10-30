"""Shared Flet theme helpers."""

from __future__ import annotations

import flet as ft

from omitme.core.models import ItemStatus, ServiceMeta

BRAND = "#5865F2"


def configure_page(page: ft.Page) -> None:
    page.title = "OmitMe"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.theme = ft.Theme(color_scheme_seed=BRAND, use_material3=True)
    page.dark_theme = ft.Theme(color_scheme_seed=BRAND, use_material3=True)
    page.padding = 0
    page.window.width = 1280
    page.window.height = 820
    page.window.min_width = 760
    page.window.min_height = 560


def icon_for(meta: ServiceMeta) -> ft.IconData:
    return getattr(ft.Icons, meta.icon, ft.Icons.EXTENSION)


def status_style(status: ItemStatus) -> tuple[str, str, str]:
    """Return ``(label, background, foreground)`` for a status chip."""
    styles: dict[ItemStatus, tuple[str, str, str]] = {
        ItemStatus.PENDING: (
            "Pending",
            ft.Colors.SURFACE_CONTAINER_HIGH,
            ft.Colors.ON_SURFACE_VARIANT,
        ),
        ItemStatus.QUEUED: (
            "Queued",
            ft.Colors.SECONDARY_CONTAINER,
            ft.Colors.ON_SECONDARY_CONTAINER,
        ),
        ItemStatus.DRY_RUN: (
            "Would delete",
            ft.Colors.TERTIARY_CONTAINER,
            ft.Colors.ON_TERTIARY_CONTAINER,
        ),
        ItemStatus.DELETED: (
            "Deleted",
            ft.Colors.PRIMARY_CONTAINER,
            ft.Colors.ON_PRIMARY_CONTAINER,
        ),
        ItemStatus.SKIPPED: (
            "Skipped",
            ft.Colors.SURFACE_CONTAINER_HIGHEST,
            ft.Colors.ON_SURFACE_VARIANT,
        ),
        ItemStatus.FAILED: (
            "Failed",
            ft.Colors.ERROR_CONTAINER,
            ft.Colors.ON_ERROR_CONTAINER,
        ),
    }
    return styles[status]


def status_chip(status: ItemStatus) -> ft.Control:
    label, background, foreground = status_style(status)
    return ft.Container(
        content=ft.Text(label, size=10, color=foreground, weight=ft.FontWeight.W_500),
        bgcolor=background,
        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        border_radius=99,
    )
