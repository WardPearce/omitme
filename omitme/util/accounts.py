import json
import platform
from os import getenv, mkdir, path
from urllib.parse import quote_plus

import aiofiles
import aiofiles.os

SYSTEM = platform.system()
if SYSTEM == "Linux":
    PATHWAY = f"{getenv('HOME')}/.config/omitme"
elif SYSTEM == "Windows":
    PATHWAY = f"{getenv('APPDATA')}\\omitme"
elif SYSTEM == "Darwin":
    PATHWAY = f"/Users/{getenv('HOME')}/Library/Application Support/omitme"
else:
    raise Exception("Platform not supported.")


if not path.exists(PATHWAY):
    mkdir(PATHWAY)


class Accounts:
    def __init__(self, platform: str) -> None:
        self.__platform = platform

    @property
    def __safe_platform(self) -> str:
        return quote_plus(self.__platform)

    def __json_store_path(self, username: str) -> str:
        return path.join(PATHWAY, f"{self.__safe_platform}-{quote_plus(username)}.json")

    async def remove(self, username: str) -> None:
        await aiofiles.os.remove(self.__json_store_path(username))

    async def add(self, username: str, session: dict) -> None:
        async with aiofiles.open(
            self.__json_store_path(username),
            "w+",
        ) as f_:
            await f_.write(json.dumps(session))

    async def get(self, username: str) -> dict:
        async with aiofiles.open(self.__json_store_path(username), "r") as f_:
            return json.loads(await f_.read())

    async def list(self) -> list[str]:
        return [
            file.replace(self.__platform, "").replace(".json", "").removeprefix("-")
            for file in await aiofiles.os.listdir(PATHWAY)
            if file.startswith(self.__platform)
        ]
