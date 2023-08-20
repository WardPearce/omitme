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

    @platform_group.command("login", help="Log into a new account")
    @click.option(
        "--nosave",
        default=False,
        type=click.BOOL,
        help=f"Saves session details for {platform.alias} in a temp file",
    )
    def login(nosave: bool, platform=platform) -> None:
        asyncio.run(platform().handle_login())

    @platform_group.command("accounts", help="List accounts already logged in")
    def accounts() -> None:
        pass

    @platform_group.group(
        "targets", help="Run specific targets on the selected platform"
    )
    @click.option(
        "--account",
        prompt="Your account name",
        help="Provide the name of the account you want to commit a action on",
        required=True,
    )
    @click.pass_context
    def targets(ctx, account: str) -> None:
        ctx.obj = {}
        ctx.obj["account"] = account

    for method, meta in platform._target_methods:

        @targets.command(meta.action.replace(" ", "-"), help=meta.description)
        @click.pass_context
        def handle_target(ctx) -> None:
            pass
