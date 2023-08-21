import httpx
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver
from seleniumwire.request import HTTPHeaders

from omitme.errors import LoginError
from omitme.util.accounts import Accounts
from omitme.util.platform import Platform
from omitme.util.targets import login
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

        resp = await session.get(
            "https://gateway.reddit.com/desktopapi/v1/prefs?redditWebClient=web2x&app=web2x-client-production&include=identity"
        )

        await accounts.add(resp.json()["account"]["email"], {"headers": headers})

        return session
