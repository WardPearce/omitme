"""
Omit your data
"""
from turtle import width
from typing import Callable, Iterator, Type, cast

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from omitme.errors import LoginError
from omitme.platforms import PLATFORMS
from omitme.util.events import CheckingEvent, OmittedEvent
from omitme.util.platform import Platform


class Omitme(toga.App):
    platform_box: toga.Box

    def startup(self) -> None:
        self.main_window = toga.MainWindow(title=self.formal_name)

        self.platform_box = toga.Box(style=Pack(direction=COLUMN))

        platform_group = toga.Group("Platforms")

        for platform in PLATFORMS:
            command = toga.Command(
                lambda widget, platform=platform: self.show_platform(
                    platform, command, widget
                ),
                group=platform_group,
                text=platform.alias.capitalize(),
                tooltip=platform.description,
                icon=f"resources/platforms/{platform.icon}",
            )

            self.commands.add(command)
            self.main_window.toolbar.add(command)

        self.main_window.content = self.platform_box
        self.main_window.show()

    def show_platform(
        self, platform: Type[Platform], command: toga.Command, widget: toga.Widget
    ) -> None:
        for child in self.platform_box.children:
            self.platform_box.remove(child)

        command.enabled = False

        init_platform = platform()
        try:
            init_platform.handle_login()
        except LoginError:
            return

        def handle_action(action: str, method: Callable) -> None:
            logs = toga.Box(style=Pack(padding=20, direction=COLUMN))
            logs.add(toga.Label(action, style=Pack(font_size=18, padding_bottom=10)))
            logs.add(toga.Button("Kill operation", style=Pack(width=150)))
            logs.add(toga.Divider(style=Pack(padding_bottom=10, padding_top=10)))

            self.platform_box.remove(actions)
            self.platform_box.add(logs)

            for event in cast(
                Iterator[OmittedEvent | CheckingEvent],
                getattr(init_platform, method.__name__)(),
            ):
                if isinstance(event, OmittedEvent):
                    logs.add(toga.Label(f"{event.content} from {event.channel}"))
                else:
                    logs.add(toga.Label(f"Checking {event.channel}"))

        actions = toga.Box(style=Pack(padding=20, direction=ROW))
        for method, meta in platform._target_methods:
            action_pretty = meta.action.capitalize()

            actions.add(
                toga.Button(
                    action_pretty,
                    on_press=lambda _, action_pretty=action_pretty, method=method: handle_action(
                        action_pretty, method
                    ),
                    style=Pack(padding_left=10),
                )
            )

        self.platform_box.add(actions)


def main() -> Omitme:
    return Omitme()
