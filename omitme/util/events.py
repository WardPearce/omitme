from pydantic import BaseModel


class OmittedEvent(BaseModel):
    content: str
    channel: str | None = None


class CheckingEvent(BaseModel):
    channel: str


class RateLimitEvent(BaseModel):
    content: str


class FailEvent(BaseModel):
    content: str
