"""Demo service used to exercise the UI without any network access."""

from __future__ import annotations

import asyncio
import random
from collections.abc import AsyncIterator, Sequence
from datetime import date, datetime, timedelta
from typing import Any

from omitme.core.models import (
    DeletableItem,
    DeleteResult,
    FilterField,
    FilterKind,
    ItemStatus,
    Option,
    Query,
    ScopeSource,
    ServiceMeta,
)
from omitme.core.registry import register
from omitme.core.service import Service, ServiceNotConnectedError

_SERVERS = [
    Option(value="srv-design", label="Design Guild", description="UI, product and design chat"),
    Option(value="srv-gaming", label="Late Night Gaming", description="Friends-only server"),
    Option(value="srv-work", label="Acme Studio", description="Work server"),
]

_CHANNELS: list[tuple[Option, str]] = [
    (Option(value="chn-general", label="#general", description="Design Guild"), "srv-design"),
    (Option(value="chn-feedback", label="#feedback", description="Design Guild"), "srv-design"),
    (Option(value="chn-random", label="#random", description="Design Guild"), "srv-design"),
    (Option(value="chn-lfg", label="#looking-for-group", description="Late Night Gaming"), "srv-gaming"),
    (Option(value="chn-clips", label="#clips", description="Late Night Gaming"), "srv-gaming"),
    (Option(value="chn-offtopic", label="#off-topic", description="Late Night Gaming"), "srv-gaming"),
    (Option(value="chn-standup", label="#standup", description="Acme Studio"), "srv-work"),
    (Option(value="chn-incidents", label="#incidents", description="Acme Studio"), "srv-work"),
]

_USERS = [
    Option(value="usr-ada", label="Ada"),
    Option(value="usr-grace", label="Grace"),
    Option(value="usr-linus", label="Linus"),
    Option(value="usr-margaret", label="Margaret"),
    Option(value="usr-alan", label="Alan"),
    Option(value="usr-barbara", label="Barbara"),
]

_CONTENT = [
    "Is the staging deploy still broken for everyone else?",
    "I moved the old screenshots into the archive folder.",
    "That colour palette looks much better on mobile now.",
    "Reminder: the retro starts in ten minutes.",
    "Found a typo in the onboarding copy — pushing a fix.",
    "Anyone up for a quick game tonight?",
    "The API docs need another pass before launch.",
    "Thanks for the review! I addressed the comments.",
    "We should probably delete these test messages.",
    "Old project notes: the migration is finished, nothing to see here.",
    "Who has the link to the shared drive?",
    "This channel has been quiet for weeks.",
    "Attaching the latest export for reference.",
    "I think we can close this thread now.",
    "Please ignore the noise from my test bot.",
    "The new build is live on the beta channel.",
]


@register
class MockService(Service):
    """An offline service with deterministic fake chat data.

    It exists so the whole flow — filters, scopes, preview, selection and the
    dry-run delete action — can be tried without credentials or network access.
    """

    meta = ServiceMeta(
        id="demo",
        name="Demo Chat",
        description="Offline sample messages for exploring the UI.",
        icon="CHAT_BUBBLE_OUTLINE",
        color="#5865F2",
    )

    filters = (
        FilterField(
            key="content",
            label="Message contains",
            kind=FilterKind.TEXT,
            placeholder="e.g. old project name",
        ),
        FilterField(
            key="author_id",
            label="Author",
            kind=FilterKind.SELECT,
            options_source="users",
        ),
        FilterField(
            key="attachments_only",
            label="Only messages with attachments",
            kind=FilterKind.BOOL,
            default=False,
        ),
        FilterField(
            key="date_range",
            label="Sent between",
            kind=FilterKind.DATE_RANGE,
            help="Leave either side empty for an open range.",
        ),
    )

    scopes = (
        ScopeSource(
            key="servers",
            label="Servers",
            description="Limit the preview to specific servers.",
        ),
        ScopeSource(
            key="channels",
            label="Channels",
            description="Limit the preview to specific channels.",
        ),
        ScopeSource(
            key="users",
            label="Users",
            description="Only include messages written by these people.",
        ),
    )

    def __init__(self) -> None:
        super().__init__()
        self._messages = self._build_messages()

    @staticmethod
    def _build_messages() -> list[DeletableItem]:
        rng = random.Random(20261030)
        now = datetime.now().replace(second=0, microsecond=0)
        messages: list[DeletableItem] = []

        for index in range(84):
            channel, server_id = rng.choice(_CHANNELS)
            user = rng.choice(_USERS)
            content = rng.choice(_CONTENT)
            if rng.random() < 0.18:
                content = f"{content} {rng.choice(_CONTENT)}"

            created_at = now - timedelta(
                days=rng.randint(0, 120),
                hours=rng.randint(0, 23),
                minutes=rng.randint(0, 59),
            )

            messages.append(
                DeletableItem(
                    id=f"msg-{index:03d}",
                    author=user.label,
                    author_id=user.value,
                    channel=channel.label.lstrip("#"),
                    channel_id=channel.value,
                    created_at=created_at,
                    content=content,
                    attachments=rng.choice([0, 0, 0, 0, 1, 2, 3]),
                    extra={"server_id": server_id},
                )
            )

        messages.sort(key=lambda item: item.created_at, reverse=True)
        return messages

    async def connect(self) -> None:
        # Simulate a short login round-trip so loading states are visible.
        await asyncio.sleep(0.15)
        self._connected = True

    async def options(self, source: str, search: str = "") -> list[Option]:
        if source == "servers":
            options = list(_SERVERS)
        elif source == "channels":
            options = [option for option, _ in _CHANNELS]
        elif source == "users":
            options = list(_USERS)
        else:
            options = []

        query = search.strip().lower()
        if query:
            options = [
                option
                for option in options
                if query in option.label.lower()
                or query in (option.description or "").lower()
            ]
        return options

    async def preview(self, query: Query) -> AsyncIterator[DeletableItem]:
        if not self.connected:
            raise ServiceNotConnectedError("Demo Chat is not connected.")

        filters: dict[str, Any] = query.filters
        scopes = query.scopes

        server_ids = set(scopes.get("servers") or [])
        channel_ids = set(scopes.get("channels") or [])
        user_ids = set(scopes.get("users") or [])

        content_query = str(filters.get("content") or "").strip().lower()
        author_id = str(filters.get("author_id") or "")
        attachments_only = bool(filters.get("attachments_only"))

        start, end = filters.get("date_range") or (None, None)
        start = _as_date(start)
        end = _as_date(end)

        count = 0
        for message in self._messages:
            if server_ids and message.extra.get("server_id") not in server_ids:
                continue
            if channel_ids and message.channel_id not in channel_ids:
                continue
            if user_ids and message.author_id not in user_ids:
                continue
            if content_query and content_query not in message.content.lower():
                continue
            if author_id and message.author_id != author_id:
                continue
            if attachments_only and message.attachments == 0:
                continue
            if start and message.created_at.date() < start:
                continue
            if end and message.created_at.date() > end:
                continue

            yield message.model_copy(update={"status": ItemStatus.PENDING})

            count += 1
            if query.limit is not None and count >= query.limit:
                break

    async def delete(
        self,
        items: Sequence[DeletableItem],
        *,
        dry_run: bool = True,
    ) -> AsyncIterator[DeleteResult]:
        for item in items:
            await asyncio.sleep(0.005)
            yield DeleteResult(
                item_id=item.id,
                status=ItemStatus.DRY_RUN if dry_run else ItemStatus.FAILED,
                message=(
                    "Dry run: no data was deleted."
                    if dry_run
                    else "Demo Chat only supports dry runs."
                ),
            )


def _as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None
