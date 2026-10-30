"""Definition-only Discord service.

This file demonstrates how a real integration would plug in.  Authentication
and API calls are intentionally unimplemented: selecting the service shows the
generated scope/filter UI and a friendly "not connected" state.
"""

from __future__ import annotations

from omitme.core.models import FilterField, FilterKind, ScopeSource, ServiceMeta
from omitme.core.registry import register
from omitme.core.service import Service


@register
class DiscordService(Service):
    meta = ServiceMeta(
        id="discord",
        name="Discord",
        description="Delete your own Discord messages. Definition-only in this build.",
        icon="DISCORD",
        color="#5865F2",
        docs_url="https://discord.com/developers/docs",
    )

    filters = (
        FilterField(
            key="content",
            label="Message contains",
            kind=FilterKind.TEXT,
            placeholder="Search your messages",
        ),
        FilterField(
            key="date_range",
            label="Sent between",
            kind=FilterKind.DATE_RANGE,
        ),
        FilterField(
            key="attachments_only",
            label="Only messages with attachments",
            kind=FilterKind.BOOL,
            default=False,
        ),
    )

    scopes = (
        ScopeSource(
            key="servers",
            label="Servers",
            description="Guilds to include in the preview.",
        ),
        ScopeSource(
            key="channels",
            label="Channels",
            description="Channels to include in the preview.",
        ),
        ScopeSource(
            key="users",
            label="Users",
            description="Only include messages you sent to these people.",
        ),
    )

    # A real implementation would:
    #   1. authenticate (OAuth or a user-supplied token) in connect()
    #   2. return guilds/channels/DMs from options()
    #   3. page through the search API in preview()
    #   4. delete each message in delete(), respecting dry_run
    #
    # The base class deliberately raises ServiceNotConnectedError so the UI
    # can show the "definition only" state.
