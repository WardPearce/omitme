import httpx
from seleniumwire import webdriver

from omitme.util.platform import Platform
from omitme.util.targets import login


class Matrix(Platform):
    api_url = "https://matrix.org"
    login_url = "https://matrix.org"
    alias = "matrix"
    icon = "matrix.png"
    description = "Manage your matrix data, e.g. Element.io"

    @login
    def handle_login(self, driver: webdriver.Chrome) -> httpx.AsyncClient:
        return httpx.AsyncClient()
