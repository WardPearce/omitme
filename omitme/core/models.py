"""UI-agnostic data models shared by services and the Flet layer.

A service definition describes *what* can be deleted and *how* a user narrows
it down.  The UI turns these declarations into controls, which means a new
service does not need to write any Flet code.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FilterKind(str, Enum):
    """Control type used to render a filter field."""

    BOOL = "bool"
    TEXT = "text"
    SELECT = "select"
    MULTISELECT = "multiselect"
    DATE_RANGE = "date_range"
    NUMBER = "number"


class ItemStatus(str, Enum):
    """Lifecycle of a single preview item."""

    PENDING = "pending"
    QUEUED = "queued"
    DRY_RUN = "dry_run"
    DELETED = "deleted"
    SKIPPED = "skipped"
    FAILED = "failed"


class Option(BaseModel):
    """A selectable value shown in a dropdown or checkbox list."""

    value: str
    label: str
    description: str | None = None


class ServiceMeta(BaseModel):
    """Human-facing metadata for a service."""

    id: str
    name: str
    description: str = ""
    #: Name of a ``flet.Icons`` attribute, e.g. ``"DISCORD"``.
    icon: str = "EXTENSION"
    color: str | None = None
    docs_url: str | None = None


class FilterField(BaseModel):
    """A filter rendered by the side panel.

    ``options`` can be supplied statically.  When ``options_source`` is set,
    the panel asks ``Service.options(source)`` for the values instead (useful
    for account-specific data such as channels or users).
    """

    key: str
    label: str
    kind: FilterKind
    default: Any = None
    help: str | None = None
    placeholder: str | None = None
    options: list[Option] = Field(default_factory=list)
    options_source: str | None = None


class ScopeSource(BaseModel):
    """A group of account objects a user can limit the preview to."""

    key: str
    label: str
    description: str | None = None
    multi: bool = True
    searchable: bool = True
    options: list[Option] = Field(default_factory=list)


class DeletableItem(BaseModel):
    """One thing that can be shown in the preview and later deleted."""

    id: str
    kind: str = "message"
    author: str
    author_id: str | None = None
    channel: str
    channel_id: str | None = None
    created_at: datetime
    content: str
    attachments: int = 0
    permalink: str | None = None
    status: ItemStatus = ItemStatus.PENDING
    extra: dict[str, Any] = Field(default_factory=dict)


class Query(BaseModel):
    """Everything the side panel collected before asking a service for data."""

    filters: dict[str, Any] = Field(default_factory=dict)
    scopes: dict[str, list[str]] = Field(default_factory=dict)
    limit: int | None = None


class DeleteResult(BaseModel):
    """Result of attempting to delete one item."""

    item_id: str
    status: ItemStatus
    message: str | None = None
