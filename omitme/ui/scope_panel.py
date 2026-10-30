"""Secondary navigation rail for choosing what to delete from a service."""

from __future__ import annotations

import flet as ft

from omitme.core.models import Option, ScopeSource

_SCOPE_ICONS: dict[str, ft.IconData] = {
    "servers": ft.Icons.DNS_OUTLINED,
    "guilds": ft.Icons.DNS_OUTLINED,
    "channels": ft.Icons.TAG,
    "users": ft.Icons.PERSON_OUTLINE,
    "people": ft.Icons.PERSON_OUTLINE,
}


class ScopePanel:
    """Shows the active service's servers, channels, users and other scopes.

    All scopes are merged into one searchable list.  Each row carries an icon
    for its source so servers, channels and users stay visually distinct.
    """

    def __init__(self, app, *, width: int = 260) -> None:
        self.app = app
        self.page = app.page
        self.state = app.state
        self.width = width
        self.summary_text = ft.Text(
            self._selection_summary(),
            size=10,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self.search_field = ft.TextField(
            hint_text="Search…",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            on_change=self._on_search,
        )
        self.list_column = ft.Column(spacing=0, tight=True)
        self._root: ft.Container | None = None

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def build(self) -> ft.Control:
        container = ft.Container(
            content=self._column(self._build_children()),
            padding=ft.Padding.symmetric(horizontal=14, vertical=16),
            width=self.width,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.only(
                right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
            ),
        )
        self._root = container
        return container

    def refresh(self) -> None:
        """Rebuild the merged scope list in place after state changed."""
        if self._root is None:
            return
        self.summary_text.value = self._selection_summary()
        self._root.content = self._column(self._build_children())

    @staticmethod
    def _column(children: list[ft.Control]) -> ft.Column:
        return ft.Column(
            children,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _build_children(self) -> list[ft.Control]:
        service = self.state.active

        children: list[ft.Control] = [
            ft.Text("Delete from", size=16, weight=ft.FontWeight.BOLD),
        ]

        if service is None:
            children.append(
                ft.Text(
                    "Choose a service from the rail to see its scopes.",
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
            return children

        children.extend(
            [
                ft.Text(
                    service.meta.name,
                    size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=1),
            ]
        )

        if not service.scopes:
            children.append(
                ft.Text(
                    "This service does not expose any scopes.",
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
            return children

        self._render_options(self.search_field.value or "")
        children.extend(
            [
                self.search_field,
                self.summary_text,
                self.list_column,
            ]
        )
        return children

    # ------------------------------------------------------------------
    # Merged scope list
    # ------------------------------------------------------------------
    def _render_options(self, text: str = "") -> None:
        service = self.state.active
        if service is None:
            self.list_column.controls = []
            return

        query = text.strip().lower()
        controls: list[ft.Control] = []

        for source in service.scopes:
            options = source.options or self.state.options.get(source.key, [])
            filtered = [
                option
                for option in options
                if not query
                or query in option.label.lower()
                or query in (option.description or "").lower()
                or query in source.label.lower()
            ]
            for option in filtered:
                controls.append(self._option_row(source, option))

        if not controls:
            controls.append(
                ft.Text(
                    "No options available.",
                    size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    italic=True,
                )
            )

        self.list_column.controls = controls

    def _option_row(self, source: ScopeSource, option: Option) -> ft.Control:
        selected = self.state.scopes.setdefault(source.key, [])

        return ft.Row(
            [
                ft.Icon(
                    _SCOPE_ICONS.get(source.key, ft.Icons.LABEL_OUTLINE),
                    size=16,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    tooltip=source.label,
                ),
                ft.Checkbox(
                    label=option.label,
                    value=option.value in selected,
                    expand=True,
                    on_change=lambda event, s=source, v=option.value: (
                        self._toggle_option(s, v, bool(event.control.value))
                    ),
                ),
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _toggle_option(
        self,
        source: ScopeSource,
        value: str,
        checked: bool,
    ) -> None:
        selected = self.state.scopes.setdefault(source.key, [])

        if checked:
            if not source.multi:
                selected[:] = [value]
            elif value not in selected:
                selected.append(value)
        elif value in selected:
            selected.remove(value)

        self.summary_text.value = self._selection_summary()
        self.summary_text.update()

        if not source.multi:
            self._render_options(self.search_field.value or "")
            self.list_column.update()

    def _on_search(self, event) -> None:
        self._render_options(event.control.value or "")
        self.list_column.update()

    def _selection_summary(self) -> str:
        service = self.state.active
        if service is None or not service.scopes:
            return "Nothing selected"

        total = sum(len(values) for values in self.state.scopes.values())
        if total:
            return f"{total} selected"

        labels = [source.label.lower() for source in service.scopes]
        if len(labels) == 1:
            return f"All {labels[0]}"
        return f"All {', '.join(labels[:-1])} and {labels[-1]}"
