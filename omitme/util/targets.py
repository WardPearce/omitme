from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, cast

import httpx
from pydantic import BaseModel

if TYPE_CHECKING:
    from omitme.util.platform import Platform


class Target(BaseModel):
    description: str | None = None
    callable_: Callable


def raise_on_4xx_5xx(response: httpx.Response):
    response.raise_for_status()


def login(func: Callable) -> Callable:
    def _implement(*args, **kwargs) -> Any:
        self_ = cast("Platform", args[0])

        http_session = cast(httpx.Client, func(self_, driver=self_._driver))
        http_session.base_url = self_.api_url
        http_session.event_hooks = {"response": [raise_on_4xx_5xx]}

        self_._session = http_session

        return http_session

    return _implement


def target(action: str, description: str | None = None) -> Callable:
    def _func(func: Callable) -> Callable:
        def _implement(*args, **kwargs) -> Any:
            self_ = cast("Platform", args[0])

            self_._targets[action] = Target(description=description, callable_=func)

            return func(self_, session=self_._session)

        return _implement

    return _func
