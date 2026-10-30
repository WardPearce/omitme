from __future__ import annotations

import unittest

from omitme.core.models import FilterKind, ItemStatus, Query
from omitme.core.state import AppState
from omitme.services import create_services


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.services = {service.meta.id: service for service in create_services()}
        self.demo = self.services["demo"]
        await self.demo.connect()

    async def test_builtin_services_are_registered(self) -> None:
        self.assertIn("demo", self.services)
        self.assertIn("discord", self.services)

    async def test_demo_preview_returns_items(self) -> None:
        items = [item async for item in self.demo.preview(Query())]
        self.assertGreater(len(items), 10)
        self.assertTrue(all(item.status is ItemStatus.PENDING for item in items))

    async def test_demo_filters_and_scopes(self) -> None:
        items = [
            item
            async for item in self.demo.preview(
                Query(
                    filters={"content": "delete"},
                    scopes={"servers": ["srv-design"]},
                )
            )
        ]
        self.assertTrue(items)
        self.assertTrue(all("delete" in item.content.lower() for item in items))
        self.assertTrue(
            all(item.extra["server_id"] == "srv-design" for item in items)
        )

    async def test_demo_dry_run(self) -> None:
        items = [item async for item in self.demo.preview(Query(limit=3))]
        results = [result async for result in self.demo.delete(items, dry_run=True)]
        self.assertEqual(len(results), 3)
        self.assertTrue(all(result.status is ItemStatus.DRY_RUN for result in results))

    async def test_discord_is_definition_only(self) -> None:
        discord = self.services["discord"]
        with self.assertRaises(Exception):
            await discord.connect()
        self.assertFalse(discord.connected)

    async def test_state_defaults_and_selection(self) -> None:
        state = AppState(list(self.services.values()))
        state.set_service(self.demo)
        await state.load_options()
        await state.refresh()

        self.assertTrue(state.items)
        self.assertEqual(state.selected, {item.id for item in state.items})
        self.assertIn("servers", state.options)

        first = state.items[0].id
        state.toggle(first, False)
        self.assertNotIn(first, state.selected)

        state.select_all()
        self.assertEqual(len(state.selected), len(state.items))

        state.clear_selection()
        self.assertFalse(state.selected)

    def test_filter_kinds_cover_ui_controls(self) -> None:
        kinds = {field.kind for field in self.demo.filters}
        self.assertIn(FilterKind.TEXT, kinds)
        self.assertIn(FilterKind.BOOL, kinds)
        self.assertIn(FilterKind.DATE_RANGE, kinds)


if __name__ == "__main__":
    unittest.main()
