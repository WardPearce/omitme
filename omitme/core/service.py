"""The service contract that every platform implements."""

from __future__ import annotations

from abc import ABC
from collections.abc import AsyncIterator, Sequence
from typing import ClassVar

from omitme.core.models import (
    DeletableItem,
    DeleteResult,
    FilterField,
    ItemStatus,
    Option,
    Query,
    ScopeSource,
    ServiceMeta,
)


class ServiceError(Exception):
    """Base class for recoverable service errors shown in the UI."""


class ServiceNotConnectedError(ServiceError):
    """Raised when an operation needs authentication first."""


class Service(ABC):
    """Base class for a deletable-data service.

    Subclasses declare ``meta``, ``filters`` and ``scopes`` as class
    attributes and implement the async methods below.  The UI is generated
    from those declarations, so a service never imports Flet.

    The default ``delete`` implementation is deliberately a no-op.  This
    release is a UI skeleton and must not touch real data.
    """

    meta: ClassVar[ServiceMeta]
    filters: ClassVar[tuple[FilterField, ...]] = ()
    scopes: ClassVar[tuple[ScopeSource, ...]] = ()

    def __init__(self) -> None:
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Authenticate and prepare the service for previewing data."""
        raise ServiceNotConnectedError(
            f"{self.meta.name} does not implement authentication yet."
        )

    async def disconnect(self) -> None:
        self._connected = False

    async def options(self, source: str, search: str = "") -> list[Option]:
        """Return choices for a scope or filter ``options_source``.

        ``search`` is a hint for services with large account-specific lists;
        implementations may ignore it.
        """
        return []

    async def preview(self, query: Query) -> AsyncIterator[DeletableItem]:
        """Yield items matching ``query`` without changing any remote state."""
        raise ServiceNotConnectedError(
            f"{self.meta.name} cannot list data yet."
        )
        yield  # pragma: no cover - makes this an async generator

    async def delete(
        self,
        items: Sequence[DeletableItem],
        *,
        dry_run: bool = True,
    ) -> AsyncIterator[DeleteResult]:
        """Delete ``items`` and report progress item by item.

        The base implementation is a safe no-op.  Real services should check
        ``dry_run`` and never send destructive requests when it is true.
        """
        for item in items:
            yield DeleteResult(
                item_id=item.id,
                status=ItemStatus.DRY_RUN if dry_run else ItemStatus.FAILED,
                message=(
                    "Dry run: no data was deleted."
                    if dry_run
                    else f"{self.meta.name} does not implement deletion yet."
                ),
            )
