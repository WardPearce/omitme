import asyncio

import click

from omitme.platforms import PLATFORMS


@click.group()
def main() -> None:
    """Interact with OmitMe from your terminal!"""

    pass


for platform in PLATFORMS:

    @main.group(platform.alias, help=platform.description)
    def platform_group() -> None:
        pass

    @platform_group.command("login")
    def login(platform=platform) -> None:
        asyncio.run(platform().handle_login())
