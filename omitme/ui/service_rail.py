"""Left-hand service switcher, generated from the registry."""

from __future__ import annotations

import flet as ft

from omitme.ui.theme import icon_for


def build_service_rail(app) -> ft.NavigationRail:
    destinations = [
        ft.NavigationRailDestination(
            icon=icon_for(service.meta),
            selected_icon=icon_for(service.meta),
            label=service.meta.name,
            tooltip=service.meta.description or service.meta.name,
        )
        for service in app.state.services
    ]

    return ft.NavigationRail(
        selected_index=0 if destinations else None,
        destinations=destinations,
        label_type=ft.NavigationRailLabelType.SELECTED,
        min_width=88,
        group_alignment=-1.0,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        on_change=app.on_service_change,
    )
