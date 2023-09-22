"""
Omit your data
"""
import asyncio
from typing import Callable, Type

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from omitme.errors import LoginError
from omitme.platforms import PLATFORMS
from omitme.util.events import CheckingEvent, CompletedEvent, FailEvent, OmittedEvent
from omitme.util.platform import Platform
from omitme.util.targets import SelectionInput, Target


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
                    await self._platform_init.handle_login()  # type: ignore
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

                self._ctx.enable_all_toolbar()

                self._ctx.top_bar_commands[self._platform.alias].enabled = False

                accounts = await self._platform_init.list_accounts()

                account_box = toga.Box(
                    style=Pack(direction=COLUMN),
                    children=[
                        toga.Button("Add new account", on_press=self.add_account),
                        toga.Divider(style=Pack(padding_top=10)),
                    ],
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

                    async def remove_handle(self, _) -> None:
                        await self._ctx._platform_init.remove_account(self._account)

                        for child in account_box.children:
                            if not isinstance(child, toga.Box):
                                continue

                            if child.children[0].text == self._account:
                                account_box.remove(child)
                                break

                for account in accounts:
                    account_box.add(
                        toga.Box(
                            style=Pack(padding_top=10),
                            children=[
                                toga.Button(
                                    account,
                                    on_press=Account(self, account).handle,
                                    style=Pack(width=300),
                                ),
                                toga.Button(
                                    "Remove",
                                    on_press=Account(self, account).remove_handle,
                                    style=Pack(
                                        padding_left=5,
                                        background_color="red",
                                        width=100,
                                    ),
                                ),
                            ],
                        )
                    )

                self._ctx.platform_box.add(account_box)

        self.top_bar_commands: dict[str, toga.Command] = {}

        for platform in PLATFORMS:
            command = toga.Command(
                ShowPlatform(self, platform).handle,
                group=platform_group,
                text=platform.alias.capitalize(),
                tooltip=platform.description,
                icon=f"resources/platforms/{platform.icon}",
            )

            self.top_bar_commands[platform.alias] = command

            self.main_window.toolbar.add(command)

        self.main_window.content = self.platform_box
        self.main_window.show()

    def remove_platform_children(self) -> None:
        for child in self.platform_box.children:
            self.platform_box.remove(child)

    def enable_all_toolbar(self) -> None:
        for command in self.top_bar_commands.values():
            command.enabled = True

    async def show_platform(
        self, platform_type: Type[Platform], init_platform: Platform
    ) -> None:
        self.remove_platform_children()

        class Action:
            def __init__(
                self,
                ctx: "Omitme",
                platform: Platform,
                action: str,
                method: Callable,
                meta: Target,
            ) -> None:
                self._ctx = ctx
                self._platform = platform
                self._action = action
                self._method = method
                self._meta = meta

            async def handle(self, _) -> None:
                self._ctx.platform_box.remove(actions)

                scroll_content = toga.Box(style=Pack(direction=COLUMN))

                scrollable = toga.ScrollContainer(
                    style=Pack(height=800),
                    content=scroll_content,
                    horizontal=False,
                    vertical=True,
                )

                self._ctx.platform_box.add(scrollable)

                # if self._meta.inputs:
                #     for input_ in self._meta.inputs:
                #         if isinstance(input_, SelectionInput):
                #             selections = await input_.run(
                #                 self._platform, self._platform._session
                #             )

                #             for selection in selections:
                #                 display_format = f"{input_.format}".format_map(
                #                     selection
                #                 )

                #                 scroll_content.add(
                #                     toga.Switch(
                #                         display_format,
                #                     )
                #                 )

                #     self._ctx.platform_box.add(toga.Button("Continue"))

                cancel_omit = False
                cancel_button = toga.Button(
                    "Cancel", on_press=lambda _: on_cancel(cancel_omit)
                )

                def on_cancel(cancel_omit: bool) -> None:
                    cancel_omit = True
                    self._ctx.remove_platform_children()
                    self._ctx.platform_box.remove(cancel_button)
                    self._ctx.enable_all_toolbar()

                self._ctx.platform_box.add(cancel_button)

                async for event in getattr(self._platform, self._method.__name__)():
                    event: OmittedEvent | CheckingEvent | FailEvent | CompletedEvent = (
                        event
                    )

                    if isinstance(event, OmittedEvent):
                        label = toga.Label(
                            f'Deleted "{event.content}" from {event.channel}',
                        )
                    elif isinstance(event, FailEvent):
                        continue
                    elif isinstance(event, CompletedEvent):
                        label = toga.Label(
                            "Task completed",
                            style=Pack(font_weight="bold", font_size=13),
                        )
                    else:
                        label = toga.Label(
                            f"Checking {event.channel}",
                            style=Pack(font_weight="bold", font_size=11),
                        )

                    label.style = Pack(padding_top=5)

                    scroll_content.insert(0, label)

                    if cancel_omit:
                        break

        actions = toga.Box(style=Pack(direction=ROW))
        for method, meta in platform_type._target_methods:
            action_pretty = meta.action.capitalize()

            actions.add(
                toga.Button(
                    action_pretty,
                    on_press=Action(
                        self, init_platform, action_pretty, method, meta
                    ).handle,
                    style=Pack(padding_left=10),
                )
            )

        self.platform_box.add(actions)


def main() -> Omitme:
    return Omitme()
