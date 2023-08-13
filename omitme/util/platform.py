from abc import abstractmethod

import httpx
from seleniumwire import webdriver

from omitme.util.targets import Target


class Platform:
    api_url: str
    login_url: str
    alias: str

    def __init__(
        self,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    ) -> None:
        self.user_agent = user_agent
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={user_agent}")
        self._session: httpx.Client | None = None
        self._targets: dict[str, Target] = {}
        self._driver = webdriver.Chrome(options=options)

    @abstractmethod
    def handle_login(self, driver: webdriver.Chrome) -> httpx.Client:
        pass
