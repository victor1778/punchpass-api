from pydantic import BaseModel, Field


class CheckIn(BaseModel):
    id: str = Field(examples=["123e4567-e89b-12d3-a456-426614174000"])
    event_id: int = Field(examples=[12345678])
    user_id: int = Field(examples=[12345678])
    status: str = Field(examples=["confirmed"])
    created: str = Field(examples=["1970-01-01T00:00:00-00:00"])
    updated: str = Field(examples=["1970-01-01T00:00:00-00:00"])
