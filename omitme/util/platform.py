from abc import abstractmethod
from typing import Callable

import httpx
from seleniumwire import webdriver

from omitme.util.targets import Target


class PlatformMeta(type):
    def __init__(cls, name, bases, attrs):
        cls._target_methods: list[tuple[Callable, Target]] = [
            (method, method._target_data)
            for method in attrs.values()
            if hasattr(method, "_target_data")
        ]


class Platform(metaclass=PlatformMeta):
    api_url: str
    login_url: str
    alias: str
    description: str
    icon: str

    def __init__(
        self,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    ) -> None:
        self.user_agent = user_agent
        self.webdriver_options = webdriver.ChromeOptions()
        self.webdriver_options.add_argument(f"user-agent={user_agent}")
        self._session: httpx.AsyncClient | None = None

    @abstractmethod
    async def handle_login(self, driver: webdriver.Chrome) -> httpx.AsyncClient:
        pass
