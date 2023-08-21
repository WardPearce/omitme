import json

import httpx
from pydantic import BaseModel
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver
from seleniumwire.utils import decode
from yarl import URL

from omitme.errors import LoginError
from omitme.util.accounts import Accounts
from omitme.util.platform import Platform
from omitme.util.targets import login
from omitme.util.wait_for import wait_until_or_close


class MatrixLogin(BaseModel):
    access_token: str
    user_id: str
    api_url: str


class Matrix(Platform):
    login_url = "https://app.element.io/#/login"
    api_url = "https://matrix-client.matrix.org"
    alias = "matrix"
    icon = "matrix.png"
    description = "Handle data across multiple matrix-supported chats"

    @login
    async def handle_login(
        self, driver: webdriver.Chrome, accounts: Accounts
    ) -> httpx.AsyncClient:
        driver.get(self.login_url)

        def get_headers_with_token(current: webdriver.Chrome) -> MatrixLogin | bool:
            for request in current.requests:
                if (
                    request.method == "POST"
                    and request.url.endswith("client/r0/login")
                    and request.response
                    and request.response.status_code == 200
                ):
                    raw_json = json.loads(
                        decode(
                            request.response.body,
                            request.response.headers.get(
                                "Content-Encoding", "identity"
                            ),
                        )
                    )

                    url = URL(request.url)
                    return MatrixLogin(**raw_json, api_url=f"{url.scheme}://{url.host}")

            return False

        try:
            content: MatrixLogin = wait_until_or_close(driver, get_headers_with_token)
        except TimeoutException:
            raise LoginError()

        session_kwargs = {
            "headers": {"Authorization": f"Bearer {content.access_token}"},
            "base_url": content.api_url,
        }

        session = httpx.AsyncClient(**session_kwargs)

        await accounts.add(content.user_id, session=session_kwargs)

        return session
