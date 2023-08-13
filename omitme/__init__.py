from omitme.platforms.discord import Discord


def main() -> None:
    discord = Discord()
    discord.handle_login()
    discord.handle_message_delete()
