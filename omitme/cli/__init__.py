import asyncio
from typing import Optional

import click

from omitme.platforms import PLATFORMS


@click.group()
def main() -> None:
    """Interact with OmitMe from your terminal!"""

    pass


loop = asyncio.get_event_loop()


for platform in PLATFORMS:

    @main.group(platform.alias, help=platform.description)
    def platform_group() -> None:
        pass

    @platform_group.command("login", help="Log into a new account")
    def login(platform=platform) -> None:
        loop.run_until_complete(platform().handle_login())

    @platform_group.command("accounts", help="List accounts already logged in")
    def accounts(platform=platform) -> None:
        accounts = loop.run_until_complete(platform().list_accounts())

        for account in accounts:
            click.echo(f"- {account}")

    @platform_group.group("target", help="Run specific target on the selected platform")
    def target() -> None:
        pass

    for method, meta in platform._target_methods:

        @target.command(meta.action.replace(" ", "-"), help=meta.description)
        @click.option(
            "--account",
            prompt="The account to use with the target",
            help="Provide the account you want to commit a action on",
            required=True,
        )
        @click.option(
            "--echo",
            default=True,
            type=click.BOOL,
            help="Should logs be echo into the terminal in real-time",
        )
        def handle_target(account: str, echo: bool, platform=platform) -> None:
            platform_init = platform()
            loop.run_until_complete(platform_init.load_account(account.strip()))

            async def handle_events() -> None:
                async for event in getattr(platform_init, method.__name__)():
                    if echo:
                        click.echo(event)

            loop.run_until_complete(handle_events())
