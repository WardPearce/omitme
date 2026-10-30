# Adding a service

OmitMe builds its UI from a service definition. A service never imports Flet:
it declares metadata, filters and scopes, then implements a few async methods.
The side panel, scope pickers and preview list are generated automatically.

## 1. Create a module

Add a file under `omitme/services/`, for example `omitme/services/my_service.py`:

```python
from collections.abc import AsyncIterator, Sequence

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
from omitme.core.service import Service


@register
class MyService(Service):
    meta = ServiceMeta(
        id="my-service",
        name="My Service",
        description="Delete your posts from My Service.",
        icon="LANGUAGE",          # any flet.Icons attribute name
        color="#0EA5E9",
    )

    # These declarations generate the side-panel controls.
    filters = (
        FilterField(
            key="content",
            label="Post contains",
            kind=FilterKind.TEXT,
            placeholder="Search text",
        ),
        FilterField(
            key="date_range",
            label="Posted between",
            kind=FilterKind.DATE_RANGE,
        ),
        FilterField(
            key="attachments_only",
            label="Only posts with attachments",
            kind=FilterKind.BOOL,
            default=False,
        ),
    )

    # These generate the scope pickers.
    scopes = (
        ScopeSource(key="spaces", label="Spaces"),
        ScopeSource(key="channels", label="Channels"),
        ScopeSource(key="users", label="Users"),
    )

    async def connect(self) -> None:
        # Authenticate here. Set _connected when ready.
        self._connected = True

    async def options(self, source: str, search: str = "") -> list[Option]:
        # Return choices for the scope/filter with this key.
        if source == "spaces":
            return [Option(value="space-1", label="Example space")]
        return []

    async def preview(self, query: Query) -> AsyncIterator[DeletableItem]:
        # Yield everything that matches query.filters / query.scopes.
        # This must be read-only.
        yield DeletableItem(
            id="post-1",
            author="you",
            channel="general",
            created_at=__import__("datetime").datetime.now(),
            content="Example post",
        )

    async def delete(
        self,
        items: Sequence[DeletableItem],
        *,
        dry_run: bool = True,
    ) -> AsyncIterator[DeleteResult]:
        for item in items:
            if dry_run:
                yield DeleteResult(item_id=item.id, status=ItemStatus.DRY_RUN)
                continue

            # Call the real API here. Report one result per item.
            yield DeleteResult(item_id=item.id, status=ItemStatus.DELETED)
```

## 2. Register the module

Import it in `omitme/services/__init__.py`:

```python
from omitme.services import my_service  # noqa: F401
```

That import runs `@register`, and the service appears in the left rail.

## 3. Contract reference

| Member | Purpose |
| --- | --- |
| `meta` | Name, description, icon and colour shown in the UI. |
| `filters` | `FilterField` declarations rendered by `FilterKind`. |
| `scopes` | `ScopeSource` declarations rendered as searchable checkbox lists. |
| `connect()` | Authenticate. Set `self._connected = True` on success. |
| `options(source, search)` | Dynamic options for a scope or `FilterField.options_source`. |
| `preview(query)` | Read-only async generator of `DeletableItem`s. |
| `delete(items, dry_run)` | Async generator of `DeleteResult`s. **Always honour `dry_run`.** |

### Filter kinds

| Kind | Rendered as |
| --- | --- |
| `FilterKind.TEXT` | Text field |
| `FilterKind.BOOL` | Switch |
| `FilterKind.NUMBER` | Numeric text field |
| `FilterKind.SELECT` | Dropdown (static `options` or `options_source`) |
| `FilterKind.MULTISELECT` | Checkbox list |
| `FilterKind.DATE_RANGE` | From/until date buttons |

### Scope options

Set `ScopeSource.options` for static choices, or leave it empty and return
values from `options(source)` for account-specific choices. The same mechanism
works for a filter by setting `FilterField.options_source`.

## Safety

This release is a UI skeleton. `AppView` always calls `delete(..., dry_run=True)`
and the built-in services never touch remote data. A real service should refuse
destructive requests unless `dry_run` is explicitly false.
