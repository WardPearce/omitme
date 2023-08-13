from abc import abstractmethod

import httpx
from seleniumwire import webdriver

from omitme.util.targets import Target


class Platform:
    api_url: str
    login_url: str
    alias: str

    def __init__(self) -> None:
        option = webdriver.ChromeOptions()
        option.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        self._session: httpx.Client | None = None
        self._targets: dict[str, Target] = {}
        self._driver = webdriver.Chrome(options=option)

    @abstractmethod
    def handle_login(self, driver: webdriver.Chrome) -> httpx.Client:
        pass
