"""
Omit your data
"""
from re import A
from turtle import width
from typing import Callable, Optional, Type

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from omitme.errors import LoginError
from omitme.platforms import PLATFORMS
from omitme.util.events import CheckingEvent, FailEvent, OmittedEvent
from omitme.util.platform import Platform


class Omitme(toga.App):
    def startup(self) -> None:
        self.main_window = toga.MainWindow(title=self.formal_name)

        self.platform_box = toga.Box(style=Pack(direction=COLUMN, padding=20))

        platform_group = toga.Group("Platforms")

        class ShowPlatform:
            def __init__(self, ctx: "Omitme", platform: type[Platform]) -> None:
                self._ctx = ctx
                self._platform = platform
                self._platform_init = platform()

            async def add_account(self, _) -> None:
                try:
                    await self._platform_init.handle_login()
                except LoginError:
                    self._ctx.remove_platform_children()

                    self._ctx.platform_box.add(
                        toga.Label(
                            "Login failed.",
                            style=Pack(font_size=15),
                        )
                    )
                    return

                await self._ctx.show_platform(self._platform, self._platform_init)

            async def handle(self, _) -> None:
                self._ctx.remove_platform_children()

                accounts = await self._platform_init.list_accounts()

                account_box = toga.Box(style=Pack(direction=COLUMN, width=300))

                account_box.add(
                    toga.Button("Add new account", on_press=self.add_account)
                )

                class Account:
                    def __init__(self, ctx: "ShowPlatform", account: str) -> None:
                        self._account = account
                        self._ctx = ctx

                    async def handle(self, _) -> None:
                        await self._ctx._platform_init.load_account(self._account)
                        await self._ctx._ctx.show_platform(
                            self._ctx._platform, self._ctx._platform_init
                        )

                for account in accounts:
                    account_box.add(
                        toga.Button(
                            account,
                            on_press=Account(self, account).handle,
                            style=Pack(padding_top=10),
                        )
                    )

                self._ctx.platform_box.add(account_box)

        for platform in PLATFORMS:
            command = toga.Command(
                ShowPlatform(self, platform).handle,
                group=platform_group,
                text=platform.alias.capitalize(),
                tooltip=platform.description,
                icon=f"resources/platforms/{platform.icon}",
            )

            self.main_window.toolbar.add(command)

        self.main_window.content = self.platform_box
        self.main_window.show()

    def remove_platform_children(self) -> None:
        for child in self.platform_box.children:
            self.platform_box.remove(child)

    async def show_platform(
        self, platform_type: Type[Platform], init_platform: Platform
    ) -> None:
        self.remove_platform_children()

        class Action:
            def __init__(
                self, ctx: "Omitme", platform: Platform, action: str, method: Callable
            ) -> None:
                self._ctx = ctx
                self._platform = platform
                self._action = action
                self._method = method

            async def handle(self, _) -> None:
                self._ctx.platform_box.remove(actions)

                logs_content = toga.Box(style=Pack(direction=COLUMN))

                logs = toga.ScrollContainer(
                    style=Pack(height=800),
                    content=logs_content,
                    horizontal=False,
                    vertical=True,
                )

                self._ctx.platform_box.add(logs)

                async for event in getattr(self._platform, self._method.__name__)():
                    event: OmittedEvent | CheckingEvent | FailEvent = event

                    if isinstance(event, OmittedEvent):
                        label = toga.Label(
                            f'Deleted "{event.content}"',
                        )
                    elif isinstance(event, FailEvent):
                        continue
                    else:
                        label = toga.Label(
                            f"Checking {event.channel}",
                            style=Pack(font_weight="bold", font_size=13),
                        )

                    label.style = Pack(padding_top=5)

                    logs_content.insert(0, label)

        actions = toga.Box(style=Pack(direction=ROW))
        for method, meta in platform_type._target_methods:
            action_pretty = meta.action.capitalize()

            actions.add(
                toga.Button(
                    action_pretty,
                    on_press=Action(self, init_platform, action_pretty, method).handle,
                    style=Pack(padding_left=10),
                )
            )

        self.platform_box.add(actions)


def main() -> Omitme:
    return Omitme()
