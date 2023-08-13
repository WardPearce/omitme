class OmitMeError(BaseException):
    pass


class LoginError(OmitMeError):
    def __init__(self) -> None:
        super().__init__("Login error")


class LoginRequiredError(OmitMeError):
    def __init__(self) -> None:
        super().__init__("Login required error")
