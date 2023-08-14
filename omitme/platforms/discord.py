import base64
import time

import httpx
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire import webdriver
from seleniumwire.request import HTTPHeaders

from omitme.errors import LoginError
from omitme.util.platform import Platform
from omitme.util.targets import login, target


class Discord(Platform):
    api_url = "https://discord.com/api/v9"
    login_url = "https://discord.com/login"
    alias = "discord"
    icon = "discord.png"
    description = "Manage your discord data"

    @login
    def handle_login(self, driver: webdriver.Chrome) -> httpx.Client:
        driver.get(self.login_url)

        wait = WebDriverWait(driver, timeout=920)

        def get_headers_with_token(current: webdriver.Chrome) -> HTTPHeaders | bool:
            for request in current.requests:
                if "Authorization" in request.headers:
                    return request.headers
            return False

        try:
            headers: dict = dict(wait.until(get_headers_with_token))
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

    def _delete_messages(
        self,
        channel: dict,
        user_id: str,
        session: httpx.Client,
        last_message_id: str | None = None,
    ) -> None:
        print(f"Checking {channel['id']} for {channel['recipients'][0]['global_name']}")

        params = {"limit": "100"}
        if last_message_id:
            params["after"] = last_message_id

        try:
            messages = session.get(
                f"/channels/{channel['id']}/messages",
                params=params,
            ).json()
        except httpx.HTTPStatusError:
            return

        for message in messages:
            if message["author"]["id"] != user_id:
                continue

            try:
                session.delete(f"/channels/{channel['id']}/messages/{message['id']}")
            except httpx.HTTPStatusError:
                pass

            last_message_id = message["id"]

        if len(messages) == 100:
            self._delete_messages(channel, user_id, session, last_message_id)

    @target(action="message delete", description="Delete all given messages")
    def handle_message_delete(self, session: httpx.Client) -> str:
        channels = session.get("/users/@me/channels").json()

        user_id = self._user_id_from_session(session)

        for channel in channels:
            if channel["type"] != 1:
                continue

            self._delete_messages(channel, user_id, session)

        return "Some status update"
