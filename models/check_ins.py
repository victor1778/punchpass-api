from pydantic import BaseModel


class CheckIn(BaseModel):
    id: str
    event_id: int
    user_id: int
    status: str
    created_at: str
    updated_at: str
