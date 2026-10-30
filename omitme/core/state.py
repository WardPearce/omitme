"""Application state shared by the UI components."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from omitme.core.models import DeletableItem, FilterKind, Option, Query
from omitme.core.service import Service


class AppState:
    """Mutable state for one app session.

    Keeping this separate from Flet makes the preview/filter behaviour easy to
    test and lets the UI be rebuilt from scratch whenever a service changes.
    """

    def __init__(self, services: Sequence[Service]) -> None:
        self.services: list[Service] = list(services)
        self.active: Service | None = None
        self.filters: dict[str, Any] = {}
        self.scopes: dict[str, list[str]] = {}
        self.items: list[DeletableItem] = []
        self.selected: set[str] = set()
        self.options: dict[str, list[Option]] = {}
        self.loading = False
        self.error: str | None = None
        self.dry_run = True

    # ------------------------------------------------------------------
    # Service / query lifecycle
    # ------------------------------------------------------------------
    def set_service(self, service: Service) -> None:
        self.active = service
        self.reset_filters()
        self.items = []
        self.selected.clear()
        self.options = {}
        self.error = None

    def reset_filters(self) -> None:
        service = self.active
        if service is None:
            self.filters = {}
            self.scopes = {}
            return

        filters: dict[str, Any] = {}
        for field in service.filters:
            if field.kind is FilterKind.DATE_RANGE:
                filters[field.key] = field.default or (None, None)
            else:
                filters[field.key] = field.default

        self.filters = filters
        self.scopes = {source.key: [] for source in service.scopes}

    def build_query(self) -> Query:
        return Query(filters=dict(self.filters), scopes={k: list(v) for k, v in self.scopes.items()})

    @property
    def option_sources(self) -> set[str]:
        service = self.active
        if service is None:
            return set()
        sources = {source.key for source in service.scopes if not source.options}
        sources |= {
            field.options_source
            for field in service.filters
            if field.options_source
        }
        return {source for source in sources if source}

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    async def load_options(self) -> None:
        service = self.active
        if service is None:
            self.options = {}
            return

        options: dict[str, list[Option]] = {}
        for source in sorted(self.option_sources):
            try:
                options[source] = await service.options(source)
            except Exception:
                options[source] = []
        self.options = options

    async def refresh(self) -> None:
        service = self.active
        if service is None:
            self.items = []
            self.selected.clear()
            return

        self.loading = True
        self.error = None
        try:
            self.items = [item async for item in service.preview(self.build_query())]
            self.selected = {item.id for item in self.items}
        except Exception as exc:  # noqa: BLE001 - surfaced in the UI
            self.items = []
            self.selected.clear()
            self.error = str(exc) or exc.__class__.__name__
        finally:
            self.loading = False

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------
    @property
    def selected_items(self) -> list[DeletableItem]:
        return [item for item in self.items if item.id in self.selected]

    def toggle(self, item_id: str, selected: bool) -> None:
        if selected:
            self.selected.add(item_id)
        else:
            self.selected.discard(item_id)

    def select_all(self) -> None:
        self.selected = {item.id for item in self.items}

    def clear_selection(self) -> None:
        self.selected.clear()
