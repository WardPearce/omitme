from typing import Any, Callable

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire import webdriver

from omitme.errors import LoginError


def wait_until_or_close(
    driver: webdriver.Chrome,
    condition: Callable,
    timeout: int = 920,
) -> Any:
    def close_condition(driver: webdriver.Chrome) -> bool:
        try:
            driver.title
            return False
        except WebDriverException:
            raise LoginError()

    try:
        return WebDriverWait(driver, timeout).until(
            lambda driver: condition(driver) or close_condition(driver)
        )
    except TimeoutException:
        pass
