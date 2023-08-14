"""
Omit your data
"""
from typing import Type

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from omitme.platforms import PLATFORMS
from omitme.platforms.discord import Discord
from omitme.util.platform import Platform


class Omitme(toga.App):
    platform_box: toga.Box

    def startup(self) -> None:
        self.main_window = toga.MainWindow(title=self.formal_name)

        self.platform_box = toga.Box(style=Pack(direction=COLUMN))

        platform_group = toga.Group("Platforms")

        for platform in PLATFORMS:
            command = toga.Command(
                lambda widget: self.show_platform_login(platform, widget),
                group=platform_group,
                text=platform.alias.capitalize(),
                tooltip=platform.description,
                icon=f"resources/platforms/{platform.icon}",
            )

            self.commands.add(command)
            self.main_window.toolbar.add(command)

        self.main_window.content = self.platform_box
        self.main_window.show()

    def show_platform_login(
        self, platform: Type[Platform], widget: toga.Widget
    ) -> None:
        self.platform_box.clear()

        init_platform = platform()
        init_platform.handle_login()

        actions = toga.Box()

        for method, meta in platform._target_methods:
            actions.add(
                toga.Button(
                    meta.action.capitalize(),
                    on_press=getattr(init_platform, method.__name__),
                )
            )

        self.platform_box.add(actions)


def main() -> Omitme:
    return Omitme()
