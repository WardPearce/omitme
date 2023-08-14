import base64
import time
from typing import Callable, Iterator

import httpx
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
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
    def handle_login(self, driver: webdriver.Chrome) -> httpx.Client:
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

        driver.close()

        headers.pop("content-length")
        headers.pop("content-type")

        return httpx.Client(headers=headers)

    def _user_id_from_session(self, session: httpx.Client) -> str:
        urlsafe_base64 = session.headers["Authorization"].split(".")[0]

        return base64.b64decode(
            urlsafe_base64 + "=" * (4 - len(urlsafe_base64) % 4)
        ).decode()

    def _handle_ratelimit(self, request: Callable, *args, **kwargs) -> httpx.Response:
        try:
            resp: httpx.Response = request(*args, **kwargs)
        except httpx.HTTPStatusError as error:
            if "X-RateLimit-Reset-After" not in error.response.headers:
                time.sleep(1)
                return self._handle_ratelimit(request, *args, **kwargs)

            time.sleep(int(error.response.headers["X-RateLimit-Reset-After"]))
            return self._handle_ratelimit(request, *args, **kwargs)

        return resp

    def _delete_messages(
        self,
        channel: dict,
        user_id: str,
        session: httpx.Client,
        last_message_id: str | None = None,
    ) -> Iterator[OmittedEvent]:
        params = {"limit": "100"}
        if last_message_id:
            params["before"] = last_message_id

        messages = self._handle_ratelimit(
            session.get, f"/channels/{channel['id']}/messages", params=params
        ).json()

        for message in messages:
            last_message_id = message["id"]

            if message["author"]["id"] != user_id:
                continue

            self._handle_ratelimit(
                session.delete,
                f"/channels/{channel['id']}/messages/{message['id']}",
            )

            yield OmittedEvent(
                channel=message["author"]["username"], content=message["content"]
            )

        if len(messages) == 100:
            for message in self._delete_messages(
                channel, user_id, session, last_message_id
            ):
                yield message

    @target(action="delete all messages", description="Delete all given messages")
    def handle_all_message_delete(
        self, session: httpx.Client
    ) -> Iterator[OmittedEvent | CheckingEvent]:
        channels = session.get("/users/@me/channels").json()

        user_id = self._user_id_from_session(session)

        for channel in channels:
            if channel["type"] != 1:
                continue

            yield CheckingEvent(channel=channel["recipients"][0]["username"])

            for message in self._delete_messages(channel, user_id, session):
                yield message

    @target(
        action="delete messages from selected channels",
        description="Deletes messages from a selected channel or channels",
    )
    def handle_selected_message_delete(
        self, session: httpx.Client
    ) -> Iterator[OmittedEvent | CheckingEvent]:
        pass
