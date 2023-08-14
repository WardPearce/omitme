from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, cast

import httpx
from pydantic import BaseModel
from seleniumwire import webdriver

from omitme.errors import LoginRequiredError

if TYPE_CHECKING:
    from omitme.util.platform import Platform


class Target(BaseModel):
    description: str | None = None
    action: str


def raise_on_4xx_5xx(response: httpx.Response):
    response.raise_for_status()


def login(func: Callable) -> Callable:
    def _implement(*args, **kwargs) -> Any:
        self_ = cast("Platform", args[0])

        driver = webdriver.Chrome(options=self_.webdriver_options)

        self_._session = cast(httpx.Client, func(self_, driver=driver))
        self_._session.base_url = self_.api_url
        self_._session.event_hooks = {"response": [raise_on_4xx_5xx]}
        self_._session.headers["User-Agent"] = self_.user_agent

        driver.quit()

        return self_._session

    return _implement


def target(action: str, description: str | None = None) -> Callable:
    def _func(func: Callable) -> Callable:
        func._target_data = Target(
            description=description,
            action=action,
        )

        @wraps(func)
        def _implement(*args, **kwargs) -> Any:
            self_ = cast("Platform", args[0])

            if not self_._session:
                raise LoginRequiredError()

            return func(self_, session=self_._session)

        return _implement

    return _func
