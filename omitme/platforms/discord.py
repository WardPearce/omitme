import httpx
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire import webdriver

from omitme.errors import LoginError
from omitme.util.platform import Platform
from omitme.util.targets import login, target


class Discord(Platform):
    api_url = "https://discord.com/api/v9"
    login_url = "https://discord.com/app"
    alias = "discord"

    @login
    def handle_login(self, driver: webdriver.Chrome) -> httpx.Client:
        driver.get(self.login_url)

        wait = WebDriverWait(driver, timeout=920)

        def get_token(current: webdriver.Chrome) -> str | bool:
            for request in current.requests:
                if (
                    request.url
                    == "https://discord.com/api/v9/users/@me/affinities/guilds"
                ):
                    return request.headers["Authorization"]
            return False

        try:
            token: str = wait.until(get_token)
        except TimeoutException:
            raise LoginError()

        return httpx.Client(headers={"Authorization": token})

    @target(action="message delete", description="Delete all given messages")
    def handle_message_delete(self, session: httpx.Client) -> str:
        relationships = session.get("/users/@me/relationships")

        print(relationships.read())

        return "Some status update"
