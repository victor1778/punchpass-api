from pydantic import BaseModel, Field


class Event(BaseModel):
    id: int
    status: str
    url: str
    created: str
    updated: str
    title: str
    location: str
    instructor: str
    start: str
    end: str


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
