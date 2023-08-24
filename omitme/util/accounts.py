import json
import platform
from os import getenv, mkdir, path
from urllib.parse import quote_plus, unquote_plus

import aiofiles
import aiofiles.os
import keyring
from cryptography.fernet import Fernet

SYSTEM = platform.system()
if SYSTEM == "Linux":
    PATHWAY = f"{getenv('HOME')}/.config/omitme"
elif SYSTEM == "Windows":
    PATHWAY = f"{getenv('APPDATA')}\\omitme"
elif SYSTEM == "Darwin":
    PATHWAY = f"/Users/{getenv('HOME')}/Library/Application Support/omitme"
else:
    raise Exception("Platform not supported.")


__key_raw = keyring.get_password("omitme", "fernet")
if __key_raw is None:
    RAW_FERNET_KEY = Fernet.generate_key()
    keyring.set_password("omitme", "fernet", RAW_FERNET_KEY.hex())
else:
    RAW_FERNET_KEY = bytes.fromhex(__key_raw)

if not path.exists(PATHWAY):
    mkdir(PATHWAY)


class Accounts:
    def __init__(self, platform: str) -> None:
        self.__platform = platform

    @property
    def __safe_platform(self) -> str:
        return quote_plus(self.__platform)

    def __json_store_path(self, username: str) -> str:
        return path.join(PATHWAY, f"{self.__safe_platform}-{quote_plus(username)}.bin")

    async def remove(self, username: str) -> None:
        await aiofiles.os.remove(self.__json_store_path(username))

    async def add(self, username: str, session: dict) -> None:
        async with aiofiles.open(
            self.__json_store_path(username),
            "wb+",
        ) as f_:
            await f_.write(Fernet(RAW_FERNET_KEY).encrypt(json.dumps(session).encode()))

    async def get(self, username: str) -> dict:
        async with aiofiles.open(self.__json_store_path(username), "rb") as f_:
            return json.loads(Fernet(RAW_FERNET_KEY).decrypt(await f_.read()))

    async def list(self) -> list[str]:
        return [
            unquote_plus(file.removeprefix(f"{self.__platform}-").removesuffix(".bin"))
            for file in await aiofiles.os.listdir(PATHWAY)
            if file.startswith(self.__platform)
        ]
