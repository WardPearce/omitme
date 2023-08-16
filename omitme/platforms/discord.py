import base64
import time
from typing import AsyncIterator, Callable

import httpx
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver
from seleniumwire.request import HTTPHeaders

from omitme.errors import LoginError
from omitme.util.events import CheckingEvent, OmittedEvent
from omitme.util.platform import Platform
from omitme.util.targets import login, target
from omitme.util.wait_for import wait_until_or_close


class Discord(Platform):
    api_url = "https://discord.com/api/v9"
    login_url = "https://discord.com/login"
    alias = "discord"
    icon = "discord.png"
    description = "Manage your discord data"

    @login
    async def handle_login(self, driver: webdriver.Chrome) -> httpx.AsyncClient:
        driver.get(self.login_url)

        def get_headers_with_token(current: webdriver.Chrome) -> HTTPHeaders | bool:
            for request in current.requests:
                if "Authorization" in request.headers:
                    return request.headers
            return False

        try:
            headers: dict = dict(wait_until_or_close(driver, get_headers_with_token))
        except TimeoutException:
            raise LoginError()

        headers.pop("content-length")
        headers.pop("content-type")

        return httpx.AsyncClient(headers=headers)

    def _user_id_from_session(self, session: httpx.AsyncClient) -> str:
        urlsafe_base64 = session.headers["Authorization"].split(".")[0]

        return base64.b64decode(
            urlsafe_base64 + "=" * (4 - len(urlsafe_base64) % 4)
        ).decode()

    async def _handle_ratelimit(
        self, request: Callable, *args, **kwargs
    ) -> httpx.Response:
        try:
            resp: httpx.Response = await request(*args, **kwargs)
        except httpx.HTTPStatusError as error:
            if "X-RateLimit-Reset-After" not in error.response.headers:
                time.sleep(1)
                return await self._handle_ratelimit(request, *args, **kwargs)

            time.sleep(int(error.response.headers["X-RateLimit-Reset-After"]))
            return await self._handle_ratelimit(request, *args, **kwargs)

        return resp

    async def _delete_messages(
        self,
        channel: dict,
        user_id: str,
        session: httpx.AsyncClient,
        last_message_id: str | None = None,
    ) -> AsyncIterator[OmittedEvent]:
        params = {"limit": "100"}
        if last_message_id:
            params["before"] = last_message_id

        messages = (
            await self._handle_ratelimit(
                session.get, f"/channels/{channel['id']}/messages", params=params
            )
        ).json()

        for message in messages:
            last_message_id = message["id"]

            if message["author"]["id"] != user_id:
                continue

            await self._handle_ratelimit(
                session.delete,
                f"/channels/{channel['id']}/messages/{message['id']}",
            )

            yield OmittedEvent(
                channel=message["author"]["username"], content=message["content"]
            )

        if len(messages) == 100:
            async for message in self._delete_messages(
                channel, user_id, session, last_message_id
            ):
                yield message

    @target(action="messages delete", description="Delete all given messages")
    async def handle_all_message_delete(
        self, session: httpx.AsyncClient
    ) -> AsyncIterator[OmittedEvent | CheckingEvent]:
        async with session as client:
            channels = (await client.get("/users/@me/channels")).json()

            user_id = self._user_id_from_session(client)

            for channel in channels:
                if channel["type"] != 1:
                    continue

                yield CheckingEvent(channel=channel["recipients"][0]["username"])

                async for message in self._delete_messages(channel, user_id, client):
                    yield message
