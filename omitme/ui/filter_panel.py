"""Side panel generated from a service's filter and scope declarations."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import flet as ft

from omitme.core.models import FilterField, FilterKind, ScopeSource


class FilterPanel:
    """Renders scope pickers and filters for the active service.

    Nothing in here knows about a specific platform.  Controls are chosen from
    ``FilterKind`` and populated from ``Service.options`` or static options.
    """

    def __init__(self, app, *, width: int | None = 360) -> None:
        self.app = app
        self.page = app.page
        self.state = app.state
        self.width = width
        self.matched_text = ft.Text(
            str(len(self.state.items)),
            size=13,
            weight=ft.FontWeight.BOLD,
        )
        self._root: ft.Container | None = None

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def build(self) -> ft.Control:
        container = ft.Container(
            content=self._column(self._build_children()),
            padding=ft.Padding.symmetric(horizontal=16, vertical=16),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.only(
                left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
            ),
        )
        if self.width is not None:
            container.width = self.width
        self._root = container
        return container

    def refresh(self) -> None:
        """Rebuild the panel in place after the underlying state changed."""
        self.matched_text.value = str(len(self.state.items))
        if self._root is None:
            return
        self._root.content = self._column(self._build_children())
        self._root.update()

    @staticmethod
    def _column(children: list[ft.Control]) -> ft.Column:
        return ft.Column(
            children,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _build_children(self) -> list[ft.Control]:
        service = self.state.active
        children: list[ft.Control] = []

        if service is None:
            return [
                ft.Text("Configure", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Choose a service from the rail to see its options.",
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ]

        header: list[ft.Control] = [
            ft.Text("Configure", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.TextButton("Reset", on_click=self._on_reset),
        ]
        if service.meta.docs_url:
            header.insert(
                2,
                ft.IconButton(
                    icon=ft.Icons.OPEN_IN_NEW,
                    icon_size=18,
                    tooltip="Service documentation",
                    url=service.meta.docs_url,
                ),
            )

        children = [
            ft.Row(
                header,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Text(
                service.meta.description,
                size=11,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ]

        if not service.connected:
            children.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.LOCK_OUTLINE,
                                size=16,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Text(
                                "Not connected — preview is unavailable.",
                                size=11,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                expand=True,
                            ),
                        ],
                        spacing=6,
                    ),
                    padding=ft.Padding.all(8),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                    border_radius=8,
                )
            )

        children.append(ft.Divider(height=1))

        if service.scopes:
            children.append(self._section_title("Scope"))
            for index, source in enumerate(service.scopes):
                children.append(
                    self._scope_section(source, expanded=index == 0)
                )

        if service.filters:
            children.append(self._section_title("Filters"))
            for field in service.filters:
                children.append(self._filter_field(field))

        self.matched_text = ft.Text(
            str(len(self.state.items)),
            size=13,
            weight=ft.FontWeight.BOLD,
        )
        children.extend(
            [
                ft.Divider(height=1),
                ft.Row(
                    [
                        ft.Text(
                            "Matched messages",
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Container(expand=True),
                        self.matched_text,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.FilledButton(
                    "Apply filters",
                    icon=ft.Icons.SEARCH,
                    width=(self.width - 32) if self.width else None,
                    disabled=not service.connected,
                    on_click=self._on_apply,
                ),
            ]
        )
        return children

    @staticmethod
    def _section_title(label: str) -> ft.Control:
        return ft.Text(
            label.upper(),
            size=10,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )

    # ------------------------------------------------------------------
    # Scope pickers
    # ------------------------------------------------------------------
    def _scope_section(
        self,
        source: ScopeSource,
        *,
        expanded: bool = False,
    ) -> ft.Control:
        selected = self.state.scopes.setdefault(source.key, [])
        options = source.options or self.state.options.get(source.key, [])

        count_text = ft.Text(
            self._selection_label(source, selected),
            size=10,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        list_column = ft.Column(spacing=0, tight=True)
        search = ft.TextField(
            hint_text=f"Search {source.label.lower()}…",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            visible=source.searchable,
            on_change=lambda event: _render_search(event.control.value or ""),
        )

        def render(text: str = "") -> list[ft.Control]:
            query = text.strip().lower()
            filtered = [
                option
                for option in options
                if not query
                or query in option.label.lower()
                or query in (option.description or "").lower()
            ]
            if not filtered:
                return [
                    ft.Text(
                        "No options available.",
                        size=11,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        italic=True,
                    )
                ]

            controls: list[ft.Control] = []
            for option in filtered:
                controls.append(
                    ft.Checkbox(
                        label=option.label,
                        value=option.value in selected,
                        on_change=lambda event, value=option.value: _toggle_option(
                            value, bool(event.control.value)
                        ),
                    )
                )
            return controls

        def _render_search(text: str) -> None:
            list_column.controls = render(text)
            list_column.update()

        def _toggle_option(value: str, checked: bool) -> None:
            if checked:
                if not source.multi:
                    selected[:] = [value]
                elif value not in selected:
                    selected.append(value)
            elif value in selected:
                selected.remove(value)

            count_text.value = self._selection_label(source, selected)
            count_text.update()

            if not source.multi:
                list_column.controls = render(search.value or "")
                list_column.update()

        list_column.controls = render()

        return ft.ExpansionTile(
            title=ft.Text(source.label, size=13),
            subtitle=count_text,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [search, list_column],
                        spacing=2,
                        tight=True,
                    ),
                    padding=ft.Padding.only(bottom=8),
                )
            ],
            expanded=expanded,
            dense=True,
            tile_padding=ft.Padding.symmetric(horizontal=6),
            controls_padding=ft.Padding.only(left=6, right=6),
        )

    @staticmethod
    def _selection_label(source: ScopeSource, selected: list[str]) -> str:
        if not selected:
            return f"All {source.label.lower()}"
        noun = source.label.lower()
        if len(selected) == 1:
            noun = noun[:-1] if noun.endswith("s") else noun
            return f"1 {noun} selected"
        return f"{len(selected)} {noun} selected"

    # ------------------------------------------------------------------
    # Filter controls
    # ------------------------------------------------------------------
    def _filter_field(self, field: FilterField) -> ft.Control:
        value: Any = self.state.filters.get(field.key, field.default)
        control: ft.Control

        if field.kind is FilterKind.BOOL:
            control = ft.Switch(
                label=field.label,
                value=bool(value),
                on_change=lambda event: self._set_filter(
                    field.key, bool(event.control.value)
                ),
            )
        elif field.kind is FilterKind.TEXT:
            control = ft.TextField(
                label=field.label,
                value=str(value or ""),
                hint_text=field.placeholder,
                dense=True,
                on_change=lambda event: self._set_filter(
                    field.key, event.control.value
                ),
            )
        elif field.kind is FilterKind.NUMBER:
            control = ft.TextField(
                label=field.label,
                value="" if value is None else str(value),
                hint_text=field.placeholder,
                keyboard_type=ft.KeyboardType.NUMBER,
                dense=True,
                on_change=lambda event: self._set_filter(
                    field.key, _parse_number(event.control.value)
                ),
            )
        elif field.kind is FilterKind.SELECT:
            options = field.options or self.state.options.get(
                field.options_source or "", []
            )
            control = ft.Dropdown(
                label=field.label,
                value=str(value or ""),
                dense=True,
                options=[
                    ft.DropdownOption(key="", text="Any"),
                    *[
                        ft.DropdownOption(key=option.value, text=option.label)
                        for option in options
                    ],
                ],
                on_select=lambda event: self._set_filter(
                    field.key, event.control.value or None
                ),
            )
        elif field.kind is FilterKind.MULTISELECT:
            control = self._multiselect_control(field, list(value or []))
        elif field.kind is FilterKind.DATE_RANGE:
            control = self._date_range_control(field, value)
        else:  # pragma: no cover - defensive for future kinds
            control = ft.Text(f"Unsupported filter: {field.kind}")

        children: list[ft.Control] = [control]
        if field.help:
            children.append(
                ft.Text(
                    field.help,
                    size=10,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
        return ft.Column(children, spacing=3, tight=True)

    def _multiselect_control(
        self,
        field: FilterField,
        selected: list[str],
    ) -> ft.Control:
        options = field.options or self.state.options.get(
            field.options_source or "", []
        )
        column = ft.Column(spacing=0, tight=True)

        def render() -> list[ft.Control]:
            if not options:
                return [
                    ft.Text(
                        "No options available.",
                        size=11,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        italic=True,
                    )
                ]
            return [
                ft.Checkbox(
                    label=option.label,
                    value=option.value in selected,
                    on_change=lambda event, value=option.value: toggle(
                        value, bool(event.control.value)
                    ),
                )
                for option in options
            ]

        def toggle(value: str, checked: bool) -> None:
            if checked and value not in selected:
                selected.append(value)
            elif not checked and value in selected:
                selected.remove(value)
            self._set_filter(field.key, list(selected))

        column.controls = render()
        return ft.Column(
            [
                ft.Text(field.label, size=12, weight=ft.FontWeight.W_500),
                column,
            ],
            spacing=2,
            tight=True,
        )

    def _date_range_control(self, field: FilterField, value: Any) -> ft.Control:
        dates = list(value or (None, None))
        if len(dates) != 2:
            dates = [None, None]

        from_button = ft.OutlinedButton(
            content=self._date_label("From", dates[0]),
            expand=True,
            on_click=lambda: self._open_date_picker(
                field, 0, from_button, until_button
            ),
        )
        until_button = ft.OutlinedButton(
            content=self._date_label("Until", dates[1]),
            expand=True,
            on_click=lambda: self._open_date_picker(
                field, 1, from_button, until_button
            ),
        )

        return ft.Column(
            [
                ft.Text(field.label, size=12, weight=ft.FontWeight.W_500),
                ft.Row([from_button, until_button], spacing=6, tight=True),
                ft.TextButton(
                    "Clear dates",
                    on_click=lambda: self._clear_dates(
                        field, from_button, until_button
                    ),
                ),
            ],
            spacing=2,
            tight=True,
        )

    def _open_date_picker(
        self,
        field: FilterField,
        index: int,
        from_button: ft.OutlinedButton,
        until_button: ft.OutlinedButton,
    ) -> None:
        dates = list(self.state.filters.get(field.key) or (None, None))
        if len(dates) != 2:
            dates = [None, None]
        current = dates[index]

        def on_change(event) -> None:
            picked = event.control.value
            if isinstance(picked, datetime):
                picked = picked.date()
            dates[index] = picked
            self.state.filters[field.key] = tuple(dates)

            if index == 0:
                from_button.content = self._date_label("From", picked)
                from_button.update()
            else:
                until_button.content = self._date_label("Until", picked)
                until_button.update()
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.DatePicker(
                first_date=date(2000, 1, 1),
                last_date=date.today(),
                value=current,
                on_change=on_change,
            )
        )

    def _clear_dates(
        self,
        field: FilterField,
        from_button: ft.OutlinedButton,
        until_button: ft.OutlinedButton,
    ) -> None:
        self.state.filters[field.key] = (None, None)
        from_button.content = self._date_label("From", None)
        until_button.content = self._date_label("Until", None)
        from_button.update()
        until_button.update()

    @staticmethod
    def _date_label(prefix: str, value: Any) -> str:
        if isinstance(value, datetime):
            value = value.date()
        if isinstance(value, date):
            return f"{prefix}: {value:%d %b %Y}"
        return f"{prefix}: Any"

    def _set_filter(self, key: str, value: Any) -> None:
        self.state.filters[key] = value

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    async def _on_apply(self) -> None:
        await self.app.apply_filters()
        self.matched_text.value = str(len(self.state.items))
        self.matched_text.update()
        if self.app.narrow:
            self.page.close_end_drawer()

    async def _on_reset(self) -> None:
        self.state.reset_filters()
        await self.app.apply_filters()
        self.refresh()
        if self.app.narrow:
            self.page.close_end_drawer()


def _parse_number(raw: str) -> int | float | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return None
