"""Application shell: wires state, services and the three UI regions."""

from __future__ import annotations

import flet as ft

from omitme.core.state import AppState
from omitme.services import create_services
from omitme.ui.filter_panel import FilterPanel
from omitme.ui.message_list import MessageList
from omitme.ui.service_rail import build_service_rail
from omitme.ui.theme import BRAND, configure_page


class AppView:
    """Owns the page layout and coordinates the UI components."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.state = AppState(create_services())
        self.narrow = False

        self.message_list = MessageList(self)
        self.rail = build_service_rail(self)
        self.panel_slot = ft.Container(width=360)
        self.filter_button = ft.IconButton(
            icon=ft.Icons.FILTER_ALT_OUTLINED,
            tooltip="Open filters",
            on_click=self._open_filters,
            visible=False,
        )
        self.theme_button = ft.IconButton(
            icon=ft.Icons.DARK_MODE_OUTLINED,
            tooltip="Toggle theme",
            on_click=self._toggle_theme,
        )

        self.page.appbar = self._build_appbar()
        self.page.on_resize = self._on_resize

        self.layout = ft.Row(
            [
                self.rail,
                ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE_VARIANT),
                self.message_list.root,
                self.panel_slot,
            ],
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        self._update_responsive()
        self.rebuild_panel(update=False)

    # ------------------------------------------------------------------
    # Construction / lifecycle
    # ------------------------------------------------------------------
    def build(self) -> ft.Control:
        return self.layout

    async def start(self) -> None:
        if self.state.services:
            await self._select_service(self.state.services[0])
        else:
            self.refresh_ui()

    def _build_appbar(self) -> ft.AppBar:
        return ft.AppBar(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.SHIELD_OUTLINED, size=20, color=ft.Colors.PRIMARY),
                    ft.Text("OmitMe", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(
                            "v2 preview",
                            size=9,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                        border_radius=99,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            elevation=0,
            actions=[
                self.filter_button,
                self.theme_button,
                ft.Container(width=8),
            ],
        )

    # ------------------------------------------------------------------
    # Service switching
    # ------------------------------------------------------------------
    def on_service_change(self, event) -> None:
        index = event.control.selected_index
        if index is None or not (0 <= index < len(self.state.services)):
            return
        service = self.state.services[index]
        if service is not self.state.active:
            self.page.run_task(self._select_service, service)

    async def _select_service(self, service, *, force: bool = False) -> None:
        if not force and service is self.state.active and not self.state.error:
            return

        self.state.set_service(service)
        self.state.loading = True
        if service in self.state.services:
            self.rail.selected_index = self.state.services.index(service)
        self.refresh_ui()

        try:
            await service.connect()
            await self.state.load_options()
            await self.state.refresh()
        except Exception as exc:  # noqa: BLE001 - shown in the UI
            self.state.items = []
            self.state.selected.clear()
            self.state.loading = False
            self.state.error = str(exc) or exc.__class__.__name__

        self.refresh_ui()

    async def reload(self) -> None:
        if self.state.active is None:
            return
        self.state.loading = True
        self.state.error = None
        self.message_list.refresh()
        self.page.update()

        await self.state.refresh()
        self.message_list.refresh()
        self.page.update()

    async def retry(self) -> None:
        if self.state.active is not None:
            await self._select_service(self.state.active, force=True)

    async def apply_filters(self) -> None:
        state = self.state
        service = state.active
        if service is None:
            return

        if not service.connected:
            try:
                await service.connect()
                await state.load_options()
            except Exception as exc:  # noqa: BLE001 - shown in the UI
                state.items = []
                state.selected.clear()
                state.loading = False
                state.error = str(exc) or exc.__class__.__name__
                self.message_list.refresh()
                self.page.update()
                return

        await state.refresh()
        self.message_list.refresh()
        self.page.update()

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    def refresh_ui(self) -> None:
        self.message_list.refresh()
        self.rebuild_panel(update=False)
        self.page.update()

    def rebuild_panel(self, *, update: bool = True) -> None:
        self.panel_slot.content = FilterPanel(self).build()
        if update:
            self.page.update()

    def _update_responsive(self) -> None:
        width = self.page.width or 1200
        self.narrow = width < 980
        self.panel_slot.visible = not self.narrow
        self.filter_button.visible = self.narrow

    def _on_resize(self) -> None:
        self._update_responsive()
        self.page.update()

    def _open_filters(self) -> None:
        self.page.end_drawer = ft.NavigationDrawer(
            controls=[FilterPanel(self, width=320).build()],
            width=340,
        )
        self.page.show_end_drawer()

    def _toggle_theme(self) -> None:
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.theme_button.icon = ft.Icons.LIGHT_MODE_OUTLINED
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.theme_button.icon = ft.Icons.DARK_MODE_OUTLINED
        self.page.update()


def main(page: ft.Page) -> None:
    configure_page(page)
    app = AppView(page)
    page.add(app.build())
    page.run_task(app.start)


__all__ = ["AppView", "main", "BRAND"]
