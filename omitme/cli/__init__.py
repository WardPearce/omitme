import asyncio
from typing import Optional

import click

from omitme.platforms import PLATFORMS
from omitme.util.targets import SelectionInput


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
        loop.run_until_complete(platform().handle_login())  # type: ignore

    @platform_group.command("accounts", help="List accounts already logged in")
    def accounts(platform=platform) -> None:
        accounts = loop.run_until_complete(platform().list_accounts())

        for account in accounts:
            click.echo(f"- {account}")

    @platform_group.command("logout", help="Logout the given account")
    @click.option(
        "--account",
        prompt="The account you wish the remove",
        help="Provide the account ID you want to remove",
        required=True,
    )
    def logout(account: str, platform=platform) -> None:
        loop.run_until_complete(platform().remove_account(account))

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
        def handle_target(
            account: str, echo: bool, platform=platform, meta=meta, method=method
        ) -> None:
            platform_init = platform()
            loop.run_until_complete(platform_init.load_account(account.strip()))

            parameters = {}

            if meta.inputs:
                for input_ in meta.inputs:
                    if isinstance(input_, SelectionInput):
                        selections = loop.run_until_complete(
                            input_.run(platform_init, platform_init._session)
                        )

                        selection_choices = []
                        indexed_selection = {}
                        for selection in selections:
                            display_format = f"{input_.format}".format_map(selection)

                            selection_choices.append(display_format)
                            indexed_selection[display_format] = selection

                        click.echo(", ".join(selection_choices))

                        chosen = click.prompt(
                            f"Select {input_.name} (comma separated)",
                        )

                        parameters[input_.parameter] = []
                        for selected in chosen.split(","):
                            selected = selected.strip()

                            if selected not in indexed_selection:
                                raise Exception(
                                    f"{selected} not found in {input_.name}"
                                )

                            parameters[input_.parameter].append(
                                indexed_selection[selected]
                            )

            async def handle_events(platform_init, method, parameters) -> None:
                async for event in getattr(platform_init, method.__name__)(
                    **parameters
                ):
                    if echo:
                        click.echo(event)

            loop.run_until_complete(handle_events(platform_init, method, parameters))
