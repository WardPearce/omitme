import asyncio
import base64
from typing import AsyncIterator, Callable, List

import httpx
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver
from seleniumwire.request import HTTPHeaders

from omitme.errors import LoginError
from omitme.util.accounts import Accounts
from omitme.util.events import CheckingEvent, CompletedEvent, FailEvent, OmittedEvent
from omitme.util.platform import Platform
from omitme.util.targets import SelectionInput, login, target
from omitme.util.wait_for import wait_until_or_close


class Discord(Platform):
    api_url = "https://discord.com/api/v9"
    login_url = "https://discord.com/login"
    alias = "discord"
    icon = "discord.png"
    description = "Manage your discord data"

    @login
    async def handle_login(
        self, driver: webdriver.Chrome, accounts: Accounts
    ) -> httpx.AsyncClient:
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

        session = httpx.AsyncClient(headers=headers)

        # Need to include the API url, because hasn't been injected yet.
        resp = await session.get(f"{self.api_url}/users/@me")

        await accounts.add(resp.json()["username"], session={"headers": headers})

        return session

    def _user_id_from_session(self, session: httpx.AsyncClient) -> str:
        urlsafe_base64 = session.headers["Authorization"].split(".")[0]

        return base64.b64decode(
            urlsafe_base64 + "=" * (4 - len(urlsafe_base64) % 4)
        ).decode()

    async def _handle_ratelimit(
        self,
        request: Callable,
        depth: int,
        *args,
        **kwargs,
    ) -> httpx.Response:
        depth += 1

        try:
            resp: httpx.Response = await request(*args, **kwargs)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 429:
                try:
                    message = error.response.json()
                    await asyncio.sleep(message["retry_after"])
                except httpx.ResponseNotRead:
                    await asyncio.sleep(3 * depth)

                return await self._handle_ratelimit(request, depth, *args, **kwargs)

            raise error

        return resp

    async def _delete_messages(
        self,
        channel: dict,
        user_id: str,
        session: httpx.AsyncClient,
        last_message_id: str | None = None,
    ) -> AsyncIterator[OmittedEvent | FailEvent]:
        params = {"limit": "100"}
        if last_message_id:
            params["before"] = last_message_id

        messages = (
            await self._handle_ratelimit(
                session.get,
                0,
                f"/channels/{channel['id']}/messages",
                params=params,
            )
        ).json()

        for message in messages:
            last_message_id = message["id"]

            if message["author"]["id"] != user_id:
                continue

            if message["type"] != 0:
                continue

            try:
                await self._handle_ratelimit(
                    session.delete,
                    0,
                    f"/channels/{channel['id']}/messages/{message['id']}",
                )
            except httpx.HTTPStatusError:
                yield FailEvent(content=message["content"])
                continue

            yield OmittedEvent(
                channel=channel["recipients"][0]["global_name"],
                content=message["content"],
            )

        if len(messages) == 100:
            async for message in self._delete_messages(
                channel, user_id, session, last_message_id
            ):
                yield message

    async def _get_channels(self, session: httpx.AsyncClient) -> List[dict]:
        return (await session.get("/users/@me/channels")).json()

    @target(
        action="messages delete selected",
        description="Delete selected messages",
        inputs=[
            SelectionInput(
                name="channels",
                parameter="channels",
                required=True,
                run=_get_channels,
                format="{recipients[0][global_name]}",
            )
        ],
    )
    async def handle_delete_selected_messages(
        self, session: httpx.AsyncClient, channels: List[dict]
    ) -> AsyncIterator[OmittedEvent | CheckingEvent | FailEvent | CompletedEvent]:
        async for event in self.handle_all_message_delete(session, channels=channels):
            yield event

    @target(action="messages delete all", description="Delete all messages")
    async def handle_all_message_delete(
        self, session: httpx.AsyncClient, channels: List[dict] | None = None
    ) -> AsyncIterator[OmittedEvent | CheckingEvent | FailEvent | CompletedEvent]:
        if not channels:
            channels = await self._get_channels(session)

        user_id = self._user_id_from_session(session)

        for channel in channels:
            if channel["type"] != 1:
                continue

            yield CheckingEvent(channel=channel["recipients"][0]["username"])

            async for message in self._delete_messages(channel, user_id, session):
                yield message

        yield CompletedEvent()
