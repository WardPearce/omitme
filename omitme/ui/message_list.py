"""The message preview list, selection state and dry-run action bar."""

from __future__ import annotations

import flet as ft

from omitme.core.models import DeletableItem, ItemStatus
from omitme.ui.dialogs import show_message_preview, show_real_deletion_unavailable
from omitme.ui.theme import icon_for, status_chip


class MessageList:
    """Builds the centre column: header, scrollable rows and action bar."""

    def __init__(self, app) -> None:
        self.app = app
        self.page = app.page

        self.header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=14),
            content=ft.Row(),
        )
        self.list_view = ft.ListView(
            expand=True,
            spacing=6,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        )

        self.root = ft.Column(
            [
                self.header,
                ft.Divider(height=1),
                self.list_view,
            ],
            expand=True,
            spacing=0,
        )
        self.refresh()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        state = self.app.state
        service = state.active

        if service is None:
            self.header.content = ft.Row(
                [
                    ft.Text(
                        "Welcome to OmitMe",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    )
                ]
            )
        else:
            matched = len(state.items)
            self.header.content = ft.Row(
                [
                    ft.Icon(
                        icon_for(service.meta),
                        color=service.meta.color or ft.Colors.PRIMARY,
                        size=22,
                    ),
                    ft.Column(
                        [
                            ft.Text(service.meta.name, size=17, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                service.meta.description,
                                size=11,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                        tight=True,
                    ),
                    ft.Container(
                        content=ft.Text(
                            f"{matched} matched",
                            size=11,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        border_radius=99,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="Reload preview",
                        disabled=state.loading or service is None,
                        on_click=self._refresh_clicked,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        self.list_view.controls = self._list_controls()

    def _list_controls(self) -> list[ft.Control]:
        state = self.app.state

        if state.loading:
            return [
                self._placeholder(
                    ft.ProgressRing(width=28, height=28),
                    "Loading preview…",
                    "Fetching the items that match your filters.",
                )
            ]

        if state.error:
            return [
                self._placeholder(
                    ft.Icon(
                        ft.Icons.LOCK_OUTLINE,
                        size=44,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    "This service is not available",
                    state.error,
                    action=ft.FilledTonalButton(
                        "Retry connection",
                        icon=ft.Icons.REFRESH,
                        on_click=self._retry_clicked,
                    ),
                )
            ]

        if not state.items:
            return [
                self._placeholder(
                    ft.Icon(
                        ft.Icons.INBOX_OUTLINED,
                        size=44,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    "No messages match",
                    "Adjust the filters or choose a different scope in the side panel.",
                )
            ]

        return [self._row(item) for item in state.items]

    def _row(self, item: DeletableItem) -> ft.Control:
        state = self.app.state
        selected = item.id in state.selected
        channel_label = (
            item.channel if item.channel.startswith("#") else f"#{item.channel}"
        )

        subtitle_controls: list[ft.Control] = [
            ft.Text(
                _preview_text(item.content),
                size=12,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
        ]
        if item.attachments:
            subtitle_controls.append(
                ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.ATTACH_FILE,
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            f"{item.attachments} attachment{'s' if item.attachments != 1 else ''}",
                            size=10,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    spacing=3,
                    tight=True,
                )
            )

        return ft.Container(
            content=ft.Row(
                [
                    ft.Checkbox(
                        value=selected,
                        on_change=lambda event, item_id=item.id: self._toggle(
                            item_id, bool(event.control.value)
                        ),
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        item.author,
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        channel_label,
                                        size=11,
                                        color=ft.Colors.PRIMARY,
                                    ),
                                    ft.Text(
                                        f"{item.created_at:%d %b %Y · %H:%M}",
                                        size=10,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                                spacing=8,
                                tight=True,
                                wrap=True,
                            ),
                            *subtitle_controls,
                        ],
                        spacing=3,
                        expand=True,
                        tight=True,
                    ),
                    ft.Row(
                        [
                            status_chip(item.status),
                            ft.IconButton(
                                icon=ft.Icons.VISIBILITY_OUTLINED,
                                icon_size=18,
                                tooltip="Preview message",
                                on_click=lambda event, current=item: show_message_preview(
                                    self.page, current
                                ),
                            ),
                        ],
                        spacing=2,
                        tight=True,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            border_radius=10,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW if selected else None,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT) if selected else None,
        )

    @staticmethod
    def _placeholder(
        icon: ft.Control,
        title: str,
        body: str,
        action: ft.Control | None = None,
    ) -> ft.Control:
        children: list[ft.Control] = [
            icon,
            ft.Text(title, size=17, weight=ft.FontWeight.BOLD),
            ft.Text(
                body,
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
            ),
        ]
        if action is not None:
            children.append(action)

        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=32, vertical=48),
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                children,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                tight=True,
            ),
        )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _toggle(self, item_id: str, selected: bool) -> None:
        self.app.state.toggle(item_id, selected)
        self.app.selection_changed()

    def select_all(self) -> None:
        self.app.state.select_all()
        self.app.selection_changed()

    def clear_selection(self) -> None:
        self.app.state.clear_selection()
        self.app.selection_changed()

    async def _refresh_clicked(self) -> None:
        await self.app.reload()

    async def _retry_clicked(self) -> None:
        await self.app.retry()

    async def delete_selected(self) -> None:
        state = self.app.state
        service = state.active
        if service is None or not state.selected_items or state.loading:
            return

        if not state.dry_run:
            show_real_deletion_unavailable(self.page)
            return

        items = list(state.selected_items)
        for item in items:
            item.status = ItemStatus.QUEUED
        self.app.selection_changed()

        try:
            results = [
                result
                async for result in service.delete(items, dry_run=True)
            ]
            by_id = {result.item_id: result for result in results}
            for item in items:
                result = by_id.get(item.id)
                item.status = result.status if result else ItemStatus.FAILED
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            for item in items:
                item.status = ItemStatus.FAILED
            self.app.selection_changed()
            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Dry run failed: {exc}"),
                    show_close_icon=True,
                )
            )
            return

        self.app.selection_changed()

        count = len(items)
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(
                    f"Dry run complete — {count} message{'s' if count != 1 else ''} "
                    "would be deleted."
                ),
                show_close_icon=True,
            )
        )


def _preview_text(content: str) -> str:
    flattened = " ".join(content.split())
    if len(flattened) > 180:
        return f"{flattened[:177]}…"
    return flattened
