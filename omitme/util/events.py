from pydantic import BaseModel


class OmittedEvent(BaseModel):
    content: str
    channel: str | None = None


class CheckingEvent(BaseModel):
    channel: str
