from typing import AsyncIterator

import httpx
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver
from seleniumwire.request import HTTPHeaders

from omitme.errors import LoginError
from omitme.util.accounts import Accounts
from omitme.util.events import CheckingEvent, CompletedEvent, FailEvent, OmittedEvent
from omitme.util.platform import Platform
from omitme.util.targets import login, target
from omitme.util.wait_for import wait_until_or_close


class Reddit(Platform):
    login_url = (
        "https://www.reddit.com/login/?dest=https%3A%2F%2Fwww.reddit.com%2Fsettings"
    )
    api_url = "https://oauth.reddit.com"
    alias = "reddit"
    description = "Manage your reddit data"
    icon = "reddit.png"

    @login
    async def handle_login(
        self, driver: webdriver.Chrome, accounts: Accounts
    ) -> httpx.AsyncClient:
        driver.get(self.login_url)

        def get_headers_with_token(current: webdriver.Chrome) -> dict | bool:
            for request in current.requests:
                if "Authorization" in request.headers:
                    headers = {}
                    if request.response:
                        headers |= request.response.headers

                    headers |= request.headers

                    return headers
            return False

        try:
            headers: dict = wait_until_or_close(driver, get_headers_with_token)
        except TimeoutException:
            raise LoginError()

        headers.pop("content-length")
        headers.pop("content-type")

        to_save = {
            "headers": headers,
            "params": {
                "redditWebClient": "desktop2x",
                "app": "desktop2x-client-production",
            },
        }

        session = httpx.AsyncClient(**to_save, base_url=self.api_url)  # type: ignore

        await accounts.add(await self._get_username(session), to_save)

        return session

    async def _delete_post(
        self, session: httpx.AsyncClient, type_id: str, post_id: str
    ) -> None:
        await session.post(
            "/api/del",
            params={"raw_json": "1", "gilding_detail": "1"},
            data={"id": f"{type_id}_{post_id}"},
        )

    async def _get_username(self, session: httpx.AsyncClient) -> str:
        resp = await session.get(
            "https://gateway.reddit.com/desktopapi/v1/prefs",
            params={"include": "identity"},
        )

        return resp.json()["account"]["displayText"]

    @target("posts delete all", description="Delete all reddit posts")
    async def handle_delete_posts(
        self, session: httpx.AsyncClient
    ) -> AsyncIterator[OmittedEvent | CheckingEvent | FailEvent | CompletedEvent]:
        resp = await session.get(
            f"/user/{await self._get_username(session)}/submitted",
            params={"timeframe": "all", "limit": "100"},
        )

        for post in resp.json()["data"]["children"]:
            await self._delete_post(session, post["kind"], post["data"]["id"])

            yield OmittedEvent(
                channel=post["data"]["subreddit"], content=post["data"]["selftext"]
            )

        yield CompletedEvent()
