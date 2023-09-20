from functools import wraps
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Coroutine, List, cast

import httpx
from pydantic import BaseModel
from seleniumwire import webdriver

from omitme.errors import LoginRequiredError

if TYPE_CHECKING:
    from omitme.util.platform import Platform


class SelectionInput(BaseModel):
    parameter: str
    run: Callable[[Any, httpx.AsyncClient], Coroutine[Any, Any, Any]]
    required: bool = False
    format: str
    name: str


class Target(BaseModel):
    description: str | None = None
    action: str
    inputs: List[SelectionInput] | None = None


async def raise_on_4xx_5xx(response: httpx.Response):
    response.raise_for_status()


def login(func: Callable) -> Callable:
    @wraps(func)
    async def _implement(*args, **kwargs) -> Any:
        self_ = cast("Platform", args[0])

        driver = webdriver.Chrome(options=self_.webdriver_options)

        self_._session = cast(
            httpx.AsyncClient,
            await func(self_, driver=driver, accounts=self_._account),
        )
        self_._session.base_url = self_.api_url
        self_._session.event_hooks = {"response": [raise_on_4xx_5xx]}
        self_._session.headers["User-Agent"] = self_.user_agent

        driver.quit()

        return self_._session

    return _implement


def target(
    action: str,
    description: str | None = None,
    inputs: List[SelectionInput] | None = None,
) -> Callable:
    def _func(func: Callable) -> Callable:
        func._target_data = Target(
            description=description, action=action, inputs=inputs
        )

        @wraps(func)
        async def _implement(*args, **kwargs) -> AsyncIterator[Any]:
            self_ = cast("Platform", args[0])

            if not self_._session:
                raise LoginRequiredError()

            async for result in func(self_, session=self_._session, **kwargs):
                yield result

        return _implement

    return _func
