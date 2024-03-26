from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from pydantic import BaseModel, Field


@dataclass
class Event:
    id: int = None
    status: str = None
    url: str = None
    title: str = None
    location: str = None
    instructor: str = None
    start: dict[str, str] = None
    end: dict[str, str] = None
    timestamp: str = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


class WriteUserToEvent(BaseModel):
    first_name: str = Field(examples=["John"])
    last_name: str = Field(examples=["Doe"])


class WriteUserToManyEvents(BaseModel):
    event_ids: list[int] = Field(
        description="A list of event IDs, each an integer.",
        examples=[
            [
                12345678,
                87654321,
            ]
        ],
    )
    first_name: str = Field(examples=["John"])
    last_name: str = Field(examples=["Doe"])
