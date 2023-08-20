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
from omitme.util.events import CheckingEvent, FailEvent, OmittedEvent
from omitme.util.platform import Platform


class Omitme(toga.App):
    def startup(self) -> None:
        self.main_window = toga.MainWindow(title=self.formal_name)

        self.platform_box = toga.Box(style=Pack(direction=COLUMN))

        platform_group = toga.Group("Platforms")

        class ShowPlatform:
            def __init__(self, ctx: "Omitme", platform: type[Platform]) -> None:
                self._ctx = ctx
                self._platform = platform

            async def handle(self, _) -> None:
                await self._ctx.show_platform(self._platform)

        for platform in PLATFORMS:
            command = toga.Command(
                ShowPlatform(self, platform).handle,
                group=platform_group,
                text=platform.alias.capitalize(),
                tooltip=platform.description,
                icon=f"resources/platforms/{platform.icon}",
            )

            self.commands.add(command)
            self.main_window.toolbar.add(command)

        self.main_window.content = self.platform_box
        self.main_window.show()

    async def show_platform(self, platform: Type[Platform]) -> None:
        for child in self.platform_box.children:
            self.platform_box.remove(child)

        init_platform = platform()
        try:
            await init_platform.handle_login()
        except LoginError:
            return

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
                    style=Pack(padding=20, height=600),
                    content=logs_content,
                    horizontal=False,
                    vertical=True,
                )

                self._ctx.platform_box.add(logs)

                async for event in getattr(self._platform, self._method.__name__)():
                    event: OmittedEvent | CheckingEvent | FailEvent = event

                    if isinstance(event, OmittedEvent):
                        label = toga.Label(f"{event.content} from {event.channel}")
                    elif isinstance(event, FailEvent):
                        label = toga.Label(f"Failed to delete {event.content}")
                    else:
                        label = toga.Label(f"Checking {event.channel}")

                    label.style = Pack(padding_top=5)

                    logs_content.add(label)

        actions = toga.Box(style=Pack(padding=20, direction=ROW))
        for method, meta in platform._target_methods:
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
