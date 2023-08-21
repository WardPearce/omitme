import json

import httpx
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver
from seleniumwire.utils import decode

from omitme.errors import LoginError
from omitme.util.accounts import Accounts
from omitme.util.platform import Platform
from omitme.util.targets import login
from omitme.util.wait_for import wait_until_or_close


class Matrix(Platform):
    api_url = "https://matrix-client.matrix.org"
    login_url = ""
    alias = "matrix"
    icon = "matrix.png"
    description = "Handle data across multiple matrix-supported chats."

    @login
    async def handle_login(
        self, driver: webdriver.Chrome, accounts: Accounts
    ) -> httpx.AsyncClient:
        driver.get(self.login_url)

        def get_headers_with_token(current: webdriver.Chrome) -> dict | bool:
            for request in current.requests:
                if (
                    request.method == "POST"
                    and request.url.endswith("client/r0/login")
                    and request.response
                ):
                    return json.loads(
                        decode(
                            request.response.body,
                            request.response.headers.get(
                                "Content-Encoding", "identity"
                            ),
                        )
                    )
            return False

        try:
            content: dict = wait_until_or_close(driver, get_headers_with_token)
        except TimeoutException:
            raise LoginError()

        auth_header = {"Authorization": f"Bearer {content['access_token']}"}

        session = httpx.AsyncClient(headers=auth_header)

        await accounts.add(content["user_id"], session={"headers": auth_header})

        return session
