# OmitMe

OmitMe is a cross-platform privacy tool for reviewing and deleting your data
from online services. This repository currently contains the **Flet UI
skeleton**: it previews messages, generates filters from a service definition,
lets you pick servers/channels/users, and simulates deletion with a dry run.

No real data is deleted in this build.

## Run

```bash
poetry install
poetry run python -m omitme
```

Or with the Flet CLI:

```bash
poetry run flet run main.py
```

The app opens with **Demo Chat**, an offline service with deterministic sample
data. Select **Discord** in the left rail to see the definition-only service
state.

## What works

- Service switcher generated from the registry.
- Side panel generated from declarative filters and scopes.
- Searchable server / channel / user pickers.
- Message preview with per-row selection, select-all and full-message dialog.
- Dry-run deletion that reports what *would* happen.
- Responsive layout: the side panel becomes an end drawer on narrow windows.
- Light/dark theme toggle.

## Adding a service

See [docs/adding-a-service.md](docs/adding-a-service.md). The short version:

```python
@register
class MyService(Service):
    meta = ServiceMeta(id="mine", name="Mine", icon="LANGUAGE")
    filters = (FilterField(key="content", label="Contains", kind=FilterKind.TEXT),)
    scopes = (ScopeSource(key="users", label="Users"),)

    async def connect(self): ...
    async def options(self, source, search=""): ...
    async def preview(self, query): ...
    async def delete(self, items, *, dry_run=True): ...
```

Then import the module in `omitme/services/__init__.py`. The UI needs no
changes.

## Layout

```
omitme/
  app.py            app shell and layout
  core/             models, service contract, registry, app state
  services/         bundled service definitions
  ui/               Flet components
docs/               service author guide
tests/              core/state tests (stdlib unittest)
```

## Tests

```bash
poetry run python -m unittest discover -s tests -v
```
